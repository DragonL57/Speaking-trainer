# Pronunciation & Prosody Evaluator

A web-based application that helps students practice pronunciation by reading predefined scripts aloud and receiving comprehensive AI-powered feedback on their speech quality, pronunciation accuracy, and prosody.

## Features

- 🎤 Browser-based audio recording
- 📁 Audio file upload support (WAV, MP3, M4A, FLAC, OGG)
- 📝 Predefined practice scripts
- 🔊 Audio playback functionality
- 📊 Comprehensive pronunciation analysis
- 📈 Detailed proficiency scores
- 🎯 Word-by-word feedback with stress error detection
- 🔍 Phoneme-level error analysis
- 🎵 Prosody analysis (intonation, pauses, sentence ending)

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your API settings:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your API key and optionally modify the API URL:
   ```bash
   # Default API URL (development environment)
   API_URL=https://dev-farm-phonics.ai-poly.com/api/phonics
   API_KEY=your_api_key_here
   ```
5. Run the application:
   ```bash
   streamlit run app.py
   ```

## Configuration

### API Settings

The application uses the Phonics AI API for pronunciation analysis. The default configuration points to the development environment:

- **Default API URL**: `https://dev-farm-phonics.ai-poly.com/api/phonics`
- **Configuration**: Set via `.env` file or application settings panel

You can override the default settings in three ways:
1. **Environment variables**: Set `API_URL` and `API_KEY` in your environment
2. **Configuration file**: Edit the `.env` file 
3. **UI Settings**: Use the settings panel in the application (gear icon)

## Usage

1. Configure your API settings (optional - defaults to development environment)
2. Read the practice script displayed on screen
3. Choose your audio input method:
   - **Record Audio**: Click to record your pronunciation directly in the browser
   - **Upload File**: Upload a pre-recorded audio file (WAV, MP3, M4A, FLAC, OGG)
4. Click "Analyze Pronunciation" to get feedback
5. Review your comprehensive analysis:
   - Overall assessment and proficiency scores
   - Prosody analysis (intonation, sentence ending, pauses)
   - Word-by-word analysis with stress error detection
   - Phoneme-level error details with spelling highlights

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Audio Processing**: streamlit-webrtc
- **API Integration**: Phonics AI API
- **Visualization**: Plotly

## Project Structure

```
pronunciation-evaluator/
├── app.py                  # Main Streamlit application
├── config/                 # Configuration management
├── src/                    # Core application modules
├── utils/                  # Utility functions
├── assets/                 # Static assets
└── tests/                  # Test files
```

## Requirements

- Python 3.8+
- Modern web browser with microphone access
- Phonics API key (for accessing the pronunciation analysis service)
- Internet connection (for API communication)