"""Input validation functions."""

import re
from typing import Tuple, Optional

def validate_api_key(api_key: Optional[str]) -> Tuple[bool, str]:
    """Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is required"
    
    if len(api_key) < 10:
        return False, "API key appears to be too short"
    
    # Basic validation - alphanumeric with possible hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9_\-]+$', api_key):
        return False, "API key contains invalid characters"
    
    return True, ""

def validate_script_text(text: str) -> Tuple[bool, str]:
    """Validate practice script text.
    
    Args:
        text: Script text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Script text cannot be empty"
    
    # Remove extra whitespace
    cleaned_text = ' '.join(text.split())
    
    if len(cleaned_text) < 3:
        return False, "Script text is too short (minimum 3 characters)"
    
    if len(cleaned_text) > 1000:
        return False, "Script text is too long (maximum 1000 characters)"
    
    # Check for valid characters (letters, numbers, punctuation, spaces)
    if not re.match(r'^[a-zA-Z0-9\s\.,!?\'";\-:()]+$', cleaned_text):
        return False, "Script contains invalid characters"
    
    return True, ""

def validate_audio_file(file_data: bytes) -> Tuple[bool, str]:
    """Validate uploaded audio file.
    
    Args:
        file_data: File data bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_data:
        return False, "No audio data provided"
    
    # Check file signature (magic numbers)
    if len(file_data) < 4:
        return False, "File is too small to be valid audio"
    
    # Check for common audio format signatures
    # WAV: RIFF
    if file_data[:4] == b'RIFF':
        return True, ""
    # MP3: ID3 or 0xFF 0xFB
    elif file_data[:3] == b'ID3' or (file_data[0] == 0xFF and (file_data[1] & 0xE0) == 0xE0):
        return True, ""
    # M4A/MP4: ftyp
    elif file_data[4:8] == b'ftyp':
        return True, ""
    # OGG: OggS
    elif file_data[:4] == b'OggS':
        return True, ""
    
    return False, "Unsupported audio format"

def sanitize_input(text: str) -> str:
    """Sanitize user input text.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Limit length
    max_length = 1000
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Invalid URL format"
    
    return True, ""