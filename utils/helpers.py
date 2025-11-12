"""General utility helper functions."""

import time
import hashlib
import json
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return "00:00"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def generate_session_id() -> str:
    """Generate a unique session ID.
    
    Returns:
        Session ID string
    """
    timestamp = str(time.time()).encode()
    return hashlib.md5(timestamp).hexdigest()[:12]

def safe_json_dumps(data: Any, indent: Optional[int] = 2) -> str:
    """Safely convert data to JSON string.
    
    Args:
        data: Data to convert
        indent: JSON indentation level
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Error converting to JSON: {e}")
        return "{}"

def calculate_confidence_level(score: float) -> str:
    """Calculate confidence level from score.
    
    Args:
        score: Score value (0-100)
        
    Returns:
        Confidence level string
    """
    if score >= 90:
        return "Very High"
    elif score >= 80:
        return "High"
    elif score >= 70:
        return "Medium"
    elif score >= 60:
        return "Low"
    else:
        return "Very Low"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_timestamp() -> str:
    """Get current timestamp in ISO format.
    
    Returns:
        ISO timestamp string
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries recursively.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (overwrites dict1 values)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_error_message(exception: Exception) -> str:
    """Extract user-friendly error message from exception.
    
    Args:
        exception: Exception object
        
    Returns:
        Error message string
    """
    error_msg = str(exception)
    
    # Clean up common error patterns
    if "Connection refused" in error_msg:
        return "Unable to connect to the service. Please check your network connection."
    elif "timeout" in error_msg.lower():
        return "The request timed out. Please try again."
    elif "401" in error_msg or "unauthorized" in error_msg.lower():
        return "Authentication failed. Please check your API key."
    elif "403" in error_msg or "forbidden" in error_msg.lower():
        return "Access denied. Please check your permissions."
    elif "404" in error_msg:
        return "The requested resource was not found."
    elif "500" in error_msg or "internal server error" in error_msg.lower():
        return "Server error. Please try again later."
    
    # Return original message if no pattern matches
    return error_msg