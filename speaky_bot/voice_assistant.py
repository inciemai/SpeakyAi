import os
import tempfile
from typing import Optional, Dict, Any
import vosk
import numpy as np
import wget
import zipfile
from gtts import gTTS
from pydub import AudioSegment
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Check if running in server environment
IS_SERVER = os.getenv('RENDER', '').lower() == 'true'

# Download vosk model if needed
MODEL_PATH = "model"
if not os.path.exists(MODEL_PATH):
    print("Downloading vosk model...")
    wget.download("https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
    with zipfile.ZipFile("vosk-model-small-en-us-0.15.zip", 'r') as zip_ref:
        zip_ref.extractall(".")

SUPPORTED_LANGUAGES = {
    'English': 'en',
    'Malayalam': 'ml',
    'Hindi': 'hi',
    'Tamil': 'ta',
    'German': 'de'
}

class VoiceAssistant:
    def __init__(self, language: str = 'English'):
        self.language = language
        self.language_code = SUPPORTED_LANGUAGES.get(language, 'en')
        
        # Initialize vosk
        vosk.SetLogLevel(-1)  # Reduce logging
        self.model = vosk.Model(MODEL_PATH)
        self.rec = vosk.KaldiRecognizer(self.model, 16000)

        # Only import sounddevice if not running on server
        if not IS_SERVER:
            try:
                import sounddevice as sd
                self.sd = sd
            except OSError:
                print("Warning: Audio hardware not available")
                self.sd = None
        else:
            self.sd = None

    def transcribe_audio(self, audio_file: str) -> str:
        """Transcribe audio file to text using vosk."""
        try:
            # Load and convert audio file
            wf = AudioSegment.from_file(audio_file)
            wf = wf.set_frame_rate(16000)
            wf = wf.set_channels(1)
            audio_data = np.array(wf.get_array_of_samples())
            
            # Process audio data
            if self.rec.AcceptWaveform(audio_data.tobytes()):
                result = eval(self.rec.Result())
                return result.get('text', '')
            else:
                result = eval(self.rec.PartialResult())
                return result.get('partial', '')
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return "Could not transcribe audio"

    def text_to_speech(self, text: str, output_file: str) -> None:
        """Convert text to speech and save to file."""
        try:
            tts = gTTS(text=text, lang=self.language_code)
            tts.save(output_file)
        except Exception as e:
            print(f"Error in text to speech: {str(e)}")
            raise

    def process_with_ai(self, text: str) -> Dict[str, Any]:
        """Process text with Gemini AI and return response."""
        if not GEMINI_API_KEY:
            return {"error": "Gemini API key not configured"}

        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"""
            Act as an English language coach. The user said: "{text}"
            
            Provide feedback on:
            1. Grammar and vocabulary
            2. Natural ways to express the same idea
            3. Any cultural context if relevant
            
            Format your response in a helpful, encouraging way.
            """
            
            response = model.generate_content(prompt)
            return {"response": response.text}
        except Exception as e:
            print(f"Error in AI processing: {str(e)}")
            return {"error": str(e)}

    def process_audio(self, audio_file: str) -> Dict[str, Any]:
        """Process audio file and return AI response."""
        try:
            transcribed_text = self.transcribe_audio(audio_file)
            if transcribed_text:
                ai_response = self.process_with_ai(transcribed_text)
                return {
                    "transcribed_text": transcribed_text,
                    **ai_response
                }
            return {"error": "Could not transcribe audio"}
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            return {"error": str(e)}

# Create a test function to verify everything works
def test_voice_assistant():
    try:
        assistant = VoiceAssistant()
        test_text = "Hello, this is a test."
        
        # Test text-to-speech
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
            assistant.text_to_speech(test_text, temp_audio.name)
            assert os.path.exists(temp_audio.name), "Failed to create audio file"
            
            # Test transcription
            result = assistant.transcribe_audio(temp_audio.name)
            assert result, "Failed to transcribe audio"
            
            # Clean up
            os.unlink(temp_audio.name)
        
        print("Voice assistant test completed successfully!")
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_voice_assistant() 