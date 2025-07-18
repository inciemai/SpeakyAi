class VoiceAssistant {
    constructor() {
        this.micButton = document.getElementById('micButton');
        this.languageSelect = document.getElementById('languageSelect');
        this.voiceSelect = document.getElementById('voiceSelect');
        this.status = document.getElementById('status');
        this.result = document.getElementById('result');
        this.userText = document.getElementById('userText');
        this.assistantText = document.getElementById('assistantText');
        
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.initializeLanguages();
        this.initializeVoices();
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

    async initializeVoices() {
        try {
            const response = await fetch('/api/voices');
            const voices = await response.json();
            
            for (const [voiceKey, voiceName] of Object.entries(voices)) {
                const option = document.createElement('option');
                option.value = voiceKey;
                option.textContent = voiceName;
                this.voiceSelect.appendChild(option);
            }
            
            // Set male as default
            this.voiceSelect.value = 'male';
        } catch (error) {
            console.error('Error loading voices:', error);
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
            
            // Try to use WebM format, fallback to other formats if not supported
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
                this.audioChunks.push(event.data);
            });

            this.mediaRecorder.addEventListener('stop', () => {
                this.processAudio();
            });

            this.mediaRecorder.start();
            this.isRecording = true;
            this.micButton.classList.add('pulse', 'bg-red-500');
            this.status.textContent = 'Listening...';
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.status.textContent = 'Error: Could not access microphone';
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.micButton.classList.remove('pulse', 'bg-red-500');
            this.status.textContent = 'Processing...';
        }
    }

    async processAudio() {
        // Determine the correct file extension based on the MIME type
        let fileExtension = 'webm';
        if (this.mediaRecorder && this.mediaRecorder.mimeType) {
            if (this.mediaRecorder.mimeType.includes('mp4')) {
                fileExtension = 'mp4';
            } else if (this.mediaRecorder.mimeType.includes('wav')) {
                fileExtension = 'wav';
            }
        }
        
        const audioBlob = new Blob(this.audioChunks, { type: this.mediaRecorder ? this.mediaRecorder.mimeType : 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob, `recording.${fileExtension}`);  // Use correct extension
        formData.append('language', this.languageSelect.value);
        formData.append('voice', this.voiceSelect.value);  // Include voice preference

        try {
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
                
                // Handle grammar and communication feedback
                const feedbackSection = document.getElementById('feedbackSection');
                if (result.grammar_correction && result.grammar_correction.had_errors) {
                    feedbackSection.classList.remove('hidden');
                    
                    // Update corrected text
                    const correctedText = document.querySelector('#correctedText .text-gray-600');
                    correctedText.textContent = result.grammar_correction.corrected_text || result.user_input;
                    
                    // Update grammar feedback
                    const grammarFeedback = document.querySelector('#grammarFeedback .text-gray-600');
                    grammarFeedback.textContent = result.grammar_correction.grammar_feedback || 'No errors found.';
                    
                    // Update speaking tips
                    const speakingTips = document.querySelector('#speakingTips .text-gray-600');
                    speakingTips.textContent = result.grammar_correction.speaking_tips || 'No pronunciation issues.';
                    
                    // Update communication advice
                    const communicationAdvice = document.querySelector('#communicationAdvice .text-gray-600');
                    communicationAdvice.textContent = result.grammar_correction.communication_advice || 'No usage issues.';
                    
                    // Update confidence score and error categories if available
                    this.updateEnhancedFeedback(result.grammar_correction);
                } else {
                    feedbackSection.classList.add('hidden');
                }
            } else {
                this.status.textContent = 'Could not understand audio';
            }
            
            // Play audio response if available
            if (result.audio_url) {
                const audio = new Audio(result.audio_url);
                await audio.play();
            }

            this.status.textContent = 'Ready to listen...';
        } catch (error) {
            console.error('Error processing audio:', error);
            this.status.textContent = 'Error processing audio';
        }
    }

    updateEnhancedFeedback(correction) {
        // Update confidence score
        const confidenceElement = document.getElementById('confidenceScore');
        if (confidenceElement && correction.confidence_score !== undefined) {
            const confidencePercent = Math.round(correction.confidence_score * 100);
            confidenceElement.textContent = `${confidencePercent}%`;
            
            // Color code based on confidence
            if (correction.confidence_score >= 0.8) {
                confidenceElement.className = 'text-green-600 font-semibold';
            } else if (correction.confidence_score >= 0.6) {
                confidenceElement.className = 'text-yellow-600 font-semibold';
            } else {
                confidenceElement.className = 'text-red-600 font-semibold';
            }
        }
        
        // Update error categories
        const categoriesElement = document.getElementById('errorCategories');
        if (categoriesElement && correction.error_categories && correction.error_categories.length > 0) {
            const categoriesList = correction.error_categories.map(cat => 
                `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${cat}</span>`
            ).join('');
            categoriesElement.innerHTML = categoriesList;
        } else if (categoriesElement) {
            categoriesElement.innerHTML = '<span class="text-gray-500">No specific errors identified</span>';
        }
        
        // Update alternative expressions
        const alternativesElement = document.getElementById('alternativeExpressions');
        if (alternativesElement && correction.alternative_expressions && correction.alternative_expressions.length > 0) {
            const alternativesList = correction.alternative_expressions.map((alt, index) => 
                `<div class="text-sm text-gray-700 mb-1">${index + 1}. "${alt}"</div>`
            ).join('');
            alternativesElement.innerHTML = alternativesList;
        } else if (alternativesElement) {
            alternativesElement.innerHTML = '<span class="text-gray-500">No alternatives provided</span>';
        }
        
        // Update conversation prompts
        const promptsElement = document.getElementById('conversationPrompts');
        if (promptsElement && correction.conversation_prompts && correction.conversation_prompts.length > 0) {
            const promptsList = correction.conversation_prompts.map((prompt, index) => 
                `<div class="text-sm text-blue-700 mb-1 cursor-pointer hover:text-blue-900" onclick="this.parentElement.parentElement.parentElement.querySelector('#userInput') ? this.parentElement.parentElement.parentElement.querySelector('#userInput').value = '${prompt.replace(/'/g, "\\'")}' : null">💬 ${prompt}</div>`
            ).join('');
            promptsElement.innerHTML = promptsList;
        } else if (promptsElement) {
            promptsElement.innerHTML = '<span class="text-gray-500">Keep practicing! Feel free to share more thoughts.</span>';
        }
        
        // Update progress acknowledgment
        const progressElement = document.getElementById('progressAcknowledgment');
        if (progressElement && correction.progress_acknowledgment) {
            progressElement.innerHTML = `<div class="text-green-700 font-medium">🎉 ${correction.progress_acknowledgment}</div>`;
        } else if (progressElement) {
            progressElement.innerHTML = '<div class="text-blue-600">Great job practicing! Keep up the communication efforts!</div>';
        }
        
        // Update suggestions count
        const suggestionsElement = document.getElementById('suggestionsCount');
        if (suggestionsElement && correction.suggestions_count !== undefined) {
            suggestionsElement.textContent = correction.suggestions_count;
        }
    }
}

// Initialize the voice assistant when the page loads
window.addEventListener('DOMContentLoaded', () => {
    window.voiceAssistant = new VoiceAssistant();
}); 