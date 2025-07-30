import os
import subprocess
import time
import wave
import tempfile
from typing import Optional, Dict, Any
import numpy as np
import speech_recognition as sr
from gtts import gTTS
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
import warnings
import asyncio
import concurrent.futures
from functools import partial

# Suppress pydub warnings about ffmpeg
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available - audio processing may be limited")

# Load environment variables
load_dotenv()

# Try to import pygame for local audio playback (optional for web deployment)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available - audio playback disabled (OK for web deployment)")

# Initialize pygame mixer only when needed
def init_pygame_mixer():
    global PYGAME_AVAILABLE
    if PYGAME_AVAILABLE:
        try:
            pygame.mixer.init()
            return True
        except pygame.error:
            PYGAME_AVAILABLE = False
            print("pygame mixer initialization failed - audio playback disabled")
            return False
    return False

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Set generation config for more controlled responses
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 200,
}

# Check if running in server environment
IS_SERVER = os.getenv('RENDER', '').lower() == 'true'

# Create a directory for temporary files in the current working directory
TEMP_DIR = os.path.join(os.getcwd(), 'temp_audio')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Clean up any existing temporary files on startup
def cleanup_existing_temp_files():
    """Clean up any existing temporary files that might be locked."""
    try:
        import glob
        for file_path in glob.glob(os.path.join(TEMP_DIR, '*')):
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    # File might be locked, ignore for now
                    pass
    except Exception as e:
        print(f"Warning: Could not clean up existing temp files: {e}")

# Run cleanup on startup
cleanup_existing_temp_files()

# Supported languages with their codes and native exit commands
SUPPORTED_LANGUAGES = {
    'English': {
        'code': 'en-US',
        'tts_code': 'en',
        'exit_command': 'goodbye',
        'change_language_command': 'change language',
        'native_name': 'English'
    },
    'Malayalam': {
        'code': 'ml-IN',
        'tts_code': 'ml',
        'exit_command': 'വിട',
        'change_language_command': 'ഭാഷ മാറ്റുക',
        'native_name': 'മലയാളം'
    },
    'Hindi': {
        'code': 'hi-IN',
        'tts_code': 'hi',
        'exit_command': 'अलविदा',
        'change_language_command': 'भाषा बदलें',
        'native_name': 'हिंदी'
    },
    'Tamil': {
        'code': 'ta-IN',
        'tts_code': 'ta',
        'exit_command': 'விடைபெறுகிறேன்',
        'change_language_command': 'மொழியை மாற்றவும்',
        'native_name': 'தமிழ்'
    },
    'German': {
        'code': 'de-DE',
        'tts_code': 'de',
        'exit_command': 'auf wiedersehen',
        'change_language_command': 'sprache ändern',
        'native_name': 'Deutsch'
    }
}

class VoiceAssistant:
    def __init__(self, language: str = 'English'):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Set language settings
        self.current_language = language
        self.language_code = SUPPORTED_LANGUAGES.get(language, 'en')
        
        # Initialize conversation history for context-aware analysis
        self.conversation_history = []
        self.user_patterns = {}
        self.grammar_analysis_cache = {}
        
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
        
        # Configure Gemini AI
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not found in environment variables")
        else:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                print("Debug: Successfully configured Gemini AI")
            except Exception as e:
                print(f"Error configuring Gemini AI: {e}")
                self.model = None

        # Initialize thread pool for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
    def correct_grammar(self, text):
        """Enhanced grammar correction with multi-stage analysis and confidence scoring."""
        try:
            # Skip processing for very short inputs or non-alphabetic content
            if len(text.strip()) < 3 or not any(c.isalpha() for c in text):
                return text, False, {
                    'corrected_text': text,
                    'grammar_feedback': '',
                    'speaking_tips': '',
                    'communication_advice': '',
                    'had_errors': False,
                    'confidence_score': 1.0,
                    'error_categories': [],
                    'suggestions_count': 0,
                    'alternative_expressions': []
                }

            # Check if we have conversation history for context-aware analysis
            if len(self.conversation_history) >= 2:
                # Use context-aware analysis for better accuracy
                analysis_result = self.get_context_aware_grammar_analysis(text)
            else:
                # Use standard multi-stage analysis for new conversations
                # Stage 1: Initial grammar analysis
                initial_analysis = self._perform_initial_grammar_analysis(text)
                
                # Stage 2: Detailed correction if needed
                if initial_analysis['had_errors']:
                    analysis_result = self._perform_detailed_correction(text, initial_analysis)
                else:
                    analysis_result = initial_analysis

            # Add to conversation history for future context-aware analysis
            self.add_to_conversation_history(text, analysis_result)
            
            return text, analysis_result['had_errors'], analysis_result
            
        except Exception as e:
            print(f"Error in grammar correction: {e}")
            return text, False, {
                'corrected_text': text,
                'grammar_feedback': '',
                'speaking_tips': '',
                'communication_advice': '',
                'had_errors': False,
                'confidence_score': 0.5,
                'error_categories': [],
                'suggestions_count': 0,
                'alternative_expressions': []
            }

    def _perform_initial_grammar_analysis(self, text):
        """Perform initial grammar analysis focused on meaning-changing errors."""
        try:
            # For voice input, we focus only on major errors that affect meaning
            analysis_result = {
                'had_errors': False,
                'corrected_text': text,
                'grammar_feedback': '',
                'speaking_tips': '',
                'communication_advice': '',
                'confidence_score': 1.0,
                'error_categories': [],
                'suggestions_count': 0,
                'alternative_expressions': []
            }
            
            # Split into words and analyze
            words = text.lower().split()
            
            # Check for missing essential words (articles, verbs, etc.)
            if len(words) >= 2:  # Only check if we have at least 2 words
                # Check for missing "is/are/am" in questions
                if words[0] in ['who', 'what', 'where', 'when', 'why', 'how']:
                    if not any(word in words[1:] for word in ['is', 'are', 'am', 'was', 'were']):
                        analysis_result['had_errors'] = True
                        analysis_result['error_categories'].append('missing_words')
                
                # Check for wrong word order in questions
                if words[0] in ['is', 'are', 'am'] and any(word in words[1:] for word in ['who', 'what', 'where', 'when', 'why', 'how']):
                    analysis_result['had_errors'] = True
                    analysis_result['error_categories'].append('word_order')
            
            # Ignore punctuation and capitalization errors
            # Only focus on errors that affect meaning
            
            return analysis_result
            
        except Exception as e:
            print(f"Error in initial grammar analysis: {e}")
            return {
                'had_errors': False,
                'corrected_text': text,
                'grammar_feedback': '',
                'speaking_tips': '',
                'communication_advice': '',
                'confidence_score': 1.0,
                'error_categories': [],
                'suggestions_count': 0,
                'alternative_expressions': []
            }

    def _perform_detailed_correction(self, text, initial_analysis):
        """Perform detailed correction with context and alternatives."""
        try:
            language_name = SUPPORTED_LANGUAGES[self.current_language]['native_name']
            
            prompt = f"""You are an expert {self.current_language} communication development coach. Your mission is to help speakers grow their confidence and fluency while providing supportive corrections.

Language: {self.current_language} ({language_name})
Speaker's input: "{text}"
Initial analysis: {initial_analysis}

COACHING PHILOSOPHY:
- Celebrate the speaker's effort and courage to communicate
- Provide corrections as growth opportunities, not failures
- Encourage expansion of thoughts and ideas
- Build confidence through positive reinforcement
- Focus on effective communication over grammatical perfection

Provide comprehensive, encouraging feedback in this format:
CORRECTED_TEXT: [supportive correction that honors the speaker's intent]
GRAMMAR_FEEDBACK: [positive grammar guidance with encouragement - start with "Great job expressing your thoughts! Here's how to make it even clearer..."]
SPEAKING_TIPS: [confidence-building pronunciation and delivery advice]
COMMUNICATION_ADVICE: [encouraging suggestions for natural expression + conversation expansion prompts]
CONFIDENCE_SCORE: [0.0-1.0 confidence in corrections]
ERROR_CATEGORIES: [categorization focusing on learning opportunities]
SUGGESTIONS_COUNT: [number of improvement suggestions]
ALTERNATIVE_EXPRESSIONS: [2-3 natural ways to express the same idea, with encouragement to try them]
CONVERSATION_PROMPTS: [Questions or prompts to encourage the speaker to continue and elaborate]

ENHANCEMENT FOCUS:
- Acknowledge what the speaker did well
- Provide gentle corrections with explanations
- Include encouraging phrases like "You're doing great!", "Keep it up!", "That's a good start!"
- Suggest ways to expand on their thoughts
- Ask follow-up questions to encourage more speaking
- Provide cultural context to make communication more natural
- Celebrate progress and effort over perfection
"""

            response = self.model.generate_content(prompt) # Use self.model
            response_text = response.text.strip()
            
            detailed_result = self._parse_grammar_response(response_text, text)
            
            # Merge with initial analysis for comprehensive feedback
            detailed_result['confidence_score'] = max(
                detailed_result.get('confidence_score', 0.5),
                initial_analysis.get('confidence_score', 0.5)
            )
            
            return detailed_result
            
        except Exception as e:
            print(f"Error in detailed correction: {e}")
            return initial_analysis

    def _parse_grammar_response(self, response_text, original_text):
        """Parse the grammar analysis response."""
        result = {
            'corrected_text': original_text,
            'grammar_feedback': '',
            'speaking_tips': '',
            'communication_advice': '',
            'had_errors': False,
            'confidence_score': 0.5,
            'error_categories': [],
            'suggestions_count': 0,
            'alternative_expressions': [],
            'conversation_prompts': [],
            'progress_acknowledgment': ''
        }
        
        try:
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('HAS_ERRORS:'):
                    has_errors = line.replace('HAS_ERRORS:', '').strip().lower()
                    result['had_errors'] = has_errors == 'true'
                elif line.startswith('CONFIDENCE:'):
                    confidence = line.replace('CONFIDENCE:', '').strip()
                    try:
                        result['confidence_score'] = float(confidence)
                    except ValueError:
                        result['confidence_score'] = 0.5
                elif line.startswith('ERROR_CATEGORIES:'):
                    categories = line.replace('ERROR_CATEGORIES:', '').strip()
                    result['error_categories'] = [cat.strip() for cat in categories.split(',') if cat.strip()]
                elif line.startswith('CORRECTED_TEXT:'):
                    corrected = line.replace('CORRECTED_TEXT:', '').strip()
                    if corrected and corrected != original_text:
                        result['corrected_text'] = corrected
                elif line.startswith('GRAMMAR_FEEDBACK:'):
                    result['grammar_feedback'] = line.replace('GRAMMAR_FEEDBACK:', '').strip()
                elif line.startswith('SPEAKING_TIPS:'):
                    result['speaking_tips'] = line.replace('SPEAKING_TIPS:', '').strip()
                elif line.startswith('COMMUNICATION_ADVICE:'):
                    result['communication_advice'] = line.replace('COMMUNICATION_ADVICE:', '').strip()
                elif line.startswith('SUGGESTIONS_COUNT:'):
                    count = line.replace('SUGGESTIONS_COUNT:', '').strip()
                    try:
                        result['suggestions_count'] = int(count)
                    except ValueError:
                        result['suggestions_count'] = 0
                elif line.startswith('ALTERNATIVE_EXPRESSIONS:'):
                    alternatives = line.replace('ALTERNATIVE_EXPRESSIONS:', '').strip()
                    result['alternative_expressions'] = [alt.strip() for alt in alternatives.split(';') if alt.strip()]
                elif line.startswith('CONVERSATION_PROMPTS:'):
                    prompts = line.replace('CONVERSATION_PROMPTS:', '').strip()
                    result['conversation_prompts'] = [prompt.strip() for prompt in prompts.split(';') if prompt.strip()]
                elif line.startswith('PROGRESS_ACKNOWLEDGMENT:'):
                    result['progress_acknowledgment'] = line.replace('PROGRESS_ACKNOWLEDGMENT:', '').strip()
            
            # Calculate suggestions count if not provided
            if result['suggestions_count'] == 0:
                suggestions = 0
                if result['grammar_feedback']:
                    suggestions += 1
                if result['speaking_tips']:
                    suggestions += 1
                if result['communication_advice']:
                    suggestions += 1
                if result['conversation_prompts']:
                    suggestions += len(result['conversation_prompts'])
                result['suggestions_count'] = suggestions
                
        except Exception as e:
            print(f"Error parsing grammar response: {e}")
            
        return result

    def _create_fallback_response(self, text):
        """Create a fallback response when analysis fails."""
        return {
            'corrected_text': text,
            'grammar_feedback': '',
            'speaking_tips': '',
            'communication_advice': '',
            'had_errors': False,
            'confidence_score': 0.3,
            'error_categories': [],
            'suggestions_count': 0,
            'alternative_expressions': [],
            'conversation_prompts': ['Tell me more about that!', 'What else would you like to share?'],
            'progress_acknowledgment': 'Keep practicing - every conversation helps you improve!'
        }

    def _get_language_specific_grammar_rules(self):
        """Get language-specific grammar rules for enhanced analysis."""
        rules = {
            'English': {
                'common_errors': [
                    'article_usage', 'verb_tense', 'subject_verb_agreement',
                    'preposition_usage', 'word_order', 'pronunciation_patterns'
                ],
                'focus_areas': [
                    'natural spoken expressions', 'informal vs formal speech',
                    'common speaking patterns', 'cultural context'
                ]
            },
            'Malayalam': {
                'common_errors': [
                    'verb_conjugation', 'case_markers', 'word_order',
                    'pronunciation', 'formal_informal_distinction'
                ],
                'focus_areas': [
                    'respectful speech patterns', 'regional variations',
                    'cultural expressions', 'natural flow'
                ]
            },
            'Hindi': {
                'common_errors': [
                    'verb_forms', 'gender_agreement', 'postpositions',
                    'pronunciation', 'formal_informal_speech'
                ],
                'focus_areas': [
                    'respectful language use', 'regional dialects',
                    'cultural context', 'natural expressions'
                ]
            },
            'Tamil': {
                'common_errors': [
                    'verb_forms', 'case_endings', 'word_order',
                    'pronunciation', 'formal_informal_distinction'
                ],
                'focus_areas': [
                    'respectful speech', 'regional variations',
                    'cultural expressions', 'natural flow'
                ]
            },
            'German': {
                'common_errors': [
                    'case_system', 'verb_conjugation', 'word_order',
                    'gender_agreement', 'pronunciation'
                ],
                'focus_areas': [
                    'formal vs informal speech', 'regional dialects',
                    'cultural context', 'natural expressions'
                ]
            }
        }
        
        return rules.get(self.current_language, rules['English'])

    async def get_ai_response(self, user_input, grammar_correction_info=None):
        """Get AI response using Gemini with encouraging, conversation-extending approach."""
        try:
            if not GEMINI_API_KEY or not self.model:
                return self._handle_api_error()

            print("Debug: Gemini API key is configured and model is initialized")
            print(f"Debug: Using language {self.current_language}")
            
            # First, perform grammar correction if not already done
            if not grammar_correction_info:
                _, _, grammar_correction_info = self.correct_grammar(user_input)
            
            # Create the prompt with grammar correction context
            prompt = self._create_prompt(user_input, grammar_correction_info)
            print("Debug: Generated base prompt")
            
            # Make API calls asynchronously with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Debug: Attempting API call (attempt {attempt + 1}/{max_retries})")
                    
                    # Run the API call in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        self.executor,
                        partial(
                            self.model.generate_content,
                            prompt,
                            generation_config=generation_config,
                            safety_settings=[
                                {
                                    "category": "HARM_CATEGORY_HARASSMENT",
                                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                                }
                            ]
                        )
                    )
                    
                    print("Debug: API call completed")
                    
                    if response and response.text:
                        ai_response = response.text.strip()
                        print("Debug: Got valid response from API")
                        
                        # Update conversation history
                        self.conversation_history.append({
                            'text': user_input,
                            'response': ai_response,
                            'grammar_info': grammar_correction_info,
                            'timestamp': time.time()
                        })
                        
                        return ai_response
                    else:
                        print(f"Debug: Empty response from Gemini API on attempt {attempt + 1}")
                        continue
                        
                except Exception as api_error:
                    print(f"Debug: Gemini API error on attempt {attempt + 1}: {str(api_error)}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)  # Wait before retry
            
            raise Exception("Failed to get response after maximum retries")
            
        except Exception as e:
            print(f"Debug: Error in get_ai_response: {str(e)}")
            return self._handle_api_error(str(e))

    def speak(self, text):
        """Convert text to speech and play it (requires pygame for local playback)."""
        if not PYGAME_AVAILABLE or not init_pygame_mixer():
            print("Audio playback not available - pygame not installed or audio device not available")
            print("For web deployment, use speak_to_file() instead")
            return
            
        temp_filename = None
        try:
            # Get the TTS language code
            tts_code = SUPPORTED_LANGUAGES[self.current_language]['tts_code']
            
            # Create TTS object
            tts = gTTS(text=text, lang=tts_code, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
        finally:
            # Clean up temporary file in finally block
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except OSError as e:
                    print(f"Warning: Could not remove temporary speech file {temp_filename}: {e}")
                    # If we can't remove it now, try to remove it later
                    import threading
                    def delayed_cleanup():
                        import time
                        time.sleep(1)  # Wait a bit
                        try:
                            if os.path.exists(temp_filename):
                                os.unlink(temp_filename)
                        except:
                            pass  # Ignore cleanup errors
                    threading.Thread(target=delayed_cleanup, daemon=True).start()

    def process_text_input(self, text):
        """Process text input and return response with grammar correction."""
        try:
            # Process the input with grammar correction
            corrected_text, had_errors, grammar_info = self.correct_grammar(text)
            
            # Get AI response
            ai_response = self.get_ai_response(text, grammar_info)
            
            return {
                'response': ai_response,
                'grammar_correction': grammar_info
            }
        except Exception as e:
            return {
                'response': f"Error processing input: {str(e)}",
                'grammar_correction': None
            }

    async def process_audio_file(self, audio_file_path):
        """Process an audio file and return transcribed text with grammar correction."""
        temp_wav_path = None
        try:
            # Run speech recognition in thread pool
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                self.executor,
                self._recognize_speech,
                audio_file_path
            )
            
            if not text:
                return None, None
                
            # Process with grammar correction
            corrected_text, had_errors, grammar_info = await loop.run_in_executor(
                self.executor,
                self.correct_grammar,
                text
            )
            
            print(f"Debug: Grammar correction result - had_errors: {had_errors}")
            print(f"Debug: Grammar info: {grammar_info}")
            
            return text, grammar_info
                
        except Exception as e:
            print(f"Error processing audio file: {e}")
            return None, None
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except OSError as e:
                    print(f"Warning: Could not remove temporary file {temp_wav_path}: {e}")

    # def speak_to_file(self, text, output_path):
    #     """Convert text to speech and save to file with 1.5x speed."""
    #     try:
    #         # Get the TTS language code
    #         tts_code = SUPPORTED_LANGUAGES[self.current_language]['tts_code']
            
    #         # Create TTS object
    #         tts = gTTS(text=text, lang=tts_code, slow=False)
            
    #         # Save to a temporary file first
    #         import tempfile
    #         with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
    #             temp_filename = temp_file.name
    #             tts.save(temp_filename)
            
    #         try:
    #             # Load the audio with pydub
    #             from pydub import AudioSegment
    #             audio = AudioSegment.from_mp3(temp_filename)
                
    #             # Speed up the audio by 2x
    #             # This method maintains pitch while increasing speed
    #             samples = audio.get_array_of_samples()
                
    #             # Create a new audio segment with increased speed by taking every other sample
    #             audio_faster = audio._spawn(samples[::2])  # Take every second sample to double speed
                
    #             # Adjust frame rate to maintain pitch at 2x speed
    #             audio_faster = audio_faster.set_frame_rate(int(audio.frame_rate *0.1))
                
    #             # Export the processed audio with a higher bitrate for better quality
    #             audio_faster.export(output_path, format="mp3", bitrate="192k")
                
    #             return True
    #         finally:
    #             # Clean up the temporary file
    #             try:
    #                 os.remove(temp_filename)
    #             except:
    #                 pass  # Ignore cleanup errors
                
    #     except Exception as e:
    #         print(f"Error saving speech to file: {e}")
    #         return False
    # def speak_to_file(self, text, output_path):
    #     """Convert text to speech and save to file."""
    #     try:
    #         # Get the TTS language code
    #         tts_code = SUPPORTED_LANGUAGES[self.current_language]['tts_code']
            
    #         # Create TTS object
    #         tts = gTTS(text=text, lang=tts_code, slow=True)
            
    #         # Save to the specified path
    #         tts.save(output_path)
            
    #         return True
    #     except Exception as e:
    #         print(f"Error saving speech to file: {e}")
    #         return False
    def speak_to_file(self, text, output_path):
        """Convert text to speech, optimize for speed while maintaining quality."""
        try:
            # Get the TTS language code
            tts_code = SUPPORTED_LANGUAGES[self.current_language]['tts_code']

            # Create temporary file for original TTS audio
            temp_path = output_path.replace(".mp3", "_temp.mp3")
            
            # Generate speech with gTTS (faster mode)
            tts = gTTS(text=text, lang=tts_code, slow=False)
            tts.save(temp_path)

            # Use ffmpeg with optimized settings for faster processing
            command = [
                "ffmpeg",
                "-i", temp_path,
                "-filter:a", "atempo=1.3",  # Speed up audio
                "-codec:a", "libmp3lame",   # Use MP3 codec
                "-qscale:a", "4",           # Higher quality (0-9, lower is better)
                "-ar", "24000",             # Sample rate
                "-ac", "1",                 # Mono audio
                "-b:a", "32k",             # Bitrate
                output_path,
                "-y",                      # Overwrite if exists
                "-loglevel", "error"       # Reduce logging
            ]
            subprocess.run(command, check=True, capture_output=True)

            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors

            return True
        except Exception as e:
            print(f"Error saving speech to file: {e}")
            return False


    def add_to_conversation_history(self, text, grammar_info=None):
        """Add user input to conversation history for context-aware analysis."""
        entry = {
            'text': text,
            'timestamp': time.time(),
            'language': self.current_language,
            'grammar_info': grammar_info
        }
        self.conversation_history.append(entry)
        
        # Keep only last 10 entries to manage memory
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
        
        # Update user patterns
        self._update_user_patterns(text, grammar_info)

    def _update_user_patterns(self, text, grammar_info):
        """Update user's common grammar patterns and errors."""
        if not grammar_info or not grammar_info.get('had_errors'):
            return
            
        error_categories = grammar_info.get('error_categories', [])
        for category in error_categories:
            if category not in self.user_patterns:
                self.user_patterns[category] = {'count': 0, 'examples': []}
            
            self.user_patterns[category]['count'] += 1
            if len(self.user_patterns[category]['examples']) < 3:
                self.user_patterns[category]['examples'].append(text)

    def get_context_aware_grammar_analysis(self, text):
        """Perform context-aware grammar analysis using conversation history."""
        try:
            # Get recent context
            recent_context = self._get_recent_context()
            common_errors = self._get_user_common_errors()
            progress_insights = self._get_progress_insights()
            
            language_name = SUPPORTED_LANGUAGES[self.current_language]['native_name']
            
            prompt = f"""You are an expert {self.current_language} communication development coach with access to the speaker's learning journey. Your role is to provide personalized, encouraging feedback that motivates continued practice and builds confidence.

Language: {self.current_language} ({language_name})
Current input: "{text}"

SPEAKER'S LEARNING CONTEXT:
Recent conversation history:
{recent_context}

Learning patterns observed:
{common_errors}

Progress insights:
{progress_insights}

PERSONALIZED COACHING APPROACH:
- Acknowledge the speaker's progress and effort throughout the conversation
- Provide corrections tailored to their specific learning patterns
- Encourage them to build on previous topics or explore new areas
- Celebrate improvements from earlier in the conversation
- Motivate continued practice with specific, achievable goals

Provide personalized, encouraging feedback in this format:
HAS_ERRORS: [true/false]
CONFIDENCE: [0.0-1.0]
ERROR_CATEGORIES: [comma-separated list focusing on learning opportunities]
CORRECTED_TEXT: [supportive correction maintaining the speaker's communication intent]
GRAMMAR_FEEDBACK: [personalized grammar guidance with progress acknowledgment]
SPEAKING_TIPS: [tailored pronunciation tips based on their patterns]
COMMUNICATION_ADVICE: [context-appropriate suggestions + conversation expansion ideas]
SUGGESTIONS_COUNT: [number of improvement suggestions]
ALTERNATIVE_EXPRESSIONS: [context-appropriate alternatives with encouragement]
CONVERSATION_PROMPTS: [Specific questions to encourage elaboration on this topic or related topics]
PROGRESS_ACKNOWLEDGMENT: [Recognition of improvements from earlier in the conversation]

FOCUS AREAS:
- Build on the conversation flow naturally
- Address recurring patterns with encouragement
- Provide specific prompts to encourage more detailed responses
- Celebrate any improvements from previous interactions
- Suggest interesting follow-up topics or questions
- Make the speaker feel comfortable expressing longer, more complex thoughts
"""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            return self._parse_grammar_response(response_text, text)
            
        except Exception as e:
            print(f"Error in context-aware grammar analysis: {e}")
            return self._create_fallback_response(text)

    def _get_recent_context(self):
        """Get recent conversation context for analysis."""
        if not self.conversation_history:
            return "No recent conversation context available."
        
        recent_entries = self.conversation_history[-3:]  # Last 3 entries
        context_lines = []
        
        for entry in recent_entries:
            context_lines.append(f"- User: {entry['text']}")
            if entry.get('grammar_info') and entry['grammar_info'].get('had_errors'):
                context_lines.append(f"  (Had grammar issues: {', '.join(entry['grammar_info'].get('error_categories', []))})")
        
        return "\n".join(context_lines)

    def _get_user_common_errors(self):
        """Get user's common error patterns for personalized feedback."""
        if not self.user_patterns:
            return "No recurring error patterns identified yet."
        
        error_summary = []
        for category, data in self.user_patterns.items():
            if data['count'] >= 2:  # Only show patterns that occur at least twice
                error_summary.append(f"- {category}: {data['count']} times")
                if data['examples']:
                    error_summary.append(f"  Examples: {', '.join(data['examples'][:2])}")
        
        return "\n".join(error_summary) if error_summary else "No recurring error patterns identified yet."

    def _get_progress_insights(self):
        """Get insights about the user's progress in the current session."""
        if len(self.conversation_history) < 2:
            return "New conversation - encouraging first steps in communication practice."
        
        insights = []
        recent_entries = self.conversation_history[-3:]
        
        # Check for improvement patterns
        error_trend = []
        for entry in recent_entries:
            if entry.get('grammar_info', {}).get('had_errors'):
                error_trend.append(True)
            else:
                error_trend.append(False)
        
        if not any(error_trend):
            insights.append("Excellent - maintaining good communication accuracy!")
        elif error_trend[-1] == False and any(error_trend[:-1]):
            insights.append("Great improvement - last response showed better accuracy!")
        
        # Check conversation length progression
        text_lengths = [len(entry['text'].split()) for entry in recent_entries]
        if len(text_lengths) >= 2 and text_lengths[-1] > text_lengths[-2]:
            insights.append("Positive - expressing thoughts in more detail!")
        
        # Check confidence progression
        confidence_scores = [entry.get('grammar_info', {}).get('confidence_score', 0.5) 
                           for entry in recent_entries if entry.get('grammar_info')]
        if len(confidence_scores) >= 2 and confidence_scores[-1] > confidence_scores[-2]:
            insights.append("Building confidence - communication quality is improving!")
        
        return " ".join(insights) if insights else "Continuing to practice - keep up the communication efforts!"

    def get_grammar_analysis_statistics(self):
        """Get statistics about user's grammar analysis and learning progress."""
        if not self.conversation_history:
            return {
                'total_analyses': 0,
                'error_rate': 0.0,
                'most_common_errors': [],
                'improvement_trend': 'insufficient_data',
                'confidence_average': 0.0,
                'suggestions_given': 0
            }
        
        total_analyses = len(self.conversation_history)
        error_count = sum(1 for entry in self.conversation_history 
                         if entry.get('grammar_info', {}).get('had_errors', False))
        error_rate = (error_count / total_analyses) * 100 if total_analyses > 0 else 0
        
        # Calculate confidence average
        confidence_scores = [entry.get('grammar_info', {}).get('confidence_score', 0.5) 
                           for entry in self.conversation_history]
        confidence_average = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Count total suggestions given
        suggestions_count = sum(entry.get('grammar_info', {}).get('suggestions_count', 0) 
                              for entry in self.conversation_history)
        
        # Get most common errors
        error_counts = {}
        for entry in self.conversation_history:
            if entry.get('grammar_info', {}).get('had_errors'):
                categories = entry.get('grammar_info', {}).get('error_categories', [])
                for category in categories:
                    error_counts[category] = error_counts.get(category, 0) + 1
        
        most_common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Determine improvement trend (simplified)
        recent_entries = self.conversation_history[-5:] if len(self.conversation_history) >= 5 else self.conversation_history
        recent_error_rate = sum(1 for entry in recent_entries 
                              if entry.get('grammar_info', {}).get('had_errors', False)) / len(recent_entries) * 100
        
        if len(self.conversation_history) < 5:
            improvement_trend = 'insufficient_data'
        elif recent_error_rate < error_rate * 0.8:
            improvement_trend = 'improving'
        elif recent_error_rate > error_rate * 1.2:
            improvement_trend = 'needs_attention'
        else:
            improvement_trend = 'stable'
        
        return {
            'total_analyses': total_analyses,
            'error_rate': round(error_rate, 1),
            'most_common_errors': most_common_errors,
            'improvement_trend': improvement_trend,
            'confidence_average': round(confidence_average, 2),
            'suggestions_given': suggestions_count
        }

    def get_personalized_learning_recommendations(self):
        """Get personalized learning recommendations based on user's grammar patterns."""
        stats = self.get_grammar_analysis_statistics()
        
        if stats['total_analyses'] < 3:
            return {
                'recommendations': ['Continue practicing to get more personalized recommendations'],
                'focus_areas': [],
                'practice_exercises': [],
                'difficulty_level': 'beginner'
            }
        
        recommendations = []
        focus_areas = []
        practice_exercises = []
        
        # Analyze error patterns for recommendations
        if stats['error_rate'] > 50:
            recommendations.append('Consider focusing on basic grammar structures')
            focus_areas.append('basic_grammar')
            practice_exercises.append('sentence_structure_practice')
        
        # Check specific error categories
        for error_category, count in stats['most_common_errors'][:3]:
            if 'verb' in error_category.lower():
                recommendations.append('Practice verb conjugation and tense usage')
                focus_areas.append('verb_usage')
                practice_exercises.append('verb_conjugation_drills')
            elif 'article' in error_category.lower():
                recommendations.append('Work on article usage (a, an, the)')
                focus_areas.append('article_usage')
                practice_exercises.append('article_practice')
            elif 'preposition' in error_category.lower():
                recommendations.append('Focus on preposition usage')
                focus_areas.append('preposition_usage')
                practice_exercises.append('preposition_exercises')
            elif 'pronunciation' in error_category.lower():
                recommendations.append('Practice pronunciation patterns')
                focus_areas.append('pronunciation')
                practice_exercises.append('pronunciation_drills')
        
        # Determine difficulty level
        if stats['error_rate'] > 70:
            difficulty_level = 'beginner'
        elif stats['error_rate'] > 40:
            difficulty_level = 'intermediate'
        else:
            difficulty_level = 'advanced'
        
        # Add general recommendations
        if stats['confidence_average'] < 0.6:
            recommendations.append('Build confidence through regular practice')
        
        if stats['improvement_trend'] == 'needs_attention':
            recommendations.append('Consider reviewing fundamental concepts')
        
        return {
            'recommendations': recommendations[:5],  # Limit to 5 recommendations
            'focus_areas': list(set(focus_areas)),  # Remove duplicates
            'practice_exercises': list(set(practice_exercises)),
            'difficulty_level': difficulty_level
        }

    def clear_conversation_history(self):
        """Clear conversation history and user patterns."""
        self.conversation_history = []
        self.user_patterns = {}
        self.grammar_analysis_cache = {}

    def get_encouraging_session_summary(self):
        """Generate an encouraging session summary to motivate continued practice."""
        stats = self.get_grammar_analysis_statistics()
        
        if stats['total_analyses'] == 0:
            return {
                'summary': "Ready to start your communication journey! Every conversation is a step toward fluency.",
                'achievements': [],
                'encouragement': "Take the first step - speak about anything that interests you!",
                'next_steps': ["Start with simple topics you enjoy", "Don't worry about perfection", "Focus on expressing your thoughts"]
            }
        
        achievements = []
        encouragement_messages = []
        next_steps = []
        
        # Celebrate participation
        if stats['total_analyses'] >= 5:
            achievements.append(f"🎉 Practiced {stats['total_analyses']} times - showing great commitment!")
        elif stats['total_analyses'] >= 3:
            achievements.append(f"💪 {stats['total_analyses']} practice sessions - building consistency!")
        else:
            achievements.append(f"🌟 Started your communication journey with {stats['total_analyses']} attempts!")
        
        # Celebrate accuracy
        if stats['error_rate'] <= 20:
            achievements.append("✨ Excellent communication accuracy - you're expressing yourself clearly!")
            encouragement_messages.append("Your communication skills are really developing well!")
        elif stats['error_rate'] <= 40:
            achievements.append("📈 Good communication progress - you're on the right track!")
            encouragement_messages.append("You're making steady improvements with each conversation!")
        else:
            achievements.append("🚀 Every attempt makes you stronger - keep practicing!")
            encouragement_messages.append("Remember, every expert was once a beginner - you're building important skills!")
        
        # Celebrate confidence
        if stats['confidence_average'] >= 0.8:
            achievements.append("🔥 High confidence in communication - you're becoming fluent!")
        elif stats['confidence_average'] >= 0.6:
            achievements.append("📊 Building communication confidence steadily!")
        
        # Celebrate improvement trend
        if stats['improvement_trend'] == 'improving':
            achievements.append("⬆️ Showing clear improvement - fantastic progress!")
            encouragement_messages.append("Your communication skills are getting noticeably better!")
        elif stats['improvement_trend'] == 'stable':
            achievements.append("🎯 Maintaining consistent communication quality!")
        
        # Provide next steps based on performance
        if stats['error_rate'] > 50:
            next_steps.extend([
                "Focus on expressing complete thoughts",
                "Practice with topics you're passionate about",
                "Don't worry about perfection - aim for clear communication"
            ])
        else:
            next_steps.extend([
                "Try discussing more complex topics",
                "Practice explaining your opinions in detail",
                "Experiment with different ways to express the same ideas"
            ])
        
        # Add encouraging messages
        general_encouragements = [
            "Every conversation is making you more confident!",
            "You're developing valuable communication skills!",
            "Keep practicing - fluency comes with consistency!",
            "Your willingness to practice shows real dedication!"
        ]
        
        if not encouragement_messages:
            import random
            encouragement_messages.append(random.choice(general_encouragements))
        
        # Create summary
        summary_parts = [
            f"Communication Session Summary: {stats['total_analyses']} practice interactions",
            f"You're building confidence and fluency with each conversation!"
        ]
        
        if stats['total_analyses'] >= 3:
            summary_parts.append(f"Communication accuracy: {100 - stats['error_rate']}% - {stats['improvement_trend'].replace('_', ' ').title()}!")
        
        return {
            'summary': " ".join(summary_parts),
            'achievements': achievements,
            'encouragement': " ".join(encouragement_messages),
            'next_steps': next_steps[:3],  # Limit to 3 next steps
            'total_conversations': stats['total_analyses'],
            'communication_accuracy': round(100 - stats['error_rate'], 1),
            'confidence_level': stats['confidence_average']
        }

    def _create_prompt(self, user_input, grammar_info=None):
        """Create the prompt for the AI model."""
        # Add grammar correction context if available
        grammar_context = ""
        if grammar_info and grammar_info.get('had_errors'):
            grammar_context = f"""
Grammar Analysis:
- Original text: "{user_input}"
- Corrected text: "{grammar_info.get('corrected_text', user_input)}"
- Grammar feedback: {grammar_info.get('grammar_feedback', '')}
- Speaking tips: {grammar_info.get('speaking_tips', '')}
"""

        return f"""You are a knowledgeable AI assistant. Respond to the user's input following these EXACT rules:

1. First, check for grammar mistakes:
   - If the word order or grammar is incorrect, start with:
     "It seems like there might be a grammatical error in your question.
     Did you mean: '[corrected question]'?
     
     Note: In English, we typically use the word order 'Who is the [title] of [place/organization]' for such questions."
   - Add a blank line after the grammar explanation

2. Then provide a comprehensive answer in 4-5 clear sentences that:
   - Starts with a direct answer to the question
   - Includes important details and context
   - Provides interesting facts or examples
   - Explains any relevant connections or implications

3. End with ONE natural follow-up question that flows from the conversation

4. Total response should be 5-6 sentences (not counting the grammar correction)

Current language: {self.current_language}
User input: "{user_input}"
{grammar_context}

Example format:
User: "who is india of father"
Assistant: "It seems like there might be a grammatical error in your question.
Did you mean: 'Who is the Father of India?'

Note: In English, we typically use the word order 'Who is the [title] of [place/organization]' rather than '[place] of [title]'.

Mahatma Gandhi is widely known as the Father of India, earning this title through his pivotal role in India's independence movement. He led India's non-violent struggle for freedom from British rule from 1915 to 1947, introducing revolutionary concepts like civil disobedience and peaceful resistance. His philosophy of non-violence, known as 'ahimsa', influenced civil rights movements worldwide and inspired leaders like Martin Luther King Jr. and Nelson Mandela. Gandhi's principles of truth, non-violence, and social justice continue to shape India's national identity and inspire movements for peace and justice globally. What aspects of Gandhi's non-violent philosophy would you like to learn more about?"

Now respond to the user's input following these rules exactly."""

    def _handle_api_error(self, error_details=None):
        """Handle API errors with appropriate messages."""
        if not GEMINI_API_KEY:
            return "Error: Gemini API key not configured. Please check your environment variables."
        elif not self.model:
            return "Error: Could not initialize Gemini AI model. Please check your API key and try restarting the server."
        return f"I apologize, but I'm having trouble generating a response right now. Error: {error_details if error_details else 'Unknown error'}"

    def _convert_to_wav(self, input_file):
        """Convert audio file to WAV format using ffmpeg."""
        try:
            output_file = input_file.rsplit('.', 1)[0] + '.wav'
            command = [
                "ffmpeg",
                "-i", input_file,
                "-acodec", "pcm_s16le",  # Use PCM 16-bit encoding
                "-ar", "16000",  # Set sample rate to 16kHz
                "-ac", "1",      # Convert to mono
                output_file,
                "-y"            # Overwrite if exists
            ]
            subprocess.run(command, check=True, capture_output=True)
            return output_file
        except Exception as e:
            print(f"Error converting audio to WAV: {e}")
            return None

    def _recognize_speech(self, audio_file_path):
        """Helper method to recognize speech from audio file."""
        try:
            # Convert audio to WAV format first
            wav_file = self._convert_to_wav(audio_file_path)
            if not wav_file:
                return None

            try:
                with sr.AudioFile(wav_file) as source:
                    audio = self.recognizer.record(source)
                    language_code = SUPPORTED_LANGUAGES[self.current_language]['code']
                    return self.recognizer.recognize_google(audio, language=language_code)
            finally:
                # Clean up the temporary WAV file
                if wav_file != audio_file_path:  # Only delete if it's a new file
                    try:
                        os.remove(wav_file)
                    except:
                        pass  # Ignore cleanup errors
        except Exception as e:
            print(f"Error in speech recognition: {e}")
            return None

def main():
    # Check for API key
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set your Gemini API key in a .env file or environment variable.")
        return
    
    # Create and run the assistant
    assistant = VoiceAssistant()
    # assistant.run()

if __name__ == "__main__":
    main() 