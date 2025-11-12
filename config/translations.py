"""Vietnamese translations for the application."""

TRANSLATIONS = {
    "en": {
        # App titles
        "app_title": "Pronunciation & Prosody Evaluator",
        "app_description": "Practice pronunciation by reading scripts aloud and receive AI-powered feedback",
        
        # Settings panel
        "settings": "Settings",
        "api_url": "API URL",
        "api_url_help": "The Phonics API endpoint URL",
        "api_key": "API Key",
        "api_key_help": "Your API authentication key",
        "practice_script": "Practice Script",
        "practice_script_help": "Select a practice script or enter custom text",
        "custom": "Custom",
        "custom_script": "Custom Script",
        "custom_script_placeholder": "Enter your custom text here...",
        "custom_script_help": "Enter the text you want to practice",
        "selected_script": "Selected Script",
        "config_error": "Configuration Error",
        
        # Sections
        "practice_script_title": "📝 Practice Script",
        "record_audio": "🎤 Record Audio",
        "record_prompt": "🎙️ Click to record your pronunciation",
        "upload_audio": "📁 Upload Audio File",
        "supported_formats": "📋 **Supported formats:** WAV, MP3, M4A, FLAC, OGG",
        "requirements": "📏 **Requirements:** Max 10MB, up to 5 minutes duration",
        "choose_audio": "Choose an audio file",
        "choose_audio_help": "Upload an audio file containing your pronunciation practice",
        "your_audio": "🔊 Your Audio",
        "source_upload": "📁 **Source:** Uploaded file | **Format:** WAV, Mono, 16kHz, 16-bit PCM",
        "source_recording": "🎤 **Source:** Recording | **Format:** WAV, Mono, 16kHz, 16-bit PCM",
        
        # Buttons
        "analyze_button": "🔍 Analyze Pronunciation",
        "download_results": "📥 Download Results (JSON)",
        "download_json": "Download JSON",
        
        # Status messages
        "analyzing": "🔍 Analyzing your pronunciation... This may take a few seconds.",
        "api_key_required": "Please configure your API key in the settings panel",
        "analysis_complete": "Analysis completed successfully!",
        "api_error": "API Error",
        "unexpected_error": "An unexpected error occurred",
        "error_processing_audio": "Error processing audio",
        
        # Results
        "analysis_results": "📊 Analysis Results",
        "overall_assessment": "🎯 Overall Assessment",
        "feedback": "Feedback",
        "reference_score": "Reference Score",
        "what_we_heard": "What we heard:",
        "proficiency_scores": "📊 Proficiency Scores",
        "score": "Score",
        "prosody_analysis": "🎵 Prosody Analysis",
        "intonation": "Intonation",
        "sentence_ending": "Sentence Ending",
        "pauses": "Pauses",
        "awkward_pause": "⚠️ Awkward Pause Detected",
        "pause_markers": "Sentence with pause markers:",
        "pause_in": "Pause detected in:",
        "word_analysis": "📖 Word-by-Word Analysis",
        "no_word_analysis": "No word analysis data available",
        "word": "Word",
        "word_index": "Word Index",
        "unintelligible": "Unintelligible",
        "stress_error": "Stress Error",
        "yes": "Yes",
        "no": "No",
        "none": "None",
        "phoneme_analysis": "🔍 Phoneme Analysis",
        "no_phoneme_errors": "✅ No phoneme errors detected - excellent pronunciation!",
        "phoneme_errors_detected": "phoneme error(s) detected:",
        "error": "Error",
        "sound_error": "Sound Error",
        "spelling": "Spelling",
        "description": "Description",
        
        # Footer
        "footer_text": "Built with ❤️ using Streamlit and Phonics AI API",
        "footer_support": "For support, please contact your administrator",
        
        # Score categories
        "pronunciation_score": "Pronunciation Score",
        "fluency_score": "Fluency Score",
        "completeness_score": "Completeness Score",
        "prosody_score": "Prosody Score",
        
        # Prosody statuses
        "varied": "Varied",
        "monotonous": "Monotonous",
        "normal": "Normal",
        "natural": "Natural",
        "awkward": "Awkward",
    },
    "vi": {
        # App titles
        "app_title": "Đánh Giá Phát Âm & Ngữ Điệu",
        "app_description": "Luyện phát âm bằng cách đọc to các đoạn văn và nhận phản hồi từ AI",
        
        # Settings panel
        "settings": "Cài Đặt",
        "api_url": "URL API",
        "api_url_help": "Địa chỉ API của Phonics",
        "api_key": "Khóa API",
        "api_key_help": "Khóa xác thực API của bạn",
        "practice_script": "Đoạn Văn Luyện Tập",
        "practice_script_help": "Chọn đoạn văn luyện tập hoặc nhập văn bản tùy chỉnh",
        "custom": "Tùy Chỉnh",
        "custom_script": "Văn Bản Tùy Chỉnh",
        "custom_script_placeholder": "Nhập văn bản tùy chỉnh tại đây...",
        "custom_script_help": "Nhập văn bản bạn muốn luyện tập",
        "selected_script": "Đoạn Văn Đã Chọn",
        "config_error": "Lỗi Cấu Hình",
        
        # Sections
        "practice_script_title": "📝 Đoạn Văn Luyện Tập",
        "record_audio": "🎤 Thu Âm",
        "record_prompt": "🎙️ Nhấn để ghi âm phát âm của bạn",
        "upload_audio": "📁 Tải Lên File Âm Thanh",
        "supported_formats": "📋 **Định dạng hỗ trợ:** WAV, MP3, M4A, FLAC, OGG",
        "requirements": "📏 **Yêu cầu:** Tối đa 10MB, thời lượng tối đa 5 phút",
        "choose_audio": "Chọn file âm thanh",
        "choose_audio_help": "Tải lên file âm thanh chứa bài luyện phát âm của bạn",
        "your_audio": "🔊 Âm Thanh Của Bạn",
        "source_upload": "📁 **Nguồn:** File tải lên | **Định dạng:** WAV, Mono, 16kHz, 16-bit PCM",
        "source_recording": "🎤 **Nguồn:** Ghi âm | **Định dạng:** WAV, Mono, 16kHz, 16-bit PCM",
        
        # Buttons
        "analyze_button": "🔍 Phân Tích Phát Âm",
        "download_results": "📥 Tải Kết Quả (JSON)",
        "download_json": "Tải JSON",
        
        # Status messages
        "analyzing": "🔍 Đang phân tích phát âm của bạn... Có thể mất vài giây.",
        "api_key_required": "Vui lòng cấu hình khóa API trong bảng cài đặt",
        "analysis_complete": "Phân tích hoàn tất thành công!",
        "api_error": "Lỗi API",
        "unexpected_error": "Đã xảy ra lỗi không mong muốn",
        "error_processing_audio": "Lỗi xử lý âm thanh",
        
        # Results
        "analysis_results": "📊 Kết Quả Phân Tích",
        "overall_assessment": "🎯 Đánh Giá Tổng Quan",
        "feedback": "Nhận xét",
        "reference_score": "Điểm Tham Chiếu",
        "what_we_heard": "Những gì chúng tôi nghe được:",
        "proficiency_scores": "📊 Điểm Thành Thạo",
        "score": "Điểm",
        "prosody_analysis": "🎵 Phân Tích Ngữ Điệu",
        "intonation": "Ngữ Điệu",
        "sentence_ending": "Kết Thúc Câu",
        "pauses": "Khoảng Dừng",
        "awkward_pause": "⚠️ Phát Hiện Khoảng Dừng Không Tự Nhiên",
        "pause_markers": "Câu có dấu khoảng dừng:",
        "pause_in": "Khoảng dừng phát hiện trong:",
        "word_analysis": "📖 Phân Tích Từng Từ",
        "no_word_analysis": "Không có dữ liệu phân tích từ",
        "word": "Từ",
        "word_index": "Chỉ Số Từ",
        "unintelligible": "Không Rõ Ràng",
        "stress_error": "Lỗi Trọng Âm",
        "yes": "Có",
        "no": "Không",
        "none": "Không có",
        "phoneme_analysis": "🔍 Phân Tích Âm Vị",
        "no_phoneme_errors": "✅ Không phát hiện lỗi âm vị - phát âm xuất sắc!",
        "phoneme_errors_detected": "lỗi âm vị được phát hiện:",
        "error": "Lỗi",
        "sound_error": "Lỗi Âm Thanh",
        "spelling": "Chính Tả",
        "description": "Mô Tả",
        
        # Footer
        "footer_text": "Được xây dựng với ❤️ sử dụng Streamlit và Phonics AI API",
        "footer_support": "Để được hỗ trợ, vui lòng liên hệ quản trị viên",
        
        # Score categories
        "pronunciation_score": "Điểm Phát Âm",
        "fluency_score": "Điểm Lưu Loát",
        "completeness_score": "Điểm Hoàn Chỉnh",
        "prosody_score": "Điểm Ngữ Điệu",
        
        # Prosody statuses
        "varied": "Đa Dạng",
        "monotonous": "Đơn Điệu",
        "normal": "Bình Thường",
        "natural": "Tự Nhiên",
        "awkward": "Không Tự Nhiên",
    }
}

def get_text(key: str, language: str = "vi") -> str:
    """Get translated text for a given key.
    
    Args:
        key: Translation key
        language: Language code (en or vi)
        
    Returns:
        Translated text
    """
    return TRANSLATIONS.get(language, TRANSLATIONS["vi"]).get(key, key)
