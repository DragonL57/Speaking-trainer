"""Audio recording and processing functionality."""

import io
import wave
import logging
import numpy as np
from typing import Optional, Tuple, Union
import streamlit as st
from pydub import AudioSegment
import time

from config.constants import (
    SAMPLE_RATE, 
    CHANNELS, 
    MAX_RECORDING_DURATION,
    AUDIO_FORMAT,
    SAMPLE_WIDTH,
    MAX_AUDIO_SIZE_MB
)

logger = logging.getLogger(__name__)

class SimpleAudioRecorder:
    """Simplified audio recorder using st.audio_input (fallback option)."""
    
    @staticmethod
    def record_audio() -> Optional[bytes]:
        """Record audio using Streamlit's audio input.
        
        Returns:
            Audio bytes or None
        """
        audio_bytes = st.audio_input("Click to record", key="audio_recorder")
        
        if audio_bytes:
            # Convert to WAV if needed
            try:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
                
                # Convert to standard format required by API
                # Mono channel
                audio = audio.set_channels(CHANNELS)
                # 16kHz sample rate
                audio = audio.set_frame_rate(SAMPLE_RATE)
                # 16-bit sample width
                audio = audio.set_sample_width(2)  # 2 bytes = 16 bits
                
                # Export as WAV with specific parameters
                wav_buffer = io.BytesIO()
                audio.export(
                    wav_buffer, 
                    format="wav",
                    parameters=["-acodec", "pcm_s16le"]  # Force 16-bit PCM
                )
                wav_buffer.seek(0)
                
                return wav_buffer.read()
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                st.error("Failed to process audio recording")
                return None
                
        return None

def process_uploaded_audio(uploaded_file) -> Optional[bytes]:
    """Process uploaded audio file and convert to required format.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Processed audio bytes or None if processing fails
    """
    if not uploaded_file:
        return None
        
    try:
        # Check file size (uploaded_file.size is in bytes)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            st.error(f"File too large ({file_size_mb:.1f}MB). Maximum size is {MAX_AUDIO_SIZE_MB}MB.")
            return None
        
        # Read the uploaded file
        audio_bytes = uploaded_file.read()
        
        # Load audio using pydub
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Convert to required format
        audio = audio.set_channels(CHANNELS)  # Mono
        audio = audio.set_frame_rate(SAMPLE_RATE)  # 16kHz
        audio = audio.set_sample_width(SAMPLE_WIDTH)  # 16-bit
        
        # Check duration
        duration_seconds = len(audio) / 1000  # pydub uses milliseconds
        if duration_seconds > MAX_RECORDING_DURATION:
            st.error(f"Audio too long ({duration_seconds:.1f}s). Maximum duration is {MAX_RECORDING_DURATION}s.")
            return None
        
        # Export as WAV with specific parameters
        wav_buffer = io.BytesIO()
        audio.export(
            wav_buffer,
            format="wav",
            parameters=["-acodec", "pcm_s16le"]  # Force 16-bit PCM
        )
        wav_buffer.seek(0)
        
        # Display success message
        st.success(f"✅ Audio file processed successfully! Duration: {duration_seconds:.1f}s")
        
        return wav_buffer.read()
        
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {e}")
        st.error(f"Failed to process audio file: {str(e)}")
        return None

def play_audio(audio_data: bytes):
    """Play audio in the browser.
    
    Args:
        audio_data: Audio bytes to play
    """
    if audio_data:
        st.audio(audio_data, format='audio/wav')
    else:
        st.warning("No audio to play")