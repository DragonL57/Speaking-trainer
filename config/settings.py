"""Configuration management for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from .constants import DEFAULT_API_URL

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class Settings:
    """Application settings management."""
    
    def __init__(self):
        self._api_url: Optional[str] = None
        self._api_key: Optional[str] = None
        self._debug: bool = False
        self._max_audio_size_mb: int = 10
        
    @property
    def api_url(self) -> str:
        """Get API URL from environment or default."""
        if self._api_url is None:
            self._api_url = os.getenv("API_URL", DEFAULT_API_URL)
        # Force update if still using old URL
        elif "farm2-phonics" in self._api_url:
            self._api_url = os.getenv("API_URL", DEFAULT_API_URL)
        return self._api_url
    
    @api_url.setter
    def api_url(self, value: str):
        """Set API URL."""
        self._api_url = value
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment."""
        if self._api_key is None:
            self._api_key = os.getenv("API_KEY")
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str):
        """Set API key."""
        self._api_key = value
    
    @property
    def debug(self) -> bool:
        """Get debug mode setting."""
        if self._debug is False:
            self._debug = os.getenv("DEBUG", "False").lower() == "true"
        return self._debug
    
    @property
    def max_audio_size_mb(self) -> int:
        """Get maximum audio file size in MB."""
        if self._max_audio_size_mb == 10:
            self._max_audio_size_mb = int(os.getenv("MAX_AUDIO_SIZE_MB", "10"))
        return self._max_audio_size_mb
    
    def validate(self) -> tuple[bool, str]:
        """Validate settings configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.api_url:
            return False, "API URL is required"
        
        if not self.api_url.startswith(("http://", "https://")):
            return False, "API URL must start with http:// or https://"
        
        if self.max_audio_size_mb < 1 or self.max_audio_size_mb > 50:
            return False, "Max audio size must be between 1 and 50 MB"
        
        return True, ""
    
    def reset(self):
        """Reset all settings to defaults."""
        self._api_url = None
        self._api_key = None
        self._debug = False
        self._max_audio_size_mb = 10

# Global settings instance
settings = Settings()
# Reset to ensure latest defaults are loaded
settings.reset()