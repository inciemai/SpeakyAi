from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from .voice_assistant import VoiceAssistant, SUPPORTED_LANGUAGES
import os
from dotenv import load_dotenv
import time

load_dotenv()

def create_app(config=None):
    """Application factory pattern for creating Flask app."""
    # Get the directory where this module is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_folder = os.path.join(current_dir, 'templates')
    static_folder = os.path.join(current_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    CORS(app)  # Enable CORS for all routes
    
    if config:
        app.config.update(config)
    
    # Initialize the voice assistant
    assistant = VoiceAssistant()
    
    # Periodic cleanup of old temporary files
    def cleanup_old_files():
        import time
        import glob
        while True:
            try:
                time.sleep(3600)  # Run every hour
                temp_dir = os.path.join(os.getcwd(), 'temp_audio')
                if os.path.exists(temp_dir):
                    # Remove files older than 1 hour
                    current_time = time.time()
                    for file_path in glob.glob(os.path.join(temp_dir, '*')):
                        if os.path.isfile(file_path):
                            file_age = current_time - os.path.getmtime(file_path)
                            if file_age > 3600:  # 1 hour
                                try:
                                    os.remove(file_path)
                                except:
                                    pass
            except:
                pass  # Ignore cleanup errors
    
    # Start cleanup thread
    import threading
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()
    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/process', methods=['POST'])
    def process_audio():
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'English')
        # voice_preference = request.form.get('voice', 'male')  # Default to male voice
        
        # Set the assistant's language and voice preference
        assistant.current_language = language
        # assistant.set_voice_preference(voice_preference)
        
        temp_input = None
        try:
            # Save the uploaded audio file temporarily with unique filename
            temp_dir = os.path.join(os.getcwd(), 'temp_audio')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                
            import uuid
            # Get the original filename to determine the correct extension
            original_filename = audio_file.filename
            file_extension = 'webm'  # default
            
            if original_filename:
                # Extract extension from original filename
                if '.' in original_filename:
                    file_extension = original_filename.split('.')[-1].lower()
                # Validate extension
                if file_extension not in ['webm', 'mp4', 'wav', 'mp3', 'ogg']:
                    file_extension = 'webm'  # fallback to webm
            
            temp_input = os.path.join(temp_dir, f'input_{uuid.uuid4().hex[:8]}.{file_extension}')
            audio_file.save(temp_input)
            
            # Process the audio and get response
            result = assistant.process_audio_file(temp_input)
            if result and result[0]:  # Check if we got valid text
                text, grammar_info = result
                ai_response = assistant.get_ai_response(text, grammar_info)
                
                # Generate response audio with unique filename
                response_filename = f'response_{uuid.uuid4().hex[:8]}_{int(time.time())}.mp3'
                static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
                response_path = os.path.join(static_dir, response_filename)
                assistant.speak_to_file(ai_response, response_path)
                
                # Schedule cleanup of response file after some time
                import threading
                def cleanup_response_file():
                    import time
                    time.sleep(300)  # Keep file for 5 minutes
                    try:
                        if os.path.exists(response_path):
                            os.remove(response_path)
                    except:
                        pass  # Ignore cleanup errors
                threading.Thread(target=cleanup_response_file, daemon=True).start()
                
                response = {
                    'text': ai_response,
                    'audio_url': f'/static/{response_filename}',
                    'user_input': text,
                    'grammar_correction': {
                        'corrected_text': grammar_info.get('corrected_text', text),
                        'grammar_feedback': grammar_info.get('grammar_feedback', ''),
                        'speaking_tips': grammar_info.get('speaking_tips', ''),
                        'communication_advice': grammar_info.get('communication_advice', ''),
                        'had_errors': grammar_info.get('had_errors', False),
                        'confidence_score': grammar_info.get('confidence_score', 0.5),
                        'error_categories': grammar_info.get('error_categories', []),
                        'suggestions_count': grammar_info.get('suggestions_count', 0),
                        'alternative_expressions': grammar_info.get('alternative_expressions', []),
                        'conversation_prompts': grammar_info.get('conversation_prompts', []),
                        'progress_acknowledgment': grammar_info.get('progress_acknowledgment', 'Great job practicing!')
                    }
                }
            else:
                response = {
                    'text': 'Sorry, I could not understand the audio.',
                    'audio_url': None,
                    'user_input': None,
                    'grammar_correction': None
                }
                
            return jsonify(response)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Cleanup in finally block to ensure it's always cleaned up
            if temp_input and os.path.exists(temp_input):
                try:
                    os.remove(temp_input)
                except OSError as e:
                    print(f"Warning: Could not remove temporary input file {temp_input}: {e}")
                    # If we can't remove it now, try to remove it later
                    import threading
                    def delayed_cleanup():
                        import time
                        time.sleep(1)  # Wait a bit
                        try:
                            if os.path.exists(temp_input):
                                os.remove(temp_input)
                        except:
                            pass  # Ignore cleanup errors
                    threading.Thread(target=delayed_cleanup, daemon=True).start()

    @app.route('/api/languages')
    def get_languages():
        return jsonify(SUPPORTED_LANGUAGES)

    # @app.route('/api/voices')
    # def get_voices():
    #     """Get available voice options."""
    #     return jsonify(assistant.get_available_voices())
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for plugin monitoring."""
        return jsonify({
            'status': 'healthy',
            'plugin': 'speaky-bot',
            'version': '1.0.0'
        })
    
    return app 