"""
Speaky Bot - A multilingual voice assistant with grammar correction and communication skills analysis.
"""

__version__ = "1.0.0"
__author__ = "SpeakyAI"
__email__ = "contact@speakyai.com"

from .voice_assistant import VoiceAssistant, SUPPORTED_LANGUAGES
from .app import create_app

__all__ = ['VoiceAssistant', 'SUPPORTED_LANGUAGES', 'create_app'] 