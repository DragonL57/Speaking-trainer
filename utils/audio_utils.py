"""Audio utility functions."""

import base64
import io
import wave
import logging
from typing import Tuple, Optional
from pydub import AudioSegment

from config.constants import MAX_AUDIO_SIZE_MB, SAMPLE_RATE, CHANNELS

logger = logging.getLogger(__name__)

def convert_to_base64(audio_file: io.BytesIO) -> str:
    """Convert audio file to base64 string.
    
    Args:
        audio_file: Audio file buffer
        
    Returns:
        Base64 encoded string
    """
    audio_file.seek(0)
    audio_bytes = audio_file.read()
    return base64.b64encode(audio_bytes).decode('utf-8')

def validate_audio_format(audio_data: bytes) -> Tuple[bool, str]:
    """Validate audio format and properties.
    
    Args:
        audio_data: Audio data bytes
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Check file size
        size_mb = len(audio_data) / (1024 * 1024)
        if size_mb > MAX_AUDIO_SIZE_MB:
            return False, f"Audio file too large ({size_mb:.1f}MB). Maximum size is {MAX_AUDIO_SIZE_MB}MB"
        
        # Try to open as WAV
        audio_buffer = io.BytesIO(audio_data)
        
        try:
            with wave.open(audio_buffer, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                duration = n_frames / framerate
        except wave.Error:
            # Try to convert with pydub
            try:
                audio = AudioSegment.from_file(io.BytesIO(audio_data))
                duration = len(audio) / 1000.0
                channels = audio.channels
                framerate = audio.frame_rate
            except Exception as e:
                return False, f"Invalid audio format: {str(e)}"
        
        # Validate duration
        if duration < 0.5:
            return False, "Recording is too short (minimum 0.5 seconds)"
        
        if duration > 300:
            return False, "Recording is too long (maximum 5 minutes)"
        
        return True, f"Valid audio: {duration:.1f}s, {framerate}Hz, {channels} channel(s)"
        
    except Exception as e:
        logger.error(f"Error validating audio: {e}")
        return False, f"Failed to validate audio: {str(e)}"

def get_audio_duration(audio_data: bytes) -> Optional[float]:
    """Get duration of audio in seconds.
    
    Args:
        audio_data: Audio data bytes
        
    Returns:
        Duration in seconds or None if unable to determine
    """
    try:
        audio_buffer = io.BytesIO(audio_data)
        
        # Try WAV format first
        try:
            with wave.open(audio_buffer, 'rb') as wav_file:
                n_frames = wav_file.getnframes()
                framerate = wav_file.getframerate()
                return n_frames / framerate
        except wave.Error:
            # Try with pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            return len(audio) / 1000.0
            
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return None

def compress_audio_if_needed(audio_data: bytes) -> bytes:
    """Compress audio if it exceeds size limits.
    
    Args:
        audio_data: Original audio data
        
    Returns:
        Compressed audio data or original if compression not needed
    """
    size_mb = len(audio_data) / (1024 * 1024)
    
    if size_mb <= MAX_AUDIO_SIZE_MB:
        return audio_data
    
    try:
        # Load audio
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        
        # Calculate compression ratio
        compression_ratio = MAX_AUDIO_SIZE_MB / size_mb
        
        # Reduce bitrate
        new_bitrate = int(128000 * compression_ratio)  # Start with 128kbps
        
        # Export with lower bitrate
        output_buffer = io.BytesIO()
        audio.export(
            output_buffer,
            format="wav",
            bitrate=f"{new_bitrate}",
            parameters=["-ac", str(CHANNELS), "-ar", str(SAMPLE_RATE)]
        )
        
        output_buffer.seek(0)
        compressed_data = output_buffer.read()
        
        logger.info(f"Compressed audio from {size_mb:.1f}MB to {len(compressed_data)/(1024*1024):.1f}MB")
        return compressed_data
        
    except Exception as e:
        logger.error(f"Error compressing audio: {e}")
        return audio_data  # Return original if compression fails

def normalize_audio_format(audio_data: bytes) -> Optional[bytes]:
    """Normalize audio to standard format (16kHz, mono, WAV).
    
    Args:
        audio_data: Input audio data
        
    Returns:
        Normalized audio data or None if conversion fails
    """
    try:
        # Load audio
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(CHANNELS)
        
        # Set sample rate
        audio = audio.set_frame_rate(SAMPLE_RATE)
        
        # Export as WAV
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format="wav")
        
        output_buffer.seek(0)
        return output_buffer.read()
        
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}")
        return None