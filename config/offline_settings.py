"""Configuration management for offline mode."""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class OfflineSettings:
    """Settings for offline pronunciation analyzer."""
    
    def __init__(self):
        self._use_offline: bool = True
        self._whisper_model: str = "base"
        self._device: str = "cpu"
        self._models_dir: Path = Path.home() / ".pronunciation_evaluator" / "models"
        
    @property
    def use_offline(self) -> bool:
        """Whether to use offline mode."""
        return os.getenv("USE_OFFLINE", "true").lower() == "true"
    
    @property
    def whisper_model(self) -> str:
        """Whisper model size (tiny, base, small, medium, large)."""
        return os.getenv("WHISPER_MODEL", self._whisper_model)
    
    @whisper_model.setter
    def whisper_model(self, value: str):
        """Set Whisper model size."""
        valid_sizes = ["tiny", "base", "small", "medium", "large"]
        if value in valid_sizes:
            self._whisper_model = value
    
    @property
    def device(self) -> str:
        """Device to run models on (cpu, cuda)."""
        return os.getenv("DEVICE", self._device)
    
    @device.setter
    def device(self, value: str):
        """Set device."""
        if value in ["cpu", "cuda"]:
            self._device = value
    
    @property
    def models_dir(self) -> Path:
        """Directory to store downloaded models."""
        return self._models_dir
    
    def validate(self) -> tuple[bool, str]:
        """Validate offline settings.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if models directory exists, create if not
        if not self.models_dir.exists():
            try:
                self.models_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create models directory: {str(e)}"
        
        return True, ""

# Global settings instance
offline_settings = OfflineSettings()
