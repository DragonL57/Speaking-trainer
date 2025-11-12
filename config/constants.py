"""Application constants and configuration values."""

# API Configuration
DEFAULT_API_URL = "https://dev-farm-phonics.ai-poly.com/api/phonics"
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Audio Configuration
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 16000  # 16kHz as required by API
CHANNELS = 1  # Mono as required by API
SAMPLE_WIDTH = 2  # 16-bit PCM (2 bytes)
MAX_AUDIO_SIZE_MB = 10
MAX_RECORDING_DURATION = 300  # 5 minutes in seconds

# Score Thresholds
SCORE_THRESHOLDS = {
    "excellent": 80,
    "good": 60,
    "needs_improvement": 0
}

# Score Colors
SCORE_COLORS = {
    "excellent": "#28a745",  # Green
    "good": "#ffc107",       # Yellow
    "needs_improvement": "#dc3545"  # Red
}

# UI Text Constants
APP_TITLE = "Đánh Giá Phát Âm & Ngữ Điệu"
APP_DESCRIPTION = "Luyện phát âm tiếng Anh bằng cách đọc to các đoạn văn và nhận phản hồi từ AI"

# Default Practice Scripts (Keep in English for pronunciation practice)
DEFAULT_SCRIPTS = [
    "The quick brown fox jumps over the lazy dog.",
    "She sells seashells by the seashore.",
    "Peter Piper picked a peck of pickled peppers.",
    "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
    "I scream, you scream, we all scream for ice cream!",
    "The rain in Spain stays mainly in the plain.",
    "A proper copper coffee pot.",
    "Betty Botter bought some butter, but she said the butter's bitter."
]

# Prosody Status Messages
PROSODY_STATUS = {
    "intonation": {
        "good": "Đa dạng",
        "poor": "Đơn điệu"
    },
    "sentence_ending": {
        "normal": "Bình thường",
        "rising": "Tăng dần",
        "falling": "Giảm dần"
    },
    "speech_flow": {
        "good": "Lưu loát",
        "poor": "Bị phân mảnh"
    },
    "pauses": {
        "good": "Tự nhiên",
        "poor": "Không tự nhiên"
    }
}

# Score Scale Information
SCORE_SCALES = {
    "acoustic_score": {"min": 0, "max": 100, "unit": "%"},
    "holistic_score": {"min": 1, "max": 5, "unit": ""},
    "segmental_accuracy": {"min": 1, "max": 5, "unit": ""},
    "chunking": {"min": 1, "max": 5, "unit": ""},
    "speed_and_pause": {"min": 1, "max": 5, "unit": ""},
    "stress_and_rhythm": {"min": 1, "max": 5, "unit": ""},
    "intonation": {"min": 1, "max": 5, "unit": ""}
}