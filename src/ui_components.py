"""Reusable UI components for the pronunciation evaluator."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import pandas as pd

from config.settings import settings
from config.constants import (
    DEFAULT_SCRIPTS,
    SCORE_SCALES,
    SCORE_COLORS,
    SCORE_THRESHOLDS
)
from src.results_processor import (
    ProcessedResults,
    ProficiencyScores,
    ProsodyAnalysis,
    WordAnalysis,
    PhonemeError
)

def render_settings_panel():
    """Render the collapsible settings panel."""
    # Force refresh of settings if old URL is detected
    if "farm2-phonics" in settings.api_url:
        settings.reset()
    
    with st.expander("⚙️ Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # API URL
            api_url = st.text_input(
                "API URL",
                value=settings.api_url,
                help="The Phonics API endpoint URL"
            )
            settings.api_url = api_url
            
            # API Key
            api_key = st.text_input(
                "API Key",
                value=settings.api_key or "",
                type="password",
                help="Your API authentication key"
            )
            if api_key:
                settings.api_key = api_key
        
        with col2:
            # Reference text selection
            script_options = ["Custom"] + DEFAULT_SCRIPTS
            selected_script = st.selectbox(
                "Practice Script",
                options=script_options,
                index=1,  # Default to first practice script
                help="Select a practice script or enter custom text"
            )
            
            # Custom text input
            if selected_script == "Custom":
                reference_text = st.text_area(
                    "Custom Script",
                    value="Enter your custom text here...",
                    height=100,
                    help="Enter the text you want to practice"
                )
            else:
                reference_text = selected_script
                st.text_area(
                    "Selected Script",
                    value=reference_text,
                    height=100,
                    disabled=True
                )
        
        # Validate settings
        is_valid, error_msg = settings.validate()
        if not is_valid:
            st.error(f"Configuration Error: {error_msg}")
        
        return reference_text

def render_practice_script_display(script_text: str):
    """Render the practice script in a prominent display.
    
    Args:
        script_text: The script text to display
    """
    st.markdown("### 📝 Practice Script")
    
    # Display script in a styled container
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
            font-size: 24px;
            line-height: 1.6;
            color: #212529;
            text-align: center;
            font-family: 'Georgia', serif;
        ">
            {script_text}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_file_upload_section():
    """Render file upload section.
    
    Returns:
        uploaded_file object or None
    """
    st.markdown("### 📁 Upload Audio File")
    st.info("📋 **Supported formats:** WAV, MP3, M4A, FLAC, OGG")
    st.info("📏 **Requirements:** Max 10MB, up to 5 minutes duration")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
        help="Upload an audio file containing your pronunciation practice"
    )
    
    if uploaded_file and st.session_state.get("uploaded_file_name") != uploaded_file.name:
        # New file uploaded, process it
        from src.audio_handler import process_uploaded_audio
        processed_audio = process_uploaded_audio(uploaded_file)
        if processed_audio:
            st.session_state.audio_data = processed_audio
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.audio_source = "upload"
    
    return uploaded_file

def render_analyze_button():
    """Render the analyze button.
    
    Returns:
        True if button was clicked, False otherwise
    """
    st.markdown("---")
    analyze_button = st.button(
        "🔍 Analyze Pronunciation",
        use_container_width=True,
        type="primary",
        disabled=st.session_state.get("audio_data") is None
    )
    
    return analyze_button

def render_proficiency_scores(scores: ProficiencyScores, percentages: Dict[str, float]):
    """Render proficiency scores dashboard.
    
    Args:
        scores: ProficiencyScores object
        percentages: Score percentages dictionary
    """
    st.markdown("### 📊 Proficiency Scores")
    
    # Create score data for visualization
    score_data = []
    for score_name, percentage in percentages.items():
        # Skip acoustic score as requested
        if score_name == "acoustic_score":
            continue
            
        scale_info = SCORE_SCALES[score_name]
        score_value = getattr(scores, score_name)
        
        # Determine color based on percentage
        if percentage >= SCORE_THRESHOLDS["excellent"]:
            color = SCORE_COLORS["excellent"]
        elif percentage >= SCORE_THRESHOLDS["good"]:
            color = SCORE_COLORS["good"]
        else:
            color = SCORE_COLORS["needs_improvement"]
        
        score_data.append({
            "Category": score_name.replace("_", " ").title(),
            "Score": score_value,
            "Percentage": percentage,
            "Color": color,
            "Max": scale_info["max"],
            "Unit": scale_info["unit"]
        })
    
    # Create columns for scores
    cols = st.columns(len(score_data))
    
    for i, (col, data) in enumerate(zip(cols, score_data)):
        with col:
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=data["Percentage"],
                title={'text': data["Category"]},
                domain={'x': [0, 1], 'y': [0, 1]},
                number={'suffix': "%"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': data["Color"]},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display actual score value
            if data["Unit"]:
                st.metric(
                    label="Score",
                    value=f"{data['Score']:.2f}/{data['Max']}{data['Unit']}"
                )
            else:
                st.metric(
                    label="Score",
                    value=f"{data['Score']:.2f}/{data['Max']}"
                )

def render_prosody_analysis(prosody: ProsodyAnalysis):
    """Render prosody analysis indicators.
    
    Args:
        prosody: ProsodyAnalysis object
    """
    st.markdown("### 🎵 Prosody Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    indicators = [
        ("Intonation", prosody.intonation_status, prosody.intonation_status == "Varied"),
        ("Sentence Ending", prosody.sentence_ending, prosody.sentence_ending == "Normal"),
        ("Pauses", prosody.pauses, prosody.pauses == "Natural")
    ]
    
    for col, (label, status, is_good) in zip([col1, col2, col3], indicators):
        with col:
            color = SCORE_COLORS["excellent"] if is_good else SCORE_COLORS["needs_improvement"]
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    padding: 20px;
                    border-radius: 10px;
                    background-color: {color}20;
                    border: 2px solid {color};
                ">
                    <h4 style="margin: 0; color: {color};">{label}</h4>
                    <p style="margin: 10px 0 0 0; font-size: 18px; font-weight: bold; color: {color};">
                        {status}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Show pause location if there were awkward pauses
    if hasattr(prosody, 'pause_sentence') and prosody.pause_sentence and prosody.pauses == "Awkward":
        st.markdown("#### ⚠️ Awkward Pause Detected")
        
        # Highlight [pause] markers in the sentence
        pause_sentence = prosody.pause_sentence
        if "[pause]" in pause_sentence:
            highlighted_sentence = pause_sentence.replace(
                "[pause]", 
                "<span style='background-color: #ff9999; font-weight: bold; padding: 2px 4px; border-radius: 3px;'>[pause]</span>"
            )
            st.markdown(
                f"**Sentence with pause markers:** {highlighted_sentence}",
                unsafe_allow_html=True
            )
        else:
            st.warning(f"Pause detected in: {pause_sentence}")

def render_word_analysis(word_analyses: List[WordAnalysis]):
    """Render word-by-word analysis table.
    
    Args:
        word_analyses: List of WordAnalysis objects
    """
    st.markdown("### 📖 Word-by-Word Analysis")
    
    if not word_analyses:
        st.info("No word analysis data available")
        return
    
    # Prepare data for display
    data = []
    for wa in word_analyses:
        # Determine score color
        score_color = "🟢" if wa.score >= 80 else "🟡" if wa.score >= 60 else "🔴"
        
        # Format unintelligible status
        unintelligible_status = "❌ Yes" if wa.is_unintelligible else "✅ No"
        
        # Format stress error
        stress_error_display = _format_stress_error(wa.stress_error_info)
        
        data.append({
            "Word": wa.word,
            "Word Index": wa.word_idx,
            "Score": f"{score_color} {wa.score:.1f}%",
            "Unintelligible": unintelligible_status,
            "Stress Error": stress_error_display
        })
    
    # Create DataFrame and display
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def _format_stress_error(stress_error_info: Dict[str, Any]) -> str:
    """Format stress error information for display.
    
    Args:
        stress_error_info: Dictionary containing stress error details
        
    Returns:
        Formatted string for stress error display
    """
    if not stress_error_info:
        return "✅ None"
    
    # Extract stress pattern information
    ref_stress = stress_error_info.get("reference_stress", "")
    user_stress = stress_error_info.get("user_stress", "")
    ref_syllable = stress_error_info.get("reference_stress_syllable", "")
    user_syllable = stress_error_info.get("user_stress_syllable", "")
    
    # Create pattern description
    pattern_desc = f"{ref_stress}→{user_stress}"
    
    # Create syllable comparison if available
    if ref_syllable and user_syllable:
        syllable_comp = f"{ref_syllable} vs {user_syllable}"
        return f"⚠️ {pattern_desc} | {syllable_comp}"
    else:
        return f"⚠️ {pattern_desc}"

def render_overall_results(results: ProcessedResults):
    """Render overall results summary.
    
    Args:
        results: ProcessedResults object
    """
    st.markdown("### 🎯 Overall Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Overall comment
        st.info(f"**Feedback:** {results.overall_comment}")
        
        # Reference score
        score_color = "🟢" if results.reference_score >= 80 else "🟡" if results.reference_score >= 60 else "🔴"
        st.metric(
            label="Reference Score",
            value=f"{score_color} {results.reference_score:.1f}%"
        )
    
    with col2:
        # Recognized text
        st.markdown("**What we heard:**")
        st.markdown(
            f"""
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                font-style: italic;
            ">
                "{results.recognized_text}"
            </div>
            """,
            unsafe_allow_html=True
        )

def render_loading_spinner():
    """Render a loading spinner during analysis."""
    with st.spinner("🔍 Analyzing your pronunciation... This may take a few seconds."):
        st.empty()

def render_error_message(error: str):
    """Render an error message.
    
    Args:
        error: Error message to display
    """
    st.error(f"❌ {error}")

def render_success_message(message: str):
    """Render a success message.
    
    Args:
        message: Success message to display
    """
    st.success(f"✅ {message}")

def render_phoneme_errors(phoneme_errors: List[PhonemeError]):
    """Render phoneme-level error analysis.
    
    Args:
        phoneme_errors: List of PhonemeError objects
    """
    st.markdown("### 🔍 Phoneme Analysis")
    
    if not phoneme_errors:
        st.info("✅ No phoneme errors detected - excellent pronunciation!")
        return
    
    st.markdown(f"**{len(phoneme_errors)} phoneme error(s) detected:**")
    
    for i, error in enumerate(phoneme_errors, 1):
        # Create a container for each error
        with st.container():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Error type badge
                error_color = SCORE_COLORS["needs_improvement"]
                st.markdown(
                    f"""
                    <div style="
                        background-color: {error_color}20;
                        border: 2px solid {error_color};
                        border-radius: 8px;
                        padding: 10px;
                        margin: 5px 0;
                        text-align: center;
                    ">
                        <strong style="color: {error_color};">Error #{i}</strong><br>
                        <span style="color: {error_color};">{error.error_type.title()}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                # Error details
                st.markdown(f"**Word:** {error.word} (position #{error.word_idx})")
                st.markdown(f"**Sound Error:** {error.error_tag}")
                
                # Highlighted spell view
                if error.spell_view:
                    # Parse the spell_view to highlight the error
                    spell_parts = error.spell_view.split('[')
                    if len(spell_parts) > 1:
                        before = spell_parts[0]
                        error_part_and_after = spell_parts[1].split(']')
                        if len(error_part_and_after) > 1:
                            error_part = error_part_and_after[0]
                            after = error_part_and_after[1]
                            highlighted_word = f"{before}<span style='background-color: #ffeb3b; font-weight: bold; padding: 2px 4px; border-radius: 3px;'>{error_part}</span>{after}"
                        else:
                            highlighted_word = error.spell_view
                    else:
                        highlighted_word = error.spell_view
                    
                    st.markdown(
                        f"**Spelling:** {highlighted_word}",
                        unsafe_allow_html=True
                    )
                
                # Definition if available (Korean definition)
                if error.definition:
                    st.markdown(f"**Description:** {error.definition}")
            
            # Add separator line
            if i < len(phoneme_errors):
                st.markdown("---")

def render_audio_player(audio_data: bytes):
    """Render audio player for recorded audio.
    
    Args:
        audio_data: Audio bytes to play
    """
    if audio_data:
        st.audio(audio_data, format='audio/wav')