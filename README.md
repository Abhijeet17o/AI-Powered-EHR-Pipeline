# EHR Pipeline System

A modular Electronic Health Record system that transcribes doctor-patient conversations using **Google Gemini (gemini-2.5-flash)** when available (falls back to Whisper AI locally if not) and extracts medical information using **Google Gemini AI**.

## 🏗️ Project Structure

```
v1/
├── core/                          # Core system components
│   ├── session_manager.py         # Manages patient consultation sessions
│   └── pipeline_manager.py        # Orchestrates the complete pipeline
│
├── modules/                       # Processing modules
│   ├── audio_recorder.py          # Audio recording from microphone
│   ├── transcription_engine.py    # Whisper AI transcription
│   └── ehr_autofill.py           # Gemini AI-powered EHR extraction
│
├── data/                          # All session data (auto-created)
│   └── sessions/                  # Individual patient sessions
│       └── {session_id}/          # Each session folder contains:
│           ├── session_metadata.json    # Session tracking info
│           ├── recording_*.wav          # Audio recording
│           ├── {patient_id}_*.json      # Transcript
│           └── ehr_{patient_id}.json    # EHR profile
│
├── run_pipeline.py                # Main entry point - run the pipeline
├── view_session.py                # View and manage sessions
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `google-generativeai` - AI transcription (Gemini 2.5 Flash) and extraction (Gemini)
- `openai-whisper` - (Optional) local transcription fallback when Gemini API key is not available
- `sounddevice` - Audio recording
- `soundfile` - Audio file handling
- `numpy` - Audio processing

### 2. Set up API Key

Get your free Gemini API key from: https://aistudio.google.com/app/apikey

Then set it as an environment variable:
```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

### 3. Run the Pipeline
```bash
python run_pipeline.py
```

This will guide you through:
1. Entering patient/doctor information
2. Recording or selecting audio file
3. Automatic transcription (using Gemini 2.5 Flash API if `GEMINI_API_KEY` is set; falls back to local Whisper if not available)
4. Automatic EHR profile extraction (using Gemini AI)

### 4. View Session Results
```bash
python view_session.py
```

## 📋 How It Works

### Session-Based Pipeline

Each patient consultation creates a **unique session** with:
- **Session ID**: `{patient_id}_{timestamp}` (e.g., `PAT001_20251115_143000`)
- **Dedicated folder**: All data for one consultation in one place
- **Tracking**: Each pipeline stage is tracked and logged

### Pipeline Stages

```
1. 🎤 RECORDING
   ├─ Record audio from microphone OR
   └─ Import existing audio file
   
2. 📝 TRANSCRIPTION (Gemini 2.5 Flash when available; local Whisper fallback)
   ├─ Load audio file
   ├─ Transcribe using OpenAI Whisper
   └─ Save transcript as JSON
   
3. 🏥 EHR AUTO-FILL (Gemini AI)
   ├─ Read transcript
   ├─ Use Google Gemini to intelligently extract:
   │  ├─ Symptoms
   │  ├─ Allergies
   │  └─ Lifestyle information
   └─ Save EHR profile
```

## 🎯 Key Features

### ✅ AI-Powered Intelligence
- **Whisper AI**: Accurate speech-to-text transcription
- **Gemini AI**: Intelligent medical data extraction (no rigid keywords!)
- Understands context and medical terminology

### ✅ Session Management
- Each consultation is a separate session
- Session ID tracks all related files
- Easy to find and review patient data
- No data mixing between patients

### ✅ Pipeline Tracking
- Each stage status: `pending` → `in_progress` → `completed`/`failed`
- View progress in real-time
- Session metadata tracks everything

### ✅ Organized Storage
- All session data in one folder
- Clear file naming convention
- Easy backup and archival

## 📖 Usage Examples

### Example: New Consultation with Recording

```bash
python run_pipeline.py
```

```
Enter Patient ID: PAT001
Enter Patient Name: John Doe
Enter Patient Age: 45
Enter Doctor ID: DOC123

Choose audio source:
  1. Use existing audio file
  2. Record new audio (30 seconds)
  3. Record new audio (custom duration)

Enter choice: 2

🎤 Recording for 30 seconds... Speak now!
```

Speak about symptoms, allergies, lifestyle → Whisper transcribes → Gemini extracts → EHR ready!

## 🔧 Configuration

### Whisper Model Selection (Optional local fallback)

If you don't have a Gemini API key, the system will fall back to local Whisper-based transcription. Edit `modules/transcription_engine.py` (line ~69) to change the Whisper model:

```python
model = whisper.load_model("base")  # Current local fallback

# Options:
# "tiny"   - Fastest, least accurate
# "base"   - Good balance (default)
# "small"  - Better accuracy
# "medium" - High accuracy, slower
# "large"  - Best accuracy, slowest
```

### Gemini Model Selection

Edit `modules/ehr_autofill.py` (line ~139):

```python
model = genai.GenerativeModel('gemini-2.5-flash')  # Current (fast & free)

# Options:
# 'gemini-2.5-flash'  - Fast, efficient (recommended)
# 'gemini-2.5-pro'    - More capable, slower
# 'gemini-pro'        - Standard model
```

## 🛠️ Troubleshooting

### "GEMINI_API_KEY environment variable not set"
```powershell
# Get API key from: https://aistudio.google.com/app/apikey
$env:GEMINI_API_KEY = "your_api_key_here"
```

### "No module named 'whisper'"
```bash
pip install openai-whisper
```

### "No module named 'google.generativeai'"
```bash
pip install google-generativeai
```

### FFmpeg not found
```bash
# Windows - using winget
winget install ffmpeg
```

## 📊 Future Modules (Roadmap)

- ✅ Module 1: Transcription Engine (Whisper AI)
- ✅ Module 2: EHR Profile Auto-Filler (Gemini AI)
- 🚧 Module 3: Medicine Database & Inventory (SQLite)
- 🚧 Module 4: Prescription Recommendation Engine (Gemini AI)
- 🚧 Module 5: Prescription Finalizer (Flask Web Interface)
- 🚧 Module 6: Patient Communication & Email

## 💡 Best Practices

1. **Use descriptive Patient IDs**: `PAT001`, `PAT002`, not random strings
2. **Keep recordings clear**: Quiet environment, good microphone
3. **30 seconds is usually enough**: For brief consultations
4. **Review transcripts**: Check Whisper accuracy before finalizing EHR
5. **Backup sessions folder**: Contains all patient data

---

**Version**: 2.0 (Gemini-Powered)  
**Last Updated**: November 15, 2025
