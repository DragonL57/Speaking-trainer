# Pronunciation & Prosody Evaluation Tool - PRD

## 1. Project Overview

### 1.1 Purpose
Create a web-based application that allows students to practice pronunciation by reading predefined scripts aloud and receive comprehensive feedback on their speech quality, pronunciation accuracy, and prosody.

### 1.2 Target Users
- **Primary**: Students learning English pronunciation
- **Secondary**: Teachers and instructors monitoring student progress
- **Tertiary**: Educational institutions implementing pronunciation assessment

### 1.3 Core Value Proposition
Provide immediate, detailed feedback on pronunciation and prosody to help students improve their speaking skills through objective AI-powered assessment.

## 2. Technical Requirements

### 2.1 API Integration
- **Endpoint**: `https://farm2-phonics.ai-poly.com/api/phonics`
- **Authentication**: x-api-key header
- **Request Format**:
  ```json
  {
    "argument": {
      "language_code": "english",
      "user": "poly",
      "reference": "text to be read",
      "audio": "base64-encoded-audio"
    }
  }
  ```

### 2.2 Technology Stack Options
- **Option A**: Streamlit (Python-based, rapid prototyping)
- **Option B**: Flask/FastAPI + HTML/CSS/JS (More customizable)
- **Option C**: React + Node.js backend (Full-stack modern)

### 2.3 Core Technical Features
- Audio recording from browser microphone
- Audio playback functionality
- Base64 audio encoding
- HTTP requests to phonics API
- Real-time recording timer
- Responsive web design

## 3. Functional Requirements

### 3.1 User Interface Components

#### 3.1.1 Header Section
- Application title: "Pronunciation & Prosody Evaluator"
- Settings/configuration icon

#### 3.1.2 Configuration Panel (Collapsible)
- API URL input field (pre-populated)
- API key input field (password type)
- Reference text textarea (editable practice script)
- Save/update settings button

#### 3.1.3 Practice Script Display
- Large, readable text display of current script
- Clear typography for easy reading
- Optional: highlighting or emphasis of difficult words

#### 3.1.4 Recording Controls
- **Start Recording** button (microphone icon)
- **Stop Recording** button (square icon)
- **Play Recording** button (play icon)
- Recording timer display (MM:SS format)
- Recording status indicator (red dot when active)
- Audio player element for playback

#### 3.1.5 Analysis Section
- **Analyze Pronunciation** button
- Loading spinner during analysis
- Error handling and user feedback

### 3.2 Results Display Requirements

#### 3.2.1 Overall Assessment
- General comment display (excellent, good, needs improvement)
- Speech-to-text recognition result
- Reference score as percentage

#### 3.2.2 Proficiency Scores Dashboard
Display all scoring categories with:
- Score value and scale (e.g., 3.49/5.0)
- Visual progress bars
- Color-coded performance levels:
  - Green: 80-100% (Excellent)
  - Yellow: 60-79% (Good)
  - Red: <60% (Needs Improvement)

**Score Categories:**
1. Acoustic Score (0-100 scale)
2. Holistic Score (1-5 scale)
3. Segmental Accuracy (1-5 scale)
4. Chunking (1-5 scale)
5. Speed & Pause (1-5 scale)
6. Stress & Rhythm (1-5 scale)
7. Intonation (1-5 scale)

#### 3.2.3 Prosody Analysis
Four key indicators with status displays:
- **Intonation**: Monotonous vs. Varied
- **Sentence Ending**: Normal/Rising/Falling pattern
- **Speech Flow**: Fragmented vs. Fluent
- **Pauses**: Awkward vs. Natural

#### 3.2.4 Word-by-Word Analysis
Table/list showing:
- Word text
- Individual word score (as percentage)
- Phoneme count
- Status flags:
  - Unintelligible indicator
  - Equal stress warning
  - Stress error notifications

#### 3.2.5 Detailed Phoneme Analysis (Future Enhancement)
- Individual phoneme scores from `align_info`
- Error type identification
- IPA notation display
- Timing information

## 4. User Experience Requirements

### 4.1 Workflow
1. User sees practice script
2. User clicks "Start Recording"
3. User reads script aloud
4. User clicks "Stop Recording"
5. User reviews recording (optional playback)
6. User clicks "Analyze Pronunciation"
7. System displays comprehensive results
8. User can record again or try new script

### 4.2 Performance Requirements
- Recording should start within 1 second
- Analysis request should complete within 10 seconds
- Interface should be responsive on mobile and desktop
- Audio quality should be suitable for analysis

### 4.3 Error Handling
- Microphone permission denied
- Network connectivity issues
- API timeout or errors
- Invalid audio format
- Large file size warnings

## 5. Design Requirements

### 5.1 Visual Design
- Clean, educational interface
- Professional color scheme (blues, greens, grays)
- Clear typography and adequate spacing
- Accessible color contrast ratios
- Mobile-responsive layout

### 5.2 Information Hierarchy
1. Practice script (most prominent)
2. Recording controls (secondary)
3. Results display (detailed but organized)
4. Settings (least prominent, collapsible)

### 5.3 Feedback Design
- Immediate visual feedback for all actions
- Clear success/error states
- Progress indicators for long operations
- Intuitive icons and labels

## 6. Data Requirements

### 6.1 Input Data
- Audio recordings (WAV format preferred)
- Practice scripts (editable text)
- API configuration (URL, key)

### 6.2 Output Data
- JSON response from phonics API
- Processed scores and feedback
- No persistent storage required (session-based)

## 7. Security & Privacy

### 7.1 Audio Data
- Audio processed client-side before sending to API
- No local storage of audio files
- Clear user consent for microphone access

### 7.2 API Security
- API key stored securely (environment variables in production)
- HTTPS communication only
- No sensitive data logging

## 8. Testing Requirements

### 8.1 Functional Testing
- Microphone recording functionality
- Audio playback verification
- API integration testing
- Results display accuracy
- Error handling scenarios

### 8.2 Usability Testing
- Clear user instructions
- Intuitive interface navigation
- Mobile device compatibility
- Accessibility compliance

## 9. Success Metrics

### 9.1 Technical Metrics
- Recording success rate > 95%
- API response time < 10 seconds
- Error rate < 5%

### 9.2 User Experience Metrics
- User completes full workflow without assistance
- Clear understanding of feedback provided
- Improved pronunciation scores over time

## 10. Future Enhancements

### 10.1 Phase 2 Features
- Multiple language support
- Custom script upload
- Progress tracking over time
- Detailed phoneme-level feedback
- Export results functionality

### 10.2 Phase 3 Features
- Teacher dashboard
- Student progress analytics
- Curriculum integration
- Advanced prosody analysis
- Real-time feedback during recording

## 11. File Structure

```
pronunciation-evaluator/
├── README.md                 # Project documentation and setup instructions
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore file
├── app.py                  # Main Streamlit application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py         # Configuration management
│   └── constants.py        # Application constants
├── src/
│   ├── __init__.py
│   ├── api_client.py       # Phonics API integration
│   ├── audio_handler.py    # Audio recording and processing
│   ├── results_processor.py # API response processing
│   └── ui_components.py    # Reusable UI components
├── utils/
│   ├── __init__.py
│   ├── audio_utils.py      # Audio conversion and validation
│   ├── validators.py       # Input validation functions
│   └── helpers.py          # General utility functions
├── assets/
│   ├── styles.css          # Custom CSS styling
│   ├── default_scripts.txt # Default practice scripts
│   └── icons/              # Application icons
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py  # API integration tests
│   ├── test_audio_handler.py # Audio processing tests
│   └── test_ui_components.py # UI component tests
└── docs/
    ├── deployment.md       # Deployment instructions
    ├── api_documentation.md # API usage documentation
    └── user_guide.md       # End-user instructions
```

### 11.1 File Descriptions

#### Core Application Files

**`app.py`** (Main Entry Point)
```python
# Main Streamlit application
# - Page configuration
# - Session state management
# - Main UI layout
# - Component orchestration
```

**`requirements.txt`**
```txt
streamlit>=1.28.0
streamlit-audio-recorder>=0.0.8
requests>=2.31.0
pandas>=2.0.0
plotly>=5.17.0
python-dotenv>=1.0.0
base64
wave
io
```

#### Configuration Module (`config/`)

**`settings.py`**
```python
# Environment variable management
# API configuration
# Default values
# Settings validation
```

**`constants.py`**
```python
# API endpoints
# Score thresholds
# UI text constants
# Color schemes
```

#### Source Code Module (`src/`)

**`api_client.py`**
```python
class PronunciationAPI:
    def __init__(self, api_url, api_key)
    def encode_audio_to_base64(self, audio_data)
    def analyze_pronunciation(self, audio_data, reference_text)
    def handle_api_errors(self, response)
```

**`audio_handler.py`**
```python
class AudioRecorder:
    def record_audio()
    def stop_recording()
    def play_audio()
    def validate_audio_quality()
    def convert_to_wav()
```

**`results_processor.py`**
```python
class ResultsProcessor:
    def process_api_response(self, response_json)
    def calculate_score_percentages(self, scores)
    def extract_feedback_data(self, feedback)
    def format_prosody_analysis(self, sentence_detail)
```

**`ui_components.py`**
```python
def render_settings_panel()
def render_practice_script_display()
def render_recording_controls()
def render_proficiency_scores()
def render_prosody_analysis()
def render_word_analysis()
```

#### Utilities Module (`utils/`)

**`audio_utils.py`**
```python
def convert_to_base64(audio_file)
def validate_audio_format(audio_data)
def get_audio_duration(audio_data)
def compress_audio_if_needed(audio_data)
```

**`validators.py`**
```python
def validate_api_key(api_key)
def validate_script_text(text)
def validate_audio_file(file)
def sanitize_input(text)
```

#### Assets and Styling

**`.streamlit/config.toml`**
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
maxUploadSize = 10
```

**`assets/styles.css`**
```css
/* Custom styling for pronunciation feedback */
/* Score visualization colors */
/* Responsive design adjustments */
/* Accessibility improvements */
```

**`assets/default_scripts.txt`**
```txt
# Collection of practice scripts
# Organized by difficulty level
# Phoneme-rich examples
# Common pronunciation challenges
```

## 12. Implementation Approach

### 12.1 Development Phases

**Phase 1: Core Functionality (Week 1)**
- Set up project structure
- Implement basic audio recording
- Create API integration
- Build minimal results display

**Phase 2: Enhanced Features (Week 2)**
- Add comprehensive results visualization
- Implement error handling
- Create settings management
- Add audio playback functionality

**Phase 3: Polish & Deploy (Week 3)**
- Enhance UI/UX design
- Add comprehensive testing
- Optimize performance
- Deploy to Streamlit Cloud

### 12.2 Technology Decision
Recommend **Streamlit** for rapid prototyping and deployment:
- Quick development cycle
- Built-in audio components
- Easy API integration
- Automatic responsive design
- Simple deployment options

### 12.3 Claude Code Implementation Commands

**Initial Project Setup:**
```bash
claude-code "Create a Streamlit pronunciation evaluation app with this exact file structure. Start with app.py as the main entry point, create all the modules in src/, and set up the configuration management."
```

**Core Functionality:**
```bash
claude-code "Implement the PronunciationAPI class in src/api_client.py to integrate with the phonics API. Include base64 audio encoding and proper error handling."

claude-code "Create the AudioRecorder class in src/audio_handler.py using streamlit-audio-recorder for browser microphone access and audio processing."

claude-code "Build the ResultsProcessor class in src/results_processor.py to parse the API JSON response and extract all feedback and proficiency score data."
```

**UI Development:**
```bash
claude-code "Implement all UI components in src/ui_components.py following the PRD requirements: settings panel, recording controls, and comprehensive results display."

claude-code "Create the main app.py file that orchestrates all components and manages the user workflow from recording to results display."
```

**Testing and Polish:**
```bash
claude-code "Add comprehensive error handling, input validation, and user feedback throughout the application."

claude-code "Create custom CSS styling in assets/styles.css for professional appearance and mobile responsiveness."
```