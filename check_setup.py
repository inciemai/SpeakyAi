#!/usr/bin/env python3
"""
Setup verification script for SpeakyAI
This script checks if all required dependencies are properly installed and working.
"""

import sys
import subprocess
import importlib
import os

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} - Installed")
        return True
    except ImportError:
        print(f"✗ {package_name} - Not installed")
        return False

def check_ffmpeg():
    """Check if ffmpeg is installed and accessible."""
    print("Checking ffmpeg installation...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version from output
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else "Unknown version"
            print(f"✓ ffmpeg - Installed ({version_line})")
            return True
        else:
            print("✗ ffmpeg - Installed but not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ ffmpeg - Not installed or not in PATH")
        return False

def check_api_key():
    """Check if API key is configured."""
    print("Checking API key configuration...")
    
    # Check for .env file
    if os.path.exists('.env'):
        try:
            with open('.env', 'r') as f:
                content = f.read()
                if 'GEMINI_API_KEY=' in content and 'your_actual_api_key_here' not in content:
                    print("✓ API key - Configured in .env file")
                    return True
                else:
                    print("✗ API key - Not configured in .env file")
                    return False
        except Exception as e:
            print(f"✗ API key - Error reading .env file: {e}")
            return False
    else:
        print("✗ API key - .env file not found")
        return False

def check_audio_dependencies():
    """Check audio-related dependencies."""
    print("Checking audio dependencies...")
    
    audio_packages = [
        ('pydub', 'pydub'),
        ('pygame', 'pygame'),
        ('SpeechRecognition', 'speech_recognition'),
        ('gTTS', 'gtts'),
        ('PyAudio', 'pyaudio')
    ]
    
    all_installed = True
    for package, import_name in audio_packages:
        if not check_package(package, import_name):
            all_installed = False
    
    return all_installed

def check_ai_dependencies():
    """Check AI-related dependencies."""
    print("Checking AI dependencies...")
    
    ai_packages = [
        ('google-generativeai', 'google.generativeai'),
        ('python-dotenv', 'dotenv')
    ]
    
    all_installed = True
    for package, import_name in ai_packages:
        if not check_package(package, import_name):
            all_installed = False
    
    return all_installed

def check_web_dependencies():
    """Check web framework dependencies."""
    print("Checking web dependencies...")
    
    web_packages = [
        ('Flask', 'flask'),
        ('Flask-CORS', 'flask_cors'),
        ('Flask-SocketIO', 'flask_socketio')
    ]
    
    all_installed = True
    for package, import_name in web_packages:
        if not check_package(package, import_name):
            all_installed = False
    
    return all_installed

def main():
    """Main verification function."""
    print("=" * 60)
    print("SpeakyAI - Setup Verification")
    print("=" * 60)
    print()
    
    checks = []
    
    # Check Python version
    checks.append(check_python_version())
    print()
    
    # Check ffmpeg
    checks.append(check_ffmpeg())
    print()
    
    # Check API key
    checks.append(check_api_key())
    print()
    
    # Check audio dependencies
    checks.append(check_audio_dependencies())
    print()
    
    # Check AI dependencies
    checks.append(check_ai_dependencies())
    print()
    
    # Check web dependencies
    checks.append(check_web_dependencies())
    print()
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✓ All {total} checks passed! Your setup is ready.")
        print()
        print("You can now run SpeakyAI:")
        print("  python main.py")
        print("  or")
        print("  python speaky_bot/app.py")
    else:
        print(f"✗ {total - passed} out of {total} checks failed.")
        print()
        print("To fix the issues:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Install ffmpeg: python setup_ffmpeg.py")
        print("3. Configure API key: Copy .env.template to .env and add your key")
        print("4. Run this check again: python check_setup.py")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 