from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="speaky-bot",
    version="1.0.0",
    author="SpeakyAI",
    author_email="contact@speakyai.com",
    description="A multilingual voice assistant with grammar correction and communication skills analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/speakyai/speaky-bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=3.0.0",
        "Flask-CORS>=4.0.0",
        "SpeechRecognition>=3.10.0",
        "pydub>=0.25.0",
        "gTTS>=2.5.0",
        "pygame>=2.5.0",
        "google-generativeai>=0.3.0",
        "python-dotenv>=1.0.0",
        "PyAudio>=0.2.14; sys_platform != 'win32'",  # Optional for Windows
    ],
    include_package_data=True,
    package_data={
        'speaky_bot': [
            'templates/*.html',
            'static/js/*.js',
        ],
    },
    entry_points={
        'console_scripts': [
            'speaky-bot=main:main',
        ],
    },
) 