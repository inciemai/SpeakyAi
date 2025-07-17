# SpeakyAI Installation Guide

This guide will help you set up SpeakyAI and resolve common issues, especially the ffmpeg warning.

## 🚀 Quick Start (Windows)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install FFmpeg (Required for Audio Processing)
**Option A: Automatic Installation (Recommended)**
```bash
python setup_ffmpeg.py
```

**Option B: Using Chocolatey**
```bash
choco install ffmpeg
```

**Option C: Using Scoop**
```bash
scoop install ffmpeg
```

### Step 3: Configure API Key
1. Copy `.env.template` to `.env`
2. Edit `.env` and add your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Step 4: Verify Setup
```bash
python check_setup.py
```

### Step 5: Run SpeakyAI
```bash
python main.py
```

## 🔧 Detailed Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (or Linux/macOS)
- Internet connection
- Microphone access

### Step-by-Step Instructions

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd SpeakyAi
```

#### 2. Create Virtual Environment (Recommended)
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/macOS
```

#### 3. Install Python Packages
```bash
pip install -r requirements.txt
```

#### 4. Install FFmpeg

**Windows Users:**
```bash
# Method 1: Automatic (easiest)
python setup_ffmpeg.py

# Method 2: Chocolatey
choco install ffmpeg

# Method 3: Scoop
scoop install ffmpeg

# Method 4: Manual download
# Visit: https://ffmpeg.org/download.html
# Download Windows build, extract, add to PATH
```

**Linux Users:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

**macOS Users:**
```bash
# Using Homebrew
brew install ffmpeg

# Using MacPorts
sudo port install ffmpeg
```

#### 5. Get API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key (free)
3. Copy the key

#### 6. Configure Environment
```bash
# Copy template
cp .env.template .env

# Edit .env file and add your API key
# GEMINI_API_KEY=your_actual_api_key_here
```

#### 7. Test Installation
```bash
python check_setup.py
```

## 🛠️ Troubleshooting

### FFmpeg Warning
**Problem:** You see this warning:
```
RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
```

**Solutions:**
1. **Run the setup script:**
   ```bash
   python setup_ffmpeg.py
   ```

2. **Check if ffmpeg is installed:**
   ```bash
   ffmpeg -version
   ```

3. **Add to PATH manually:**
   - Find where ffmpeg.exe is located
   - Add that directory to your system PATH
   - Restart your terminal

### Audio Issues
**Problem:** Microphone not working or audio not processing

**Solutions:**
1. Check microphone permissions in Windows settings
2. Ensure audio drivers are installed
3. Try a different browser (Chrome recommended)
4. Check if microphone is set as default device

### API Key Issues
**Problem:** "Invalid API key" or similar errors

**Solutions:**
1. Verify your API key is correct in `.env` file
2. Check your internet connection
3. Ensure the API key has proper permissions
4. Try regenerating the API key

### Python Package Issues
**Problem:** Import errors or missing packages

**Solutions:**
1. Reinstall requirements:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

2. Update pip:
   ```bash
   python -m pip install --upgrade pip
   ```

3. Check Python version:
   ```bash
   python --version
   # Should be 3.8 or higher
   ```

## 🎯 Verification Checklist

Before running SpeakyAI, ensure:

- [ ] Python 3.8+ installed
- [ ] All packages installed (`pip install -r requirements.txt`)
- [ ] FFmpeg installed and in PATH
- [ ] API key configured in `.env` file
- [ ] Microphone working and accessible
- [ ] Internet connection available

Run the verification script:
```bash
python check_setup.py
```

All checks should pass before proceeding.

## 🚀 Running SpeakyAI

### Web Interface (Recommended)
```bash
python main.py
# or
python speaky_bot/app.py
```

Then open: http://localhost:5000

### Command Line Interface
```bash
python speaky_bot/cli.py
```

## 📞 Getting Help

If you encounter issues:

1. **Run the verification script:**
   ```bash
   python check_setup.py
   ```

2. **Check the troubleshooting section above**

3. **Common solutions:**
   - Restart your terminal/command prompt
   - Restart your computer
   - Reinstall Python packages
   - Check Windows updates

4. **Still having issues?**
   - Check the README.md file
   - Look at the error messages carefully
   - Ensure all prerequisites are met

## 🎉 Success!

Once everything is working, you should see:
- No ffmpeg warnings
- Web interface loads at http://localhost:5000
- Microphone button works
- Audio processing works correctly
- AI responses are generated

Enjoy using SpeakyAI! 🎤🤖 