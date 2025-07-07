#!/usr/bin/env python3
"""
Command-line interface for Speaky Bot plugin.
"""

import argparse
import sys
from .app import run_app
import os

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Speaky Bot - Multilingual Voice Assistant Plugin",
        prog="speaky-bot"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Web server command
    web_parser = subparsers.add_parser(
        'web', 
        help='Run the web interface server'
    )
    web_parser.add_argument(
        '--port', 
        type=int, 
        default=5000, 
        help='Port to run the web server on (default: 5000)'
    )
    web_parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Run in debug mode'
    )
    
    # Plugin info command
    info_parser = subparsers.add_parser(
        'info', 
        help='Show plugin information'
    )
    
    # Setup command
    setup_parser = subparsers.add_parser(
        'setup', 
        help='Setup the plugin (create .env file template)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'web':
        from .app import create_app
        app = create_app()
        app.run(debug=args.debug, port=args.port)
    
    elif args.command == 'info':
        print_plugin_info()
    
    elif args.command == 'setup':
        setup_plugin()

def print_plugin_info():
    """Print plugin information."""
    from . import __version__, __author__, __email__
    
    print("Speaky Bot Plugin Information")
    print("=" * 40)
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print(f"Email: {__email__}")
    print("\nFeatures:")
    print("- Multilingual voice recognition")
    print("- AI-powered responses using Google Gemini")
    print("- Grammar correction and communication analysis")
    print("- Text-to-speech in multiple languages")
    print("- Web interface and CLI support")
    print("\nSupported Languages:")
    from .voice_assistant import SUPPORTED_LANGUAGES
    for lang, details in SUPPORTED_LANGUAGES.items():
        print(f"- {lang} ({details['native_name']})")

def setup_plugin():
    """Setup the plugin by creating configuration files."""
    env_template = """# Speaky Bot Plugin Configuration
# Copy this file to .env and fill in your API keys

# Google Gemini AI API Key (Required)
# Get it from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    env_file = '.env.template'
    if os.path.exists(env_file):
        print(f"{env_file} already exists.")
    else:
        with open(env_file, 'w') as f:
            f.write(env_template)
        print(f"Created {env_file}")
        print("Please copy this file to .env and add your API keys.")
    
    # Create temp_audio directory
    temp_dir = 'temp_audio'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Created {temp_dir} directory for temporary audio files.")

if __name__ == '__main__':
    main() 