from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from .voice_assistant import VoiceAssistant, SUPPORTED_LANGUAGES
import os
from dotenv import load_dotenv
import time
import asyncio
from functools import partial
import subprocess

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
    async def process_audio():
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if not audio_file.filename:
            return jsonify({'error': 'Invalid audio file'}), 400
            
        language = request.form.get('language', 'English')
        assistant.current_language = language
        
        temp_input = None
        try:
            # Create temp directory if not exists
            temp_dir = os.path.join(os.getcwd(), 'temp_audio')
            os.makedirs(temp_dir, exist_ok=True)
                
            # Generate unique filename with original extension
            file_extension = os.path.splitext(audio_file.filename)[1].lower()[1:] or 'webm'
            if file_extension not in ['webm', 'mp4', 'wav', 'mp3', 'ogg']:
                file_extension = 'webm'
            
            temp_input = os.path.join(temp_dir, f'input_{os.urandom(4).hex()}.{file_extension}')
            audio_file.save(temp_input)
            
            # Process audio and get response concurrently
            loop = asyncio.get_event_loop()
            audio_task = loop.create_task(assistant.process_audio_file(temp_input))
            
            # Wait for audio processing
            result = await audio_task
            
            if not result or not result[0]:
                return jsonify({
                    'error': 'Could not understand the audio. Please try speaking clearly and ensure your microphone is working properly.'
                }), 400
                
            text, grammar_info = result
            
            # Get AI response
            ai_response = await assistant.get_ai_response(text, grammar_info)
            
            # Generate response audio
            response_filename = f'response_{os.urandom(4).hex()}_{int(time.time())}.mp3'
            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
            response_path = os.path.join(static_dir, response_filename)
            
            # Run text-to-speech in thread pool with optimized settings
            await loop.run_in_executor(
                assistant.executor,
                partial(assistant.speak_to_file, ai_response, response_path)
            )
            
            # Schedule cleanup of response file
            def cleanup_response_file():
                time.sleep(300)  # Keep file for 5 minutes
                try:
                    if os.path.exists(response_path):
                        os.remove(response_path)
                except:
                    pass
            threading.Thread(target=cleanup_response_file, daemon=True).start()
            
            return jsonify({
                'status': 'success',
                'message': 'Audio processed successfully',
                'data': {
                    'text': ai_response,
                    'audio_url': f'/static/{response_filename}',
                    'user_input': text,
                }
            })
            
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Error processing audio format. Please try a different audio format or check your microphone settings.',
                'data': None
            }), 500
        except Exception as e:
            print(f"Error processing audio: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'data': None
            }), 500
        finally:
            # Clean up temporary input file
            if temp_input and os.path.exists(temp_input):
                try:
                    os.remove(temp_input)
                except:
                    pass

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

def run_app():
    """Function to run the Flask app - used by CLI."""
    app = create_app()
    
    try:
        import hypercorn.asyncio
        from hypercorn.config import Config
        
        config = Config()
        config.bind = ["127.0.0.1:5000"]
        config.use_reloader = True
        
        import asyncio
        asyncio.run(hypercorn.asyncio.serve(app, config))
    except ImportError:
        # Fallback to regular Flask server
        app.run(debug=True, port=5000) 
