from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="speaky-bot-plugin",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A multilingual voice assistant plugin with grammar correction and communication skills analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/speaky-bot",
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
    install_requires=requirements,
    include_package_data=True,
    package_data={
        'speaky_bot': [
            'templates/*.html',
            'static/js/*.js',
        ],
    },
    entry_points={
        'console_scripts': [
            'speaky-bot=speaky_bot.cli:main',
        ],
    },
    extras_require={
        'dev': [
            'pytest',
            'black',
            'flake8',
        ],
    },
) 