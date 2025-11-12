"""Main Streamlit application for Pronunciation & Prosody Evaluator."""

import streamlit as st
import logging
from typing import Optional
import time

from config.constants import APP_TITLE, APP_DESCRIPTION, DEFAULT_SCRIPTS
from config.settings import settings
from src.api_client import PronunciationAPI, PronunciationAPIError
from src.audio_handler import SimpleAudioRecorder, play_audio
from src.results_processor import ResultsProcessor
from src.ui_components import (
    render_settings_panel,
    render_practice_script_display,
    render_file_upload_section,
    render_analyze_button,
    render_proficiency_scores,
    render_prosody_analysis,
    render_word_analysis,
    render_overall_results,
    render_phoneme_errors,
    render_loading_spinner,
    render_error_message,
    render_success_message,
    render_audio_player
)
# Đã xoá import ui_epitran

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "reference_text" not in st.session_state:
    st.session_state.reference_text = ""

def main():
    """Main application logic."""
    
    # Header - compact
    st.title(APP_TITLE)
    
    # Main layout - 2 columns (30/70)
    col_input, col_result = st.columns([3, 7])
    
    with col_input:
        st.markdown("### Chọn Văn Bản & Thu Âm")
        
        # Practice script selection - compact
        script_options = ["Tùy Chỉnh"] + DEFAULT_SCRIPTS
        selected_script = st.selectbox(
            "Đoạn Văn Luyện Tập",
            options=script_options,
            index=1,
            label_visibility="collapsed"
        )
        
        if selected_script == "Tùy Chỉnh":
            reference_text = st.text_area(
                "Văn Bản",
                value="Enter your custom text here...",
                height=80,
                label_visibility="collapsed"
            )
        else:
            reference_text = selected_script
            st.text_area(
                "Văn Bản",
                value=reference_text,
                height=80,
                disabled=True,
                label_visibility="collapsed"
            )
        
        st.session_state.reference_text = reference_text
        
        # Recording section - compact
        st.markdown("**Thu Âm**")
        audio_file = st.audio_input("Nhấn để ghi âm", key="audio_recorder", label_visibility="collapsed")
        
        if audio_file:
            # Process the audio to ensure correct format
            try:
                audio_file.seek(0)
                raw_audio = audio_file.read()
                
                from src.audio_handler import convert_audio_to_wav
                audio_data = convert_audio_to_wav(raw_audio)
                
                if audio_data:
                    st.session_state.audio_data = audio_data
                    st.session_state.audio_source = "recording"
                    st.success("✅ Đã ghi âm xong")
                else:
                    st.error("Không thể xử lý âm thanh")
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
                logger.error(f"Audio processing error: {e}")
        
        # Analyze button - only show if audio is recorded
        if st.session_state.audio_data:
            analyze_button = st.button("🎯 Phân Tích", type="primary", use_container_width=True)
        else:
            analyze_button = False
            st.info("👆 Vui lòng ghi âm trước khi phân tích")
    
    with col_result:
        st.markdown("### Kết Quả")
        
        # Analysis logic
        if analyze_button and st.session_state.audio_data:
            with st.spinner("Đang phân tích..."):
                try:
                    # Create API client
                    api_client = PronunciationAPI(
                        api_url=settings.api_url,
                        api_key=settings.api_key
                    )
                    
                    # Analyze pronunciation
                    response = api_client.analyze_pronunciation(
                        audio_data=st.session_state.audio_data,
                        reference_text=st.session_state.reference_text
                    )
                    
                    # Process results
                    processor = ResultsProcessor()
                    results = processor.process_api_response(response)
                    st.session_state.analysis_results = results
                    
                    render_success_message("Phân tích hoàn tất!")
                    
                except PronunciationAPIError as e:
                    render_error_message(f"Lỗi API: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    render_error_message(f"Lỗi: {str(e)}")
        
        # Display results
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results
            
            # Create 2 tabs
            tab1, tab2 = st.tabs(["📊 Tổng Quan", "🔍 Chi Tiết"])
            
            with tab1:
                # Overall results first
                render_overall_results(results)
                
                # Colored word display - hiển thị từng từ với màu sắc
                st.subheader("Phân Tích Từng Từ")
                if results.word_analyses:
                    import html
                    
                    # Create a mapping of word errors for quick lookup
                    word_errors_map = {}
                    if results.phoneme_errors:
                        for error in results.phoneme_errors:
                            word_key = f"{error.word}_{error.word_idx}"
                            if word_key not in word_errors_map:
                                word_errors_map[word_key] = []
                            word_errors_map[word_key].append(error)
                    
                    # Custom CSS for beautiful tooltips
                    tooltip_css = """
                    <style>
                    .word-tooltip {
                        position: relative;
                        display: inline-block;
                        cursor: help;
                        font-weight: 600;
                        margin: 0 4px;
                        border-bottom: 2px dotted;
                        transition: all 0.2s;
                    }
                    .word-tooltip:hover {
                        transform: translateY(-2px);
                    }
                    .word-tooltip .tooltiptext {
                        visibility: hidden;
                        width: 320px;
                        background-color: #2c3e50;
                        color: #fff;
                        text-align: left;
                        border-radius: 8px;
                        padding: 12px 16px;
                        position: absolute;
                        z-index: 1000;
                        bottom: 125%;
                        left: 50%;
                        margin-left: -160px;
                        opacity: 0;
                        transition: opacity 0.3s, visibility 0.3s;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        font-size: 14px;
                        line-height: 1.6;
                        font-weight: normal;
                        white-space: normal;
                    }
                    .word-tooltip .tooltiptext::after {
                        content: "";
                        position: absolute;
                        top: 100%;
                        left: 50%;
                        margin-left: -8px;
                        border-width: 8px;
                        border-style: solid;
                        border-color: #2c3e50 transparent transparent transparent;
                    }
                    .word-tooltip:hover .tooltiptext {
                        visibility: visible;
                        opacity: 1;
                    }
                    .tooltip-score {
                        font-size: 16px;
                        font-weight: 600;
                        color: #3498db;
                        margin-bottom: 8px;
                        padding-bottom: 8px;
                        border-bottom: 1px solid rgba(255,255,255,0.2);
                    }
                    .tooltip-error-title {
                        font-weight: 600;
                        color: #e74c3c;
                        margin-top: 8px;
                        margin-bottom: 4px;
                    }
                    .tooltip-error-item {
                        margin: 6px 0;
                        padding-left: 12px;
                        border-left: 3px solid #e74c3c;
                    }
                    .tooltip-error-type {
                        color: #f39c12;
                        font-weight: 600;
                    }
                    .tooltip-error-detail {
                        color: #ecf0f1;
                        font-size: 13px;
                        margin-top: 2px;
                    }
                    .tooltip-no-error {
                        color: #2ecc71;
                        font-weight: 600;
                    }
                    </style>
                    """
                    
                    # Create HTML with colored words and beautiful tooltips
                    words_html = []
                    
                    for word_analysis in results.word_analyses:
                        word = word_analysis.word
                        score = word_analysis.score
                        word_idx = word_analysis.word_idx
                        phoneme_details = word_analysis.phoneme_details
                        
                        # Build tooltip content with detailed error info
                        word_key = f"{word_analysis.word}_{word_idx}"
                        tooltip_parts = [f'<div class="tooltip-score">📊 Điểm: {score:.0f}/100</div>']
                        
                        # Add phoneme-level details if available (only show errors)
                        if phoneme_details and len(phoneme_details) > 0:
                            # Only show phonemes with errors (score < 70)
                            error_phonemes = [p for p in phoneme_details if p.score < 70]
                            if error_phonemes:
                                tooltip_parts.append(f'<div class="tooltip-error-title" style="margin-top: 10px;">Âm cần cải thiện:</div>')
                                # Show max 3 worst phonemes
                                for phoneme in sorted(error_phonemes, key=lambda p: p.score)[:3]:
                                    if phoneme.score >= 40:
                                        status_icon = "⚠️"
                                        status_color = "#ffc107"
                                    else:
                                        status_icon = "❌"
                                        status_color = "#dc3545"
                                    
                                    tooltip_parts.append(f'<div style="color: {status_color}; margin: 4px 0;">{status_icon} /{phoneme.ipa}/ - {phoneme.score:.0f}</div>')
                        
                        # Add word-level errors if available (only most important one)
                        if word_key in word_errors_map:
                            errors = word_errors_map[word_key]
                            # Only show first most important error
                            important_errors = [e for e in errors if e.error_type not in ['correction']][:1]
                            if important_errors:
                                error = important_errors[0]
                                error_tag = html.escape(error.error_tag)
                                # Translate error type to Vietnamese
                                error_type_vn = {
                                    'substitution': 'Thay thế',
                                    'deletion': 'Thiếu âm',
                                    'insertion': 'Thêm âm',
                                    'correction': 'Chính xác'
                                }.get(error.error_type, error.error_type)
                                
                                tooltip_parts.append(f'<div class="tooltip-error-title" style="margin-top: 10px;">Lỗi chính:</div>')
                                tooltip_parts.append(f'<div style="color: #f39c12; margin: 4px 0;">{error_tag}</div>')
                                tooltip_parts.append(f'<div style="color: #bbb; font-size: 11px;">({error_type_vn})</div>')
                        
                        tooltip_content = ''.join(tooltip_parts)
                        
                        # Build word display with letter-level coloring based on phonemes
                        word_html_parts = []
                        ipa_html_parts = []
                        ipa_text = word_analysis.ipa if word_analysis.ipa else ""
                        
                        # Color each letter based on corresponding phoneme score
                        if phoneme_details and len(phoneme_details) > 0:
                            # Simple heuristic: distribute letters across phonemes
                            letters = list(word)
                            num_letters = len(letters)
                            num_phonemes = len(phoneme_details)
                            
                            # Calculate which letters correspond to which phonemes
                            letters_per_phoneme = num_letters / num_phonemes
                            
                            for i, letter in enumerate(letters):
                                # Determine which phoneme this letter belongs to
                                phoneme_idx = min(int(i / letters_per_phoneme), num_phonemes - 1)
                                phoneme = phoneme_details[phoneme_idx]
                                
                                # Determine color based on phoneme score
                                if phoneme.score >= 70:
                                    letter_color = "#28a745"  # Green
                                elif phoneme.score >= 40:
                                    letter_color = "#ffc107"  # Yellow
                                else:
                                    letter_color = "#dc3545"  # Red
                                
                                word_html_parts.append(f'<span style="color: {letter_color};">{html.escape(letter)}</span>')
                            
                            # Color each IPA phoneme based on its score
                            for phoneme in phoneme_details:
                                if phoneme.score >= 70:
                                    phoneme_color = "#28a745"  # Green
                                elif phoneme.score >= 40:
                                    phoneme_color = "#ffc107"  # Yellow
                                else:
                                    phoneme_color = "#dc3545"  # Red
                                
                                ipa_html_parts.append(f'<span style="color: {phoneme_color};">{html.escape(phoneme.ipa)}</span>')
                            
                            colored_word = ''.join(word_html_parts)
                            colored_ipa = ' '.join(ipa_html_parts)
                        else:
                            # Fallback: color entire word based on overall score
                            if score >= 70:
                                color = "#28a745"
                            elif score >= 40:
                                color = "#ffc107"
                            else:
                                color = "#dc3545"
                            colored_word = f'<span style="color: {color};">{html.escape(word)}</span>'
                            colored_ipa = f'<span style="color: {color};">{html.escape(ipa_text)}</span>'
                        
                        # Add word with colored letters, colored IPA, and tooltip
                        word_html = f'''<span class="word-tooltip" style="display: inline-block; text-align: center; margin: 0 8px;">
                            <div style="font-weight: 500; border-bottom: 2px solid #dee2e6;">{colored_word}</div>
                            <div style="font-size: 12px; margin-top: 2px; font-style: italic;">/{colored_ipa}/</div>
                            <span class="tooltiptext">{tooltip_content}</span>
                        </span>'''
                        words_html.append(word_html)
                    
                    colored_html = tooltip_css
                    colored_html += '<div style="font-size: 18px; line-height: 3; padding: 15px; background-color: #f8f9fa; border-radius: 8px;">'
                    colored_html += ''.join(words_html)
                    colored_html += '</div>'
                    
                    # Hint text
                    colored_html += '''
                    <div style="margin-top: 10px; font-size: 14px; color: #6c757d; text-align: center;">
                        💡 Di chuột lên từ để xem chi tiết lỗi
                    </div>
                    '''
                    
                    st.markdown(colored_html, unsafe_allow_html=True)
                    # Create a mapping of word errors for quick lookup
                    word_errors_map = {}
                    if results.phoneme_errors:
                        for error in results.phoneme_errors:
                            word_key = f"{error.word}_{error.word_idx}"
                            if word_key not in word_errors_map:
                                word_errors_map[word_key] = []
                            word_errors_map[word_key].append(error)
                    
                    # Custom CSS for beautiful tooltips
                    tooltip_css = """
                    <style>
                    .word-tooltip {
                        position: relative;
                        display: inline-block;
                        cursor: help;
                        font-weight: 600;
                        margin: 0 4px;
                        border-bottom: 2px dotted;
                        transition: all 0.2s;
                    }
                    .word-tooltip:hover {
                        transform: translateY(-2px);
                    }
                    .word-tooltip .tooltiptext {
                        visibility: hidden;
                        width: 320px;
                        background-color: #2c3e50;
                        color: #fff;
                        text-align: left;
                        border-radius: 8px;
                        padding: 12px 16px;
                        position: absolute;
                        z-index: 1000;
                        bottom: 125%;
                        left: 50%;
                        margin-left: -160px;
                        opacity: 0;
                        transition: opacity 0.3s, visibility 0.3s;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        font-size: 14px;
                        line-height: 1.6;
                        font-weight: normal;
                    }
                    .word-tooltip .tooltiptext::after {
                        content: "";
                        position: absolute;
                        top: 100%;
                        left: 50%;
                        margin-left: -8px;
                        border-width: 8px;
                        border-style: solid;
                        border-color: #2c3e50 transparent transparent transparent;
                    }
                    .word-tooltip:hover .tooltiptext {
                        visibility: visible;
                        opacity: 1;
                    }
                    .tooltip-score {
                        font-size: 16px;
                        font-weight: 600;
                        color: #3498db;
                        margin-bottom: 8px;
                        padding-bottom: 8px;
                        border-bottom: 1px solid rgba(255,255,255,0.2);
                    }
                    .tooltip-error-title {
                        font-weight: 600;
                        color: #e74c3c;
                        margin-top: 8px;
                        margin-bottom: 4px;
                    }
                    .tooltip-error-item {
                        margin: 6px 0;
                        padding-left: 12px;
                        border-left: 3px solid #e74c3c;
                    }
                    .tooltip-error-type {
                        color: #f39c12;
                        font-weight: 600;
                    }
                    .tooltip-error-detail {
                        color: #ecf0f1;
                        font-size: 13px;
                        margin-top: 2px;
                    }
                    .tooltip-no-error {
                        color: #2ecc71;
                        font-weight: 600;
                    }
                    </style>
                    """
                    
                    # Build HTML - phần này đã được xử lý ở trên với html.escape
                    # Không cần code duplicate này nữa
                    
                else:
                    st.info("Không có dữ liệu phân tích")
            
            with tab2:
                # All detailed metrics with beautiful design
                
                # Pronunciation scores section with colored cards
                st.markdown("### 🎯 Điểm Phát Âm")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score = results.proficiency_scores.acoustic_score/10
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 20px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">Âm học</div>
                            <div style="color: {color}; font-size: 32px; font-weight: 700;">{score:.1f}<span style="font-size: 18px;">/10</span></div>
                            <div style="color: #6c757d; font-size: 12px; margin-top: 5px;">Chất lượng âm thanh</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    score = results.proficiency_scores.holistic_score*2
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 20px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">Tổng quát</div>
                            <div style="color: {color}; font-size: 32px; font-weight: 700;">{score:.1f}<span style="font-size: 18px;">/10</span></div>
                            <div style="color: #6c757d; font-size: 12px; margin-top: 5px;">Đánh giá tổng thể</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col3:
                    score = results.proficiency_scores.segmental_accuracy*2
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 20px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">Độ chính xác</div>
                            <div style="color: {color}; font-size: 32px; font-weight: 700;">{score:.1f}<span style="font-size: 18px;">/10</span></div>
                            <div style="color: #6c757d; font-size: 12px; margin-top: 5px;">Chính xác âm vị</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Prosody & Fluency scores section with colored cards
                st.markdown("### 🎵 Điểm Ngữ Điệu & Lưu Loát")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    score = results.proficiency_scores.stress_and_rhythm*2
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 15px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 5px;">Nhấn & Nhịp</div>
                            <div style="color: {color}; font-size: 28px; font-weight: 700;">{score:.1f}<span style="font-size: 16px;">/10</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    score = results.proficiency_scores.intonation*2
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 15px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 5px;">Ngữ Điệu</div>
                            <div style="color: {color}; font-size: 28px; font-weight: 700;">{score:.1f}<span style="font-size: 16px;">/10</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col3:
                    score = results.proficiency_scores.chunking*2
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 15px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 5px;">Phân Đoạn</div>
                            <div style="color: {color}; font-size: 28px; font-weight: 700;">{score:.1f}<span style="font-size: 16px;">/10</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col4:
                    score = results.proficiency_scores.speed_and_pause*2
                    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; 
                                    padding: 15px; 
                                    border-radius: 10px; 
                                    margin-bottom: 10px;">
                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 5px;">Tốc Độ & Dừng</div>
                            <div style="color: {color}; font-size: 28px; font-weight: 700;">{score:.1f}<span style="font-size: 16px;">/10</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Prosody analysis detail with icons and colored boxes
                st.markdown("### 🎙️ Đánh Giá Chi Tiết")
                prosody = results.prosody_analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    status_color = "#28a745" if prosody.sentence_ending == "Normal" else "#ffc107"
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; 
                                    padding: 20px; 
                                    border-radius: 10px; 
                                    border-top: 3px solid {status_color};
                                    text-align: center;">
                            <div style="font-size: 24px; margin-bottom: 10px;">🎬</div>
                            <div style="color: #495057; font-weight: 600; margin-bottom: 5px;">Kết thúc câu</div>
                            <div style="color: {status_color}; font-size: 18px; font-weight: 600;">{prosody.sentence_ending}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    status_color = "#28a745" if prosody.pauses == "Natural" else "#dc3545"
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; 
                                    padding: 20px; 
                                    border-radius: 10px; 
                                    border-top: 3px solid {status_color};
                                    text-align: center;">
                            <div style="font-size: 24px; margin-bottom: 10px;">⏸️</div>
                            <div style="color: #495057; font-weight: 600; margin-bottom: 5px;">Khoảng dừng</div>
                            <div style="color: {status_color}; font-size: 18px; font-weight: 600;">{prosody.pauses}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
    # Footer - compact at bottom
    st.caption("Được xây dựng với Streamlit")

if __name__ == "__main__":
    main()