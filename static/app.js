// Healthcare AI Assistant Frontend
class HealthcareAssistant {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.updateStatus('Ready', 'success');
        console.log('HealthcareAssistant initialized');
    }

    initializeElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.messagesContainer = document.getElementById('messages-container');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.statusIndicator = document.getElementById('status-indicator');
        this.quickActions = document.querySelectorAll('.quick-action');
        this.currentToolElement = document.getElementById('current-tool');
        this.toolDetailsElement = document.getElementById('tool-details');
        
        console.log('Elements found:', {
            messageInput: !!this.messageInput,
            sendButton: !!this.sendButton,
            messagesContainer: !!this.messagesContainer,
            typingIndicator: !!this.typingIndicator,
            statusIndicator: !!this.statusIndicator,
            quickActions: this.quickActions.length
        });
    }

    bindEvents() {
        // Send button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => {
                console.log('Send button clicked');
                this.sendMessage();
            });
        }
        
        // Enter key press
        if (this.messageInput) {
            this.messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    console.log('Enter key pressed');
                    this.sendMessage();
                }
            });
        }

        // Quick action buttons
        this.quickActions.forEach(button => {
            button.addEventListener('click', () => {
                const query = button.getAttribute('data-query');
                console.log('Quick action clicked:', query);
                if (this.messageInput) {
                    this.messageInput.value = query;
                }
                this.sendMessage();
            });
        });

        // Home page features toggle
        const featuresButton = document.querySelector('.btn-secondary');
        if (featuresButton) {
            featuresButton.addEventListener('click', () => {
                this.toggleFeatures();
            });
        }
    }

    async sendMessage() {
        const query = this.messageInput ? this.messageInput.value.trim() : '';
        console.log('Sending message:', query);
        
        if (!query) {
            console.log('Empty query, returning');
            return;
        }

        // Add user message
        this.addMessage(query, 'user');
        
        // Clear input
        if (this.messageInput) {
            this.messageInput.value = '';
        }

        // Show typing indicator
        this.showTypingIndicator();
        
        // Update status
        this.updateStatus('Thinking...', 'warning');

        try {
            console.log('Making API request...');
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            console.log('Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Response not ok:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log('Response data:', data);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Check if agent is not ready
            if (data.detail && data.detail.includes('Agent not ready')) {
                this.addMessage('The AI agent is not ready yet. Please check if the OpenAI API key is configured correctly.', 'bot', { error: true });
                this.updateStatus('Agent not ready', 'error');
                this.updateCurrentTool('None');
                this.updateToolDetails('No details available');
                return;
            }
            
            // Extract clean answer and tool info
            const { clean_answer, tool, tool_details } = data;
            
            // Add bot response with clean answer only
            this.addMessage(clean_answer, 'bot');
            
            // Update tool info
            this.updateCurrentTool(tool || 'Unknown');
            
            // Update tool details
            this.updateToolDetails(tool_details || 'No details available');
            
            // Update status
            this.updateStatus('Ready', 'success');

        } catch (error) {
            console.error('Error in sendMessage:', error);
            this.hideTypingIndicator();
            this.addMessage(`Error: ${error.message}`, 'bot', { error: true });
            this.updateStatus('Error', 'error');
            this.updateCurrentTool('Error');
        }
    }

    addMessage(text, sender, metadata = {}) {
        // Ensure text is a string and handle undefined/null values
        const safeText = text || '';
        console.log('Adding message:', { text: safeText.substring(0, 50) + '...', sender, metadata });
        
        if (!this.messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (metadata.error) {
            messageDiv.classList.add('error-message');
        }
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        const icon = document.createElement('i');
        icon.className = sender === 'bot' ? 'fas fa-robot' : 'fas fa-user';
        avatar.appendChild(icon);
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = safeText;
        
        content.appendChild(messageText);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        console.log('Showing typing indicator');
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'block';
            this.scrollToBottom();
        }
    }

    hideTypingIndicator() {
        console.log('Hiding typing indicator');
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }

    updateStatus(text, type = 'success') {
        console.log('Updating status:', text, type);
        if (this.statusIndicator) {
            const statusText = this.statusIndicator.querySelector('.status-text');
            const statusDot = this.statusIndicator.querySelector('.status-dot');
            
            if (statusText) statusText.textContent = text;
            
            // Update dot color based on status
            if (statusDot) {
                statusDot.className = `status-dot status-${type}`;
            }
        }
    }

    updateCurrentTool(tool) {
        console.log('Updating current tool:', tool);
        if (this.currentToolElement) {
            this.currentToolElement.textContent = tool;
        }
    }



    updateToolDetails(details) {
        console.log('Updating tool details:', details);
        if (this.toolDetailsElement) {
            this.toolDetailsElement.textContent = details;
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.messagesContainer) {
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }
        }, 100);
    }

    toggleFeatures() {
        const featuresSection = document.getElementById('features');
        if (featuresSection) {
            const isVisible = featuresSection.style.display !== 'none';
            featuresSection.style.display = isVisible ? 'none' : 'block';
        }
    }
}

// Global function for home page
function showFeatures() {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
        featuresSection.style.display = 'block';
        featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize the assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing HealthcareAssistant');
    try {
        new HealthcareAssistant();
    } catch (error) {
        console.error('Error initializing HealthcareAssistant:', error);
    }
});
