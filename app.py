"""Main Streamlit application for Pronunciation & Prosody Evaluator."""

import streamlit as st
import logging
from typing import Optional
import time

from config.constants import APP_TITLE, APP_DESCRIPTION
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
    
    # Header
    st.title(f"🎤 {APP_TITLE}")
    st.markdown(APP_DESCRIPTION)
    st.markdown("---")
    
    # Settings panel
    reference_text = render_settings_panel()
    st.session_state.reference_text = reference_text
    
    # Practice script display
    render_practice_script_display(reference_text)
    
    # Audio input section
    st.markdown("---")
    
    # Direct recording section
    st.markdown("### 🎤 Record Audio")
    audio_file = st.audio_input("🎙️ Click to record your pronunciation", key="audio_recorder")
    
    if audio_file:
        # Process the audio to ensure correct format
        try:
            # Read the uploaded file
            audio_file.seek(0)
            raw_audio = audio_file.read()
            
            # Convert to proper format using pydub
            from pydub import AudioSegment
            import io
            
            # Load the audio
            audio = AudioSegment.from_file(io.BytesIO(raw_audio))
            
            # Convert to required format: mono, 16kHz, 16-bit PCM
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Export as WAV
            wav_buffer = io.BytesIO()
            audio.export(
                wav_buffer, 
                format="wav",
                parameters=["-acodec", "pcm_s16le"]  # Force 16-bit PCM
            )
            wav_buffer.seek(0)
            audio_data = wav_buffer.read()
            
            st.session_state.audio_data = audio_data
            st.session_state.audio_source = "recording"
            
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            logger.error(f"Audio processing error: {e}")
    
    # File upload section
    st.markdown("---")
    uploaded_file = render_file_upload_section()
    
    # Show audio player if we have audio data
    if st.session_state.get("audio_data"):
        st.markdown("### 🔊 Your Audio")
        render_audio_player(st.session_state.audio_data)
        
        # Show audio source info
        source = st.session_state.get("audio_source", "recording")
        if source == "upload":
            st.info(f"📁 **Source:** Uploaded file | **Format:** WAV, Mono, 16kHz, 16-bit PCM")
        else:
            st.info(f"🎤 **Source:** Recording | **Format:** WAV, Mono, 16kHz, 16-bit PCM")
    
    # Analyze button
    analyze_button = render_analyze_button()
    
    # Analysis logic
    if analyze_button and st.session_state.audio_data:
        with st.spinner("🔍 Analyzing your pronunciation... This may take a few seconds."):
            try:
                # Validate API key
                if not settings.api_key:
                    render_error_message("Please configure your API key in the settings panel")
                    return
                
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
                
                render_success_message("Analysis completed successfully!")
                
            except PronunciationAPIError as e:
                render_error_message(f"API Error: {str(e)}")
                return
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                render_error_message(f"An unexpected error occurred: {str(e)}")
                return
    
    # Display results
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
        results = st.session_state.analysis_results
        
        # Overall results
        render_overall_results(results)
        
        # Proficiency scores
        st.markdown("---")
        processor = ResultsProcessor()
        percentages = processor.calculate_score_percentages(results.proficiency_scores)
        render_proficiency_scores(results.proficiency_scores, percentages)
        
        # Prosody analysis
        st.markdown("---")
        render_prosody_analysis(results.prosody_analysis)
        
        # Word analysis
        st.markdown("---")
        render_word_analysis(results.word_analyses)
        
        # Phoneme errors
        st.markdown("---")
        render_phoneme_errors(results.phoneme_errors)
        
        # Export results button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Download Results (JSON)", use_container_width=True):
                import json
                results_json = json.dumps(results.raw_response, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=results_json,
                    file_name=f"pronunciation_analysis_{int(time.time())}.json",
                    mime="application/json"
                )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #6c757d;">
            <p>Built with ❤️ using Streamlit and Phonics AI API</p>
            <p style="font-size: 12px;">For support, please contact your administrator</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()