from setuptools import setup, find_packages

setup(
    name="speaky-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "flask-socketio",
        "pyttsx3",
        "SpeechRecognition",
        "pyaudio",
        "pydub",
        "requests",
        "python-dotenv",
        "loguru",
    ],
    python_requires=">=3.8",
    author="SpeakyAI",
    description="A voice assistant bot with web interface",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 