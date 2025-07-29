class VoiceAssistant {
    constructor() {
        this.micButton = document.getElementById('micButton');
        this.languageSelect = document.getElementById('languageSelect');
        this.status = document.getElementById('status');
        this.result = document.getElementById('result');
        this.userText = document.getElementById('userText');
        this.grammarCorrection = document.getElementById('grammarCorrection');
        this.assistantText = document.getElementById('assistantText');
        
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.initializeLanguages();
        this.setupEventListeners();
    }

    async initializeLanguages() {
        try {
            const response = await fetch('/api/languages');
            const languages = await response.json();
            
            for (const [lang, details] of Object.entries(languages)) {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = `${lang} (${details.native_name})`;
                this.languageSelect.appendChild(option);
            }
        } catch (error) {
            console.error('Error loading languages:', error);
        }
    }

    setupEventListeners() {
        this.micButton.addEventListener('click', () => {
            if (!this.isRecording) {
                this.startRecording();
            } else {
                this.stopRecording();
            }
        });
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                } 
            });
            
            let mimeType = 'audio/webm';
            if (!MediaRecorder.isTypeSupported('audio/webm')) {
                if (MediaRecorder.isTypeSupported('audio/mp4')) {
                    mimeType = 'audio/mp4';
                } else if (MediaRecorder.isTypeSupported('audio/wav')) {
                    mimeType = 'audio/wav';
                } else {
                    mimeType = ''; // Use default
                }
            }
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: mimeType
            });
            this.audioChunks = [];

            this.mediaRecorder.addEventListener('dataavailable', (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            });

            this.mediaRecorder.addEventListener('stop', async () => {
                const audioBlob = new Blob(this.audioChunks, { 
                    type: this.mediaRecorder.mimeType 
                });
                await this.processAudio(audioBlob);
                
                stream.getTracks().forEach(track => track.stop());
            });

            this.mediaRecorder.start(100);
            this.isRecording = true;
            this.micButton.classList.add('pulse', 'bg-red-500');
            this.status.textContent = 'Listening...';
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.status.textContent = 'Error: Could not access microphone';
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.micButton.classList.remove('pulse', 'bg-red-500');
            this.status.textContent = 'Processing...';
        }
    }

    async processAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'audio.webm');
            formData.append('language', this.languageSelect.value);
            
            this.status.textContent = 'Processing...';
            
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.error) {
                this.status.textContent = `Error: ${result.error}`;
                return;
            }

            // Show the result container
            this.result.classList.remove('hidden');
            
            // Update the text content
            if (result.user_input && result.text) {
                this.userText.textContent = `You: ${result.user_input}`;
                this.assistantText.textContent = `Assistant: ${result.text}`;
                
                // Play audio response if available
                if (result.audio_url) {
                    const audio = new Audio(result.audio_url);
                    await audio.play();
                }
            } else {
                this.status.textContent = 'Could not process audio. Please try again.';
            }
            
            // Reset recording state
            this.isRecording = false;
            this.micButton.classList.remove('recording');
            this.status.textContent = 'Ready to listen...';
            
        } catch (error) {
            console.error('Error processing audio:', error);
            this.status.textContent = 'Error processing audio. Please try again.';
        }
    }
}

// Initialize the voice assistant when the page loads
window.addEventListener('DOMContentLoaded', () => {
    window.voiceAssistant = new VoiceAssistant();
});