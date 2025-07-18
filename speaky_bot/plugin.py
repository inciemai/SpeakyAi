"""
Plugin interface for Speaky Bot.
This module defines the plugin interface that other applications can use to integrate
the voice assistant functionality.
"""

from typing import Dict, Any, Optional
from .voice_assistant import VoiceAssistant, SUPPORTED_LANGUAGES

class SpeakyBotPlugin:
    """Main plugin implementation for Speaky Bot."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin with optional configuration."""
        self.config = config or {}
        self.assistant = VoiceAssistant()
        
        # Apply configuration
        if 'default_language' in self.config:
            self.assistant.current_language = self.config['default_language']
    
    def process_text(self, text: str, language: str = 'English') -> Dict[str, Any]:
        """
        Process text input and return response with grammar analysis.
        
        Args:
            text: Input text to process
            language: Language for processing (default: English)
        
        Returns:
            Dictionary containing:
            - response: AI response text
            - grammar_correction: Grammar analysis results
            - original_text: Original input text
            - language: Language used for processing
        """
        self.assistant.current_language = language
        result = self.assistant.process_text_input(text)
        
        return {
            'response': result['response'],
            'grammar_correction': result['grammar_correction'],
            'original_text': text,
            'language': language
        }
    
    def process_audio(self, audio_file_path: str, language: str = 'English') -> Dict[str, Any]:
        """
        Process audio input and return response.
        
        Args:
            audio_file_path: Path to audio file
            language: Language for processing (default: English)
        
        Returns:
            Dictionary containing:
            - response: AI response text
            - transcribed_text: Transcribed text from audio
            - grammar_correction: Grammar analysis results
            - language: Language used for processing
        """
        self.assistant.current_language = language
        
        # Process audio file
        result = self.assistant.process_audio_file(audio_file_path)
        if result and result[0]:
            text, grammar_info = result
            ai_response = self.assistant.get_ai_response(text, grammar_info)
            
            return {
                'response': ai_response,
                'transcribed_text': text,
                'grammar_correction': grammar_info,
                'language': language
            }
        else:
            return {
                'response': 'Could not process audio',
                'transcribed_text': None,
                'grammar_correction': None,
                'language': language,
                'error': 'Audio processing failed'
            }
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """Get list of supported languages."""
        return SUPPORTED_LANGUAGES
    
    def text_to_speech(self, text: str, language: str = 'English', output_path: Optional[str] = None) -> bool:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            language: Language for TTS (default: English)
            output_path: Path to save audio file (if None, just plays audio - requires pygame)
        
        Returns:
            True if successful, False otherwise
        """
        self.assistant.current_language = language
        
        if output_path:
            return self.assistant.speak_to_file(text, output_path)
        else:
            try:
                self.assistant.speak(text)
                return True
            except:
                print("Audio playback failed - consider providing output_path for file generation")
                return False
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        from . import __version__, __author__
        
        return {
            'name': 'Speaky Bot',
            'version': __version__,
            'author': __author__,
            'description': 'Multilingual voice assistant with grammar correction',
            'supported_languages': list(SUPPORTED_LANGUAGES.keys()),
            'features': [
                'Voice recognition',
                'Text-to-speech',
                'Grammar correction',
                'Communication analysis',
                'Multi-language support'
            ]
        }

# Plugin registry functions for easy integration
def create_plugin(config: Optional[Dict[str, Any]] = None) -> SpeakyBotPlugin:
    """Create a new instance of the Speaky Bot plugin."""
    return SpeakyBotPlugin(config)

def get_plugin_info() -> Dict[str, Any]:
    """Get plugin information without creating an instance."""
    plugin = SpeakyBotPlugin()
    return plugin.get_plugin_info()

# Export main classes and functions
__all__ = [
    'SpeakyBotPlugin', 
    'create_plugin',
    'get_plugin_info'
] 