"""
Module 1: Transcription Engine
This module transcribes doctor-patient conversations using OpenAI's Whisper model
and saves the transcript to a structured JSON file.
"""

import base64
import contextlib
import io
import json
import os
import logging
from datetime import datetime

# Try to import Gemini client (google.generativeai); if not available we'll fall back to local Whisper
try:
    import google.generativeai as genai
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False

_USE_GEMINI = bool(os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')) and _HAS_GEMINI

# Attempt to import local Whisper for fallback (optional) regardless of Gemini availability
try:
    import whisper
except Exception:
    whisper = None

# Cache the loaded Whisper model so it is only loaded once per process
_whisper_model = None


def _get_whisper_model():
    """Return a cached Whisper 'base' model, loading it only on first call."""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model (first call)...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model


_AUDIO_MAGIC = [
    (b'\x1a\x45\xdf\xa3', 'audio/webm'),   # WebM / MKV
    (b'OggS',              'audio/ogg'),
    (b'RIFF',              'audio/wav'),    # WAV – checked further below
    (b'ID3',               'audio/mpeg'),  # MP3 with ID3 tag
    (b'\xff\xfb',          'audio/mpeg'),  # MP3 without tag
    (b'\xff\xf3',          'audio/mpeg'),
    (b'\xff\xf2',          'audio/mpeg'),
]


def _detect_audio_mime_type(file_path: str) -> str:
    """Detect audio MIME type from file header bytes."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
        for magic, mime in _AUDIO_MAGIC:
            if header[:len(magic)] == magic:
                # WAV: confirm WAVE marker at offset 8
                if mime == 'audio/wav' and header[8:12] != b'WAVE':
                    continue
                return mime
        # M4A / AAC container
        if header[4:8] == b'ftyp':
            return 'audio/mp4'
    except Exception:
        pass
    return 'audio/webm'  # safe default – browser MediaRecorder default


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def transcribe_conversation(audio_file_path, patient_id, doctor_id, output_dir=None):
    """
    Transcribes an audio conversation and saves it to a structured JSON file.
    
    Args:
        audio_file_path (str): Path to the audio file to transcribe
        patient_id (str): Unique identifier for the patient
        doctor_id (str): Unique identifier for the doctor
        output_dir (str, optional): Directory to save the JSON file. 
                                     Defaults to current working directory if not provided.
    
    Returns:
        str: File path of the created JSON file containing the transcript,
             or None if transcription fails
    
    Raises:
        ValueError: If input validation fails
        FileNotFoundError: If the audio file doesn't exist
        Exception: If transcription fails
    """
    
    try:
        # Input Validation
        if not audio_file_path or not isinstance(audio_file_path, str):
            error_msg = "audio_file_path must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(patient_id, str) or not patient_id:
            error_msg = "patient_id must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(doctor_id, str) or not doctor_id:
            error_msg = "doctor_id must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Verify audio file exists
        if not os.path.exists(audio_file_path):
            error_msg = f"Audio file not found: {audio_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Starting transcription for patient: {patient_id}")

        # If Gemini API key is present and client available, use Gemini for transcription
        if _USE_GEMINI:
            api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

            # Configure the genai library (preferred) and create a GenerativeModel
            try:
                genai.configure(api_key=api_key)
            except Exception as e:
                logger.debug(f"genai.configure not available or failed: {e}")

            logger.info("Using Gemini API for transcription (gemini-2.5-flash)")

            # Build a concise transcription prompt (multilingual-aware)
            prompt = (
                "Transcribe this audio accurately. "
                "If multiple speakers are present, indicate speaker turns as Speaker 1/2 if possible. "
                "Return only the transcript text."
            )

            # Upload the audio (best-effort) using genai helper.
            # Suppress genai's internal gRPC stdout noise during the upload.
            uploaded = None
            _stdout_buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(_stdout_buf):
                    try:
                        uploaded = genai.upload_file(audio_file_path)
                    except Exception:
                        uploaded = genai.upload_file(path=audio_file_path)
                logger.info("Uploaded audio to Gemini Files API")
            except Exception as e:
                logger.warning(f"Could not upload audio via genai.upload_file: {e}")
                uploaded = None

            # Create the model object using the installed genai API
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                logger.error(f"GenerativeModel API unavailable: {e}")
                model = None

            # Prepare contents: prompt + uploaded object.
            # When upload fails, skip the raw-bytes Gemini path entirely and
            # fall through to the reliable local Whisper fallback instead.
            if uploaded is None:
                logger.info("Gemini upload failed – using local Whisper directly")
                if whisper is None:
                    raise RuntimeError("Gemini upload failed and Whisper is not installed")
                result = _get_whisper_model().transcribe(audio_file_path)
            else:
                contents = [prompt, uploaded]

            # Build a GenerationConfig when available for deterministic transcription
            if uploaded is not None:
              gen_cfg = None
              try:
                  gen_cfg = genai.GenerationConfig(temperature=0.0, max_output_tokens=32768)
              except Exception:
                  try:
                      from google.generativeai import GenerationConfig
                      gen_cfg = GenerationConfig(temperature=0.0, max_output_tokens=32768)
                  except Exception:
                      gen_cfg = None

              # Call the model and robustly parse results
              try:
                if model is not None:
                    _stdout_buf2 = io.StringIO()
                    with contextlib.redirect_stdout(_stdout_buf2):
                        if gen_cfg is not None:
                            response = model.generate_content(contents=contents, generation_config=gen_cfg)
                        else:
                            response = model.generate_content(contents=contents)
                else:
                    # As a last resort, try older client-based API if present
                    try:
                        client = genai.Client(api_key=api_key)
                        _stdout_buf3 = io.StringIO()
                        with contextlib.redirect_stdout(_stdout_buf3):
                            if gen_cfg is not None:
                                response = client.models.generate_content(model='gemini-2.5-flash', contents=contents, generation_config=gen_cfg)
                            else:
                                response = client.models.generate_content(model='gemini-2.5-flash', contents=contents)
                    except Exception as e:
                        logger.error(f"No viable Gemini model call path: {e}")
                        raise

                # Extract transcript text from many possible response shapes
                transcript_text = None
                # simple attributes
                transcript_text = getattr(response, 'text', None) or getattr(response, 'output', None)
                # candidates list (common in some genai returns)
                if not transcript_text and hasattr(response, 'candidates'):
                    try:
                        transcript_text = response.candidates[0].content if response.candidates else None
                    except Exception:
                        transcript_text = None
                # nested dict forms
                if not transcript_text and isinstance(response, dict):
                    transcript_text = response.get('text') or response.get('output')
                    # some responses wrap candidates
                    if not transcript_text and 'candidates' in response:
                        try:
                            transcript_text = response['candidates'][0].get('content')
                        except Exception:
                            pass

                # Normalize to string
                transcript_text = (transcript_text or "").strip()

                if transcript_text:
                    logger.info("Gemini returned transcript text")
                    result = {"text": transcript_text}
                else:
                    logger.warning("Gemini returned no transcript text; falling back to Whisper")
                    raise RuntimeError("Empty transcript from Gemini")

              except Exception as e:
                logger.error(f"Gemini generate_content failed: {e}", exc_info=True)
                logger.info("Falling back to local Whisper transcription")
                if whisper is None:
                    raise
                try:
                    result = _get_whisper_model().transcribe(audio_file_path)
                except Exception as we:
                    logger.error(f"Whisper fallback also failed: {we}", exc_info=True)
                    raise

        else:
            if whisper is None:
                raise RuntimeError("Whisper is not installed and no Gemini API key found")

            logger.info(f"Transcribing audio with Whisper: {audio_file_path}")
            result = _get_whisper_model().transcribe(audio_file_path)
        
        # Get current timestamp in ISO 8601 format
        conversation_timestamp = datetime.now().isoformat()
        
        # Create the structured dictionary
        transcript_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "conversation_timestamp": conversation_timestamp,
            "transcript": result.get("text") if isinstance(result, dict) else (result["text"] if isinstance(result, dict) else result)
        }
        
        # Create filename with patient_id and timestamp (safe for filesystems)
        # Convert ISO timestamp to filesystem-safe format
        timestamp_safe = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        json_filename = f"{patient_id}_{timestamp_safe}.json"
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()  # Default to current working directory
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Full path for the JSON file
        json_filepath = os.path.join(output_dir, json_filename)
        
        # Save to JSON file
        with open(json_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(transcript_data, json_file, indent=4, ensure_ascii=False)
        
        logger.info(f"Transcript saved successfully to: {json_filepath}")
        
        return json_filepath
    
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        return None
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}", exc_info=True)
        return None


if __name__ == '__main__':
    # Example usage
    print("="*60)
    print("Module 1: Transcription Engine - Example Usage")
    print("="*60)
    
    # Dummy parameters for demonstration
    audio_file = "sample_conversation.mp3"  # Replace with actual audio file path
    patient_id = "PAT123"
    doctor_id = "DOC456"
    output_directory = "transcripts"  # Optional: specify output directory
    
    print(f"\nAttempting to transcribe:")
    print(f"  Audio File: {audio_file}")
    print(f"  Patient ID: {patient_id}")
    print(f"  Doctor ID: {doctor_id}")
    print(f"  Output Dir: {output_directory}")
    print()
    
    # Call the transcription function with optional output_dir
    json_file_path = transcribe_conversation(audio_file, patient_id, doctor_id, output_directory)
    
    if json_file_path:
        print(f"\n✓ Success! Transcript saved to: {json_file_path}")
        
        # Display the contents of the created JSON file
        print("\nJSON Contents:")
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
    else:
        print("\n✗ Transcription failed. Check the logs above for details.")
        print("\nTo test this module, please:")
        print("1. Place an audio file in the project directory")
        print("2. Update the 'audio_file' variable with the correct path")
        print("3. Run the script again")
