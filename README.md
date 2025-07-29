# English Speaking Coach - AI-Powered Voice Assistant

An intelligent English learning assistant that helps users improve their spoken English and communication skills through real-time AI-powered feedback, grammar correction, and pronunciation guidance.

## 🎯 What is a Plugin?

A plugin is a modular software component that adds specific functionality to your application without modifying the core code. The Speaky Bot plugin provides:

- **Easy Integration**: Drop-in voice assistant functionality for any Python application
- **Modular Design**: Use only the features you need
- **Standardized Interface**: Consistent API for voice processing, text analysis, and TTS
- **Extensible**: Can be extended with custom features

## 🚀 Features

- **🎯 English Learning Focus** - Specialized for improving English communication skills
- **✏️ Real-time Grammar Correction** - Detects and explains grammar mistakes
- **💬 Natural Expression Coaching** - Suggests more fluent, natural ways to express ideas
- **📚 Educational Explanations** - Detailed explanations of corrections with academic context
- **🗣️ Pronunciation Guidance** - Tips for better pronunciation and delivery
- **❓ Interactive Learning** - Follow-up questions and vocabulary expansion suggestions
- **🎙️ Voice Recognition** - Advanced speech-to-text for natural interaction
- **🔊 AI-Powered Responses** - Uses Google Gemini AI for intelligent, contextual feedback
- **🌐 Web Interface** - Beautiful, modern web UI for easy interaction
- **📱 Cross-Platform** - Works on any device with a microphone and web browser

## 📦 Quick Setup

### 🚀 One-Command Setup
```bash
# Clone and setup automatically
git clone <repository-url>
cd speaky-bot
python setup_coach.py
```

### 🔧 Manual Setup
```bash
# 1. Clone the repository
git clone <repository-url>
cd speaky-bot

# 2. Install requirements
pip install -r requirements.txt

# 3. Create environment file
cp .env.template .env

# 4. Edit .env and add your API key
# Get your free API key from: https://makersuite.google.com/app/apikey
```

### 📦 Optional Dependencies

For local development with audio playback support:

```bash
# Install PortAudio development libraries first:

# On Ubuntu/Debian:
sudo apt-get install portaudio19-dev

# On macOS:
brew install portaudio

# On Windows:
# PortAudio is included in PyAudio wheels for Windows

# Then install optional dependencies:
pip install -r optional-requirements.txt
```

Note: PyAudio is only required for local audio playback. The web interface works without it.

## ⚙️ Configuration

### 🔑 Get Your Free API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key (it's free!)
3. Copy the key and paste it in your `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### ✅ Test Your Setup
```bash
# Run the demo to test everything works
python examples/english_learning_demo.py
```

## 🎮 How to Use

### 🌐 Web Interface (Recommended)
```bash
# Start the English Speaking Coach
python app.py

# Open in your browser
# http://localhost:5000
```

**Using the Web Interface:**
1. 🎙️ Click the microphone button
2. 🗣️ Speak in English (ask questions, make statements, etc.)
3. 📚 Get instant feedback with:
   - Grammar corrections
   - Better ways to express your ideas
   - Pronunciation tips
   - Educational explanations
   - Follow-up questions

### 📝 Text Demo
```bash
# See examples of corrections and feedback
python examples/english_learning_demo.py
```

## 💬 Example Interaction

Here's exactly how the English Speaking Coach works:

**👤 User says:** *"Who is the nation of the father of India?"*

**🤖 Coach responds:**
> There's a small grammatical issue in your sentence. The correct way to ask this would be: "Who is the Father of the Nation of India?"
> 
> This correction makes your sentence clearer because the phrase "Father of the Nation" is a proper title that should be kept together.
> 
> Here's a more natural way to express this: "Who is considered the Father of the Nation in India?"
> 
> To answer your question: Mahatma Gandhi is widely regarded as the Father of the Nation in India because of his pivotal role in the struggle for independence through non-violent resistance.
> 
> Would you like to know more about Gandhi's philosophy of non-violence or other independence leaders?

**👤 User says:** *"Yes, I do."*

**🤖 Coach responds:**
> Great! Your grammar is perfect!
> 
> Here's a more conversational way to express interest: "Yes, I'd love to learn more about that" or "That sounds fascinating, please tell me more."
> 
> Gandhi's philosophy was based on 'Satyagraha' (truth-force) and 'Ahimsa' (non-violence). He believed that non-violent resistance was more powerful than violence because it could change hearts and minds, not just defeat opponents...
> 
> Would you like me to explain any specific aspects of his philosophy, or are you curious about how these principles influenced other world leaders?

### 🔧 For Developers
```python
from speaky_bot.plugin import create_plugin

# Create plugin instance
plugin = create_plugin({
    'default_language': 'English'
})

# Process text
result = plugin.process_text("Hello, how are you?")
print(result['response'])

# Process audio file
result = plugin.process_audio('audio.wav', language='English')
print(result['transcribed_text'])

# Text-to-speech
plugin.text_to_speech("Hello world", output_path="output.mp3")
```

### Flask Integration
```python
from flask import Flask
from speaky_bot.plugin import create_plugin

app = Flask(__name__)
plugin = create_plugin()

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json['text']
    result = plugin.process_text(text)
    return jsonify(result)
```

## 🔧 Plugin Interface

The plugin provides a standardized interface for integration:

```python
from speaky_bot.plugin import SpeakyBotPlugin

class MyCustomPlugin(SpeakyBotPlugin):
    def process_text(self, text, language='English'):
        # Custom text processing logic
        return super().process_text(text, language)
```

## 🌍 Supported Languages

- **English** - Full support with grammar analysis
- **Malayalam** (മലയാളം) - Native language support
- **Hindi** (हिंदी) - Comprehensive language features
- **Tamil** (தமிழ்) - Complete language integration
- **German** (Deutsch) - Full language support

## 📁 Project Structure

```
speaky-bot/
├── speaky_bot/              # Main plugin package
│   ├── __init__.py         # Package initialization
│   ├── voice_assistant.py  # Core voice assistant logic
│   ├── app.py              # Flask web application
│   ├── cli.py              # Command-line interface
│   ├── plugin.py           # Plugin interface
│   ├── templates/          # Web templates
│   └── static/             # Static files (JS, CSS)
├── examples/               # Usage examples
├── setup.py                # Package setup
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## 🔌 How the Plugin Works

1. **Voice Input**: Captures audio through microphone or file
2. **Speech Recognition**: Converts audio to text using Google Speech API
3. **Grammar Analysis**: Analyzes text for grammar and communication issues
4. **AI Response**: Generates intelligent responses using Gemini AI
5. **Text-to-Speech**: Converts responses to natural speech
6. **Feedback**: Provides grammar corrections and communication tips

## 🛠️ API Reference

### Core Methods
- `process_text(text, language)` - Process text input
- `process_audio(audio_path, language)` - Process audio file
- `text_to_speech(text, language, output_path)` - Generate speech
- `get_supported_languages()` - Get available languages
- `get_plugin_info()` - Get plugin metadata

### Web Endpoints
- `GET /` - Web interface
- `POST /api/process` - Process audio
- `GET /api/languages` - Get languages
- `GET /api/voices` - Get voice options
- `GET /api/health` - Health check

## 📋 Requirements

- Python 3.8+
- Internet connection for AI processing
- Microphone access (for voice input)
- Google Gemini AI API key
- FFmpeg (for audio processing) - **See troubleshooting section below**

## 🔧 Troubleshooting

### FFmpeg Warning/Error
If you see this warning when running SpeakyAI:
```
RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
```

**Quick Fix (Windows):**
```bash
# Run the automatic setup script
python setup_ffmpeg.py

# Or use the batch file
setup_ffmpeg.bat
```

**Manual Installation Options:**

1. **Using Chocolatey (Windows):**
   ```bash
   choco install ffmpeg
   ```

2. **Using Scoop (Windows):**
   ```bash
   scoop install ffmpeg
   ```

3. **Manual Download:**
   - Visit: https://ffmpeg.org/download.html
   - Download the Windows build
   - Extract and add to your system PATH

4. **Linux/macOS:**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # macOS (using Homebrew)
   brew install ffmpeg
   ```

**After Installation:**
- Restart your terminal/command prompt
- Run SpeakyAI again - the warning should be gone!

### Other Common Issues

**Audio Not Working:**
- Check microphone permissions
- Ensure audio drivers are installed
- Try a different browser (Chrome recommended)

**API Key Issues:**
- Verify your Google Gemini API key is correct
- Check your internet connection
- Ensure the API key has proper permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details