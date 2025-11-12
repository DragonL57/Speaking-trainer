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
    
    # Main layout - 2 columns
    col_input, col_result = st.columns([1, 1])
    
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
                    st.success("Đã ghi âm")
                else:
                    st.error("Không thể xử lý âm thanh")
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
                logger.error(f"Audio processing error: {e}")
        
        # Analyze button
        analyze_button = st.button("Phân Tích", type="primary", use_container_width=True)
    
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
            
            # Create tabs for results
            tab1, tab2, tab3 = st.tabs([
                "Phát Âm", 
                "Ngữ Điệu",
                "Lưu Loát"
            ])
            
            with tab1:
                # Overall pronunciation scores
                st.subheader("Điểm Tổng Quát")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Âm học", f"{results.proficiency_scores.acoustic_score/10:.1f}/10")
                with col2:
                    st.metric("Tổng quát", f"{results.proficiency_scores.holistic_score*2:.1f}/10")
                with col3:
                    st.metric("Độ chính xác", f"{results.proficiency_scores.segmental_accuracy*2:.1f}/10")
                
                # Colored word display - hiển thị từng từ với màu sắc
                st.subheader("Phân Tích Chi Tiết")
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
                        word = html.escape(word_analysis.word)
                        score = word_analysis.score
                        word_idx = word_analysis.word_idx
                        
                        # Determine color based on score
                        if score >= 70:
                            color = "#28a745"  # Green - Đúng
                        elif score >= 40:
                            color = "#ffc107"  # Yellow/Orange - Gần đúng
                        else:
                            color = "#dc3545"  # Red - Sai
                        
                        # Build tooltip content with detailed error info
                        word_key = f"{word_analysis.word}_{word_idx}"
                        tooltip_parts = [f'<div class="tooltip-score">📊 Điểm: {score:.0f}/100</div>']
                        
                        if word_key in word_errors_map:
                            errors = word_errors_map[word_key]
                            tooltip_parts.append(f'<div class="tooltip-error-title">⚠️ Phát hiện {len(errors)} lỗi:</div>')
                            for idx, error in enumerate(errors, 1):
                                error_type = html.escape(error.error_type)
                                error_tag = html.escape(error.error_tag)
                                tooltip_parts.append(f'<div class="tooltip-error-item">')
                                tooltip_parts.append(f'<span class="tooltip-error-type">{idx}. {error_type}</span>')
                                tooltip_parts.append(f'<div class="tooltip-error-detail">🔊 {error_tag}</div>')
                                if error.definition:
                                    # Remove Korean text if present, truncate if too long
                                    definition = error.definition
                                    if '음소' not in definition:  # Skip Korean definitions
                                        definition = definition[:80] + '...' if len(definition) > 80 else definition
                                        definition_escaped = html.escape(definition)
                                        tooltip_parts.append(f'<div class="tooltip-error-detail">{definition_escaped}</div>')
                                tooltip_parts.append('</div>')
                        else:
                            tooltip_parts.append('<div class="tooltip-no-error">✅ Không có lỗi</div>')
                        
                        tooltip_content = ''.join(tooltip_parts)
                        
                        # Add word with color and beautiful tooltip
                        word_html = f'''<span class="word-tooltip" style="color: {color}; border-bottom-color: {color};">
                            {word}
                            <span class="tooltiptext">{tooltip_content}</span>
                        </span>'''
                        words_html.append(word_html)
                    
                    colored_html = tooltip_css
                    colored_html += '<div style="font-size: 18px; line-height: 2.5; padding: 15px; background-color: #f8f9fa; border-radius: 8px;">'
                    colored_html += ''.join(words_html)
                    colored_html += '</div>'
                    
                    # Legend
                    colored_html += '''
                    <div style="margin-top: 10px; font-size: 14px; color: #6c757d;">
                        <span style="color: #28a745; font-weight: 600;">● Đúng (≥70)</span>
                        <span style="margin-left: 15px; color: #ffc107; font-weight: 600;">● Gần đúng (40-69)</span>
                        <span style="margin-left: 15px; color: #dc3545; font-weight: 600;">● Sai (<40)</span>
                        <span style="margin-left: 20px;">💡 Di chuột lên từ để xem chi tiết lỗi</span>
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
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Nhấn & Nhịp ",
                        f"{results.proficiency_scores.stress_and_rhythm*2:.1f}/10",
                        help="Thang điểm 1-5, chuyển thành 2-10. Điểm càng cao càng tốt."
                    )
                with col2:
                    st.metric(
                        "Ngữ Điệu ",
                        f"{results.proficiency_scores.intonation*2:.1f}/10",
                        help="Thang điểm 1-5, chuyển thành 2-10. Điểm càng cao càng tốt."
                    )
                # Phân tích ngữ điệu
                st.markdown("<b>🎵 Phân Tích Ngữ Điệu</b>", unsafe_allow_html=True)
                prosody = results.prosody_analysis
                st.markdown(f"<b>Ngữ điệu</b><br>{prosody.intonation_status}", unsafe_allow_html=True)
                st.markdown(f"<b>Kết thúc câu</b><br>{prosody.sentence_ending}", unsafe_allow_html=True)
                st.markdown(f"<b>Khoảng dừng</b><br>{prosody.pauses}", unsafe_allow_html=True)
            
            with tab3:
                # Fluency scores
                st.subheader("Điểm Lưu Loát")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Phân Đoạn", f"{results.proficiency_scores.chunking*2:.1f}/10")
                with col2:
                    st.metric("Tốc Độ & Dừng", f"{results.proficiency_scores.speed_and_pause*2:.1f}/10")
                
                # Overall results
                st.subheader("Tổng Quan")
                render_overall_results(results)
    
    # Footer - compact at bottom
    st.caption("Được xây dựng với Streamlit")

if __name__ == "__main__":
    main()