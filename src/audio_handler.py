"""Audio recording and processing functionality."""

import io
import wave
import logging
import numpy as np
from typing import Optional, Tuple, Union
import streamlit as st
import soundfile as sf
from scipy import signal
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


def convert_audio_to_wav(audio_bytes: bytes) -> Optional[bytes]:
    """Convert audio bytes to WAV format (mono, 16kHz, 16-bit PCM).
    
    Args:
        audio_bytes: Input audio bytes in any format
        
    Returns:
        WAV audio bytes or None if conversion fails
    """
    try:
        # Read audio using soundfile
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
        
        # Convert stereo to mono if needed
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Resample to 16kHz if needed
        if sample_rate != SAMPLE_RATE:
            num_samples = int(len(audio_data) * SAMPLE_RATE / sample_rate)
            audio_data = signal.resample(audio_data, num_samples)
        
        # Normalize to int16 range
        if audio_data.dtype != np.int16:
            # Normalize to -1.0 to 1.0 range if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            # Convert to int16
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write to WAV format
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_data, SAMPLE_RATE, format='WAV', subtype='PCM_16')
        wav_buffer.seek(0)
        
        return wav_buffer.read()
        
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return None

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
            # Convert to WAV format
            try:
                wav_data = convert_audio_to_wav(audio_bytes)
                if wav_data:
                    return wav_data
                else:
                    st.error("Failed to process audio recording")
                    return None
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
            st.error(f"File quá lớn ({file_size_mb:.1f}MB). Kích thước tối đa là {MAX_AUDIO_SIZE_MB}MB.")
            return None
        
        # Read the uploaded file
        audio_bytes = uploaded_file.read()
        
        # Convert to WAV format using soundfile
        wav_data = convert_audio_to_wav(audio_bytes)
        
        if not wav_data:
            st.error("Không thể xử lý file âm thanh")
            return None
        
        # Check duration
        audio_data, sample_rate = sf.read(io.BytesIO(wav_data))
        duration_seconds = len(audio_data) / sample_rate
        
        if duration_seconds > MAX_RECORDING_DURATION:
            st.error(f"Âm thanh quá dài ({duration_seconds:.1f}s). Thời lượng tối đa là {MAX_RECORDING_DURATION}s.")
            return None
        
        # Display success message
        st.success(f"✅ File âm thanh đã được xử lý thành công! Thời lượng: {duration_seconds:.1f}s")
        
        return wav_data
        
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {e}")
        st.error(f"Không thể xử lý file âm thanh: {str(e)}")
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