#!/usr/bin/env python3
"""
Setup script for SpeakyAI - Installs ffmpeg dependency for audio processing
This script helps users install ffmpeg on Windows systems to resolve pydub dependency issues.
"""

import os
import sys
import subprocess
import zipfile
import urllib.request
import tempfile
import shutil
from pathlib import Path

def check_ffmpeg_installed():
    """Check if ffmpeg is already installed and accessible."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ ffmpeg is already installed and working!")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False

def download_ffmpeg():
    """Download ffmpeg for Windows."""
    print("Downloading ffmpeg for Windows...")
    
    # URL for ffmpeg Windows builds (static build)
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "ffmpeg.zip")
        
        print("Downloading from:", ffmpeg_url)
        print("This may take a few minutes...")
        
        # Download the file
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        
        print("Download completed! Extracting...")
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the extracted directory
        extracted_dir = None
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path) and item.startswith('ffmpeg'):
                extracted_dir = item_path
                break
        
        if not extracted_dir:
            raise Exception("Could not find ffmpeg directory in extracted files")
        
        # Copy ffmpeg.exe to a location in PATH or current directory
        ffmpeg_exe = os.path.join(extracted_dir, 'bin', 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_exe):
            raise Exception("ffmpeg.exe not found in extracted files")
        
        # Copy to current directory for easy access
        current_dir = os.getcwd()
        target_path = os.path.join(current_dir, 'ffmpeg.exe')
        
        shutil.copy2(ffmpeg_exe, target_path)
        print(f"✓ ffmpeg.exe copied to: {target_path}")
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)
        
        return target_path
        
    except Exception as e:
        print(f"Error downloading ffmpeg: {e}")
        return None

def install_ffmpeg_via_chocolatey():
    """Try to install ffmpeg using Chocolatey package manager."""
    print("Attempting to install ffmpeg via Chocolatey...")
    
    try:
        # Check if Chocolatey is installed
        result = subprocess.run(['choco', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("Chocolatey not found. Please install Chocolatey first:")
            print("Visit: https://chocolatey.org/install")
            return False
        
        # Install ffmpeg via Chocolatey
        print("Installing ffmpeg via Chocolatey...")
        result = subprocess.run(['choco', 'install', 'ffmpeg', '-y'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ ffmpeg installed successfully via Chocolatey!")
            return True
        else:
            print(f"Chocolatey installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error with Chocolatey installation: {e}")
        return False

def install_ffmpeg_via_scoop():
    """Try to install ffmpeg using Scoop package manager."""
    print("Attempting to install ffmpeg via Scoop...")
    
    try:
        # Check if Scoop is installed
        result = subprocess.run(['scoop', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("Scoop not found. Please install Scoop first:")
            print("Visit: https://scoop.sh/")
            return False
        
        # Install ffmpeg via Scoop
        print("Installing ffmpeg via Scoop...")
        result = subprocess.run(['scoop', 'install', 'ffmpeg'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ ffmpeg installed successfully via Scoop!")
            return True
        else:
            print(f"Scoop installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error with Scoop installation: {e}")
        return False

def add_to_path(ffmpeg_path):
    """Add ffmpeg directory to PATH environment variable."""
    try:
        ffmpeg_dir = os.path.dirname(os.path.abspath(ffmpeg_path))
        
        # Get current PATH
        current_path = os.environ.get('PATH', '')
        
        if ffmpeg_dir not in current_path:
            # Add to PATH
            new_path = ffmpeg_dir + os.pathsep + current_path
            os.environ['PATH'] = new_path
            
            print(f"✓ Added {ffmpeg_dir} to PATH for this session")
            print("Note: To make this permanent, add the directory to your system PATH")
            return True
        else:
            print("✓ ffmpeg directory is already in PATH")
            return True
            
    except Exception as e:
        print(f"Error adding to PATH: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 60)
    print("SpeakyAI - FFmpeg Setup Script")
    print("=" * 60)
    print()
    
    # Check if ffmpeg is already installed
    if check_ffmpeg_installed():
        print("Setup complete! Your system is ready to run SpeakyAI.")
        return
    
    print("FFmpeg is required for audio processing in SpeakyAI.")
    print("This script will help you install it.")
    print()
    
    # Try different installation methods
    installation_success = False
    
    # Method 1: Try Chocolatey
    print("Method 1: Installing via Chocolatey package manager...")
    if install_ffmpeg_via_chocolatey():
        installation_success = True
    else:
        print()
        # Method 2: Try Scoop
        print("Method 2: Installing via Scoop package manager...")
        if install_ffmpeg_via_scoop():
            installation_success = True
        else:
            print()
            # Method 3: Manual download
            print("Method 3: Manual download and installation...")
            ffmpeg_path = download_ffmpeg()
            if ffmpeg_path:
                add_to_path(ffmpeg_path)
                installation_success = True
    
    print()
    if installation_success:
        print("✓ FFmpeg installation completed successfully!")
        print()
        print("You can now run SpeakyAI without the ffmpeg warning.")
        print("If you still see warnings, try restarting your terminal/command prompt.")
    else:
        print("✗ FFmpeg installation failed.")
        print()
        print("Manual installation options:")
        print("1. Download from: https://ffmpeg.org/download.html")
        print("2. Install via Chocolatey: choco install ffmpeg")
        print("3. Install via Scoop: scoop install ffmpeg")
        print("4. Add ffmpeg to your system PATH after installation")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main() 