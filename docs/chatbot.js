/**
 * Feng Shui AI Chatbot Component
 * Provides intelligent improvement suggestions based on analysis results
 */

class FengShuiChatbot {
    constructor() {
        this.isOpen = false;
        this.conversationHistory = [];
        this.currentAnalysisData = null;
        const baseUrl = window.apiBaseUrl || 'https://fengshui-ai.onrender.com';
        this.apiUrl = `${baseUrl}/api`;
        
        this.init();
    }
    
    init() {
        this.createChatUI();
        this.attachEventListeners();
    }
    
    createChatUI() {
        // Create chatbot container
        const chatContainer = document.createElement('div');
        chatContainer.id = 'fengshui-chatbot';
        chatContainer.className = 'chatbot-container';
        chatContainer.innerHTML = `
            <!-- Chat Toggle Button -->
            <button id="chat-toggle-btn" class="chat-toggle-btn" title="Ask AI for Improvements">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
                    <circle cx="12" cy="9" r="1.5" fill="white"/>
                    <circle cx="8" cy="9" r="1.5" fill="white"/>
                    <circle cx="16" cy="9" r="1.5" fill="white"/>
                </svg>
                <span class="chat-btn-text" data-i18n="chat.btn">Ask AI</span>
            </button>
            
            <!-- Chat Window -->
            <div id="chat-window" class="chat-window chat-hidden">
                <div class="chat-header">
                    <div class="chat-header-content">
                        <div class="chat-avatar">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
                                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2"/>
                                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2"/>
                            </svg>
                        </div>
                        <div class="chat-title">
                            <h3 data-i18n="chat.title">Feng Shui AI Assistant</h3>
                            <p class="chat-subtitle" data-i18n="chat.subtitle">Get personalized improvement suggestions</p>
                        </div>
                    </div>
                    <button id="chat-close-btn" class="chat-close-btn" title="Close">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>
                
                <div id="chat-messages" class="chat-messages">
                    <div class="chat-welcome">
                        <div class="welcome-icon">💡</div>
                        <h4 data-i18n="chat.welcome.title">How can I help improve your space?</h4>
                        <p data-i18n="chat.welcome.desc">I'll analyze your feng shui results and provide actionable recommendations.</p>
                    </div>
                </div>
                
                <div class="chat-quick-actions" id="quick-actions">
                    <button class="quick-action-btn" data-action="improve" data-i18n="chat.quick.improve">
                        🎯 How to improve overall?
                    </button>
                    <button class="quick-action-btn" data-action="qi-flow" data-i18n="chat.quick.qi">
                        🌊 Improve Qi flow
                    </button>
                    <button class="quick-action-btn" data-action="budget" data-i18n="chat.quick.budget">
                        💰 Budget-friendly tips
                    </button>
                </div>
                
                <div class="chat-input-container">
                    <div class="chat-input-wrapper">
                        <textarea 
                            id="chat-input" 
                            class="chat-input" 
                            data-i18n="chat.input.placeholder"
                            placeholder="Ask about improvements..."
                            rows="1"
                        ></textarea>
                        <button id="chat-send-btn" class="chat-send-btn" title="Send message">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                    <p class="chat-disclaimer" data-i18n="chat.disclaimer">AI-powered suggestions based on feng shui principles</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(chatContainer);
    }
    
    attachEventListeners() {
        const toggleBtn = document.getElementById('chat-toggle-btn');
        const closeBtn = document.getElementById('chat-close-btn');
        const sendBtn = document.getElementById('chat-send-btn');
        const input = document.getElementById('chat-input');
        
        toggleBtn.addEventListener('click', () => this.toggleChat());
        closeBtn.addEventListener('click', () => this.closeChat());
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleQuickAction(action);
            });
        });

        // Re-apply translations when language changes
        window.addEventListener('qilang:changed', () => {
            this.applyTranslations();
        });

        // Apply current language immediately
        this.applyTranslations();
        
        // Enter to send (Shift+Enter for new line)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
    }
    
    toggleChat() {
        this.isOpen = !this.isOpen;
        const chatWindow = document.getElementById('chat-window');
        const toggleBtn = document.getElementById('chat-toggle-btn');
        
        if (this.isOpen) {
            chatWindow.classList.remove('chat-hidden');
            toggleBtn.classList.add('chat-open');
            
            // Check if analysis data is available
            if (!this.currentAnalysisData) {
                this.showNoAnalysisMessage();
            }
        } else {
            chatWindow.classList.add('chat-hidden');
            toggleBtn.classList.remove('chat-open');
        }
    }
    
    closeChat() {
        this.isOpen = false;
        const chatWindow = document.getElementById('chat-window');
        const toggleBtn = document.getElementById('chat-toggle-btn');
        
        chatWindow.classList.add('chat-hidden');
        toggleBtn.classList.remove('chat-open');
    }
    
    applyTranslations() {
        if (typeof QiLang === 'undefined') return;
        const container = document.getElementById('fengshui-chatbot');
        if (!container) return;
        container.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = QiLang.get(key);
            if (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && el.type !== 'button')) {
                el.placeholder = text;
            } else {
                el.textContent = text;
            }
        });
    }

    showNoAnalysisMessage() {
        const messagesContainer = document.getElementById('chat-messages');
        const text = (typeof QiLang !== 'undefined') ? QiLang.get('chat.no.analysis') : 'Please run a feng shui analysis first. Once you have results, I can provide personalized improvement suggestions!';
        const noAnalysisMsg = `
            <div class="chat-message bot-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>${text}</p>
                </div>
            </div>
        `;
        
        const welcome = messagesContainer.querySelector('.chat-welcome');
        if (welcome) {
            welcome.insertAdjacentHTML('afterend', noAnalysisMsg);
        }
    }
    
    setAnalysisData(analysisData) {
        this.currentAnalysisData = analysisData;
        console.log('Analysis data set for chatbot:', analysisData);
        
        // Show notification that AI is ready
        const toggleBtn = document.getElementById('chat-toggle-btn');
        toggleBtn.classList.add('has-data');
    }
    
    handleQuickAction(action) {
        // Always send queries in English to the backend for consistent AI responses
        let query = '';
        switch(action) {
            case 'improve':
                query = 'How can I improve the overall feng shui of this location?';
                break;
            case 'qi-flow':
                query = 'What specific steps can I take to improve the Qi flow?';
                break;
            case 'budget':
                query = 'What are some budget-friendly improvements I can make?';
                break;
        }
        
        if (query) {
            document.getElementById('chat-input').value = query;
            this.sendMessage();
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Clear input and reset height
        input.value = '';
        input.style.height = 'auto';
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Hide quick actions after first message
        document.getElementById('quick-actions').style.display = 'none';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            let response;
            
            if (this.currentAnalysisData) {
                // Get improvement suggestions based on analysis
                response = await this.getImprovementSuggestions(message);
            } else {
                // General chat without analysis context
                response = await this.sendChatMessage(message);
            }
            
            this.hideTypingIndicator();
            
            if (response.success) {
                this.addMessage(response.response, 'bot', response.is_mock);
            } else {
                // Prefer backend-provided explanation so users see the real cause.
                let errorText = response.response || response.error || 'Sorry, I encountered an error. Please try again.';

                if ((response.error || '').includes('402')) {
                    errorText = 'DeepSeek API returned 402 (quota/billing). Please check your DeepSeek credits or billing, then try again.';
                }

                this.addMessage(errorText, 'bot', false, true);
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addMessage('Connection error. Please check if the backend server is running.', 'bot', false, true);
        }
    }
    
    async getImprovementSuggestions(query = null) {
        const response = await fetch(`${this.apiUrl}/chat/improve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                analysis_data: this.currentAnalysisData,
                query: query
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.data;
    }
    
    async sendChatMessage(message) {
        const response = await fetch(`${this.apiUrl}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                history: this.conversationHistory,
                context: this.currentAnalysisData
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.data;
    }
    
    addMessage(content, sender, isMock = false, isError = false) {
        const messagesContainer = document.getElementById('chat-messages');
        const welcome = messagesContainer.querySelector('.chat-welcome');
        
        // Remove welcome message on first real message
        if (welcome && sender === 'user') {
            welcome.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message${isError ? ' error-message' : ''}`;
        
        const avatar = sender === 'user' ? '👤' : '🤖';
        const formattedContent = this.formatMessage(content);
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                ${formattedContent}
                ${isMock ? '<div class="mock-notice">💡 This is a sample response. Add your DeepSeek API key for personalized suggestions.</div>' : ''}
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Add to conversation history
        if (!isError) {
            this.conversationHistory.push({
                role: sender === 'user' ? 'user' : 'assistant',
                content: content
            });
        }
    }
    
    formatMessage(content) {
        // Convert markdown-style formatting to HTML
        let formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
            .replace(/^## (.*$)/gim, '<h4>$1</h4>') // H4
            .replace(/^### (.*$)/gim, '<h5>$1</h5>') // H5
            .replace(/^- (.*$)/gim, '<li>$1</li>') // List items
            .replace(/\n\n/g, '</p><p>') // Paragraphs
            .replace(/\n/g, '<br>'); // Line breaks
        
        // Wrap list items in ul
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Wrap in paragraph if no block elements
        if (!formatted.match(/<(h[1-6]|ul|ol|p)/)) {
            formatted = `<p>${formatted}</p>`;
        }
        
        return formatted;
    }
    
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chat-message bot-message typing-message';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    clearChat() {
        const messagesContainer = document.getElementById('chat-messages');
        const welcomeTitle = (typeof QiLang !== 'undefined') ? QiLang.get('chat.welcome.title') : 'How can I help improve your space?';
        const welcomeDesc = (typeof QiLang !== 'undefined') ? QiLang.get('chat.welcome.desc') : "I'll analyze your feng shui results and provide actionable recommendations.";
        messagesContainer.innerHTML = `
            <div class="chat-welcome">
                <div class="welcome-icon">💡</div>
                <h4 data-i18n="chat.welcome.title">${welcomeTitle}</h4>
                <p data-i18n="chat.welcome.desc">${welcomeDesc}</p>
            </div>
        `;
        
        this.conversationHistory = [];
        document.getElementById('quick-actions').style.display = 'flex';
    }
}

// Initialize chatbot when DOM is ready
let fengShuiChatbot;
document.addEventListener('DOMContentLoaded', () => {
    fengShuiChatbot = new FengShuiChatbot();
    window.fengShuiChatbot = fengShuiChatbot;
});

// Export for use in other scripts
window.FengShuiChatbot = FengShuiChatbot;
