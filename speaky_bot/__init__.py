"""
Speaky Bot - A multilingual voice assistant plugin with grammar correction and communication skills analysis.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .voice_assistant import VoiceAssistant, SUPPORTED_LANGUAGES
from .app import create_app

__all__ = ['VoiceAssistant', 'SUPPORTED_LANGUAGES', 'create_app'] 