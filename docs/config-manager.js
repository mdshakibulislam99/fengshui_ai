/**
 * DeepSeek API Configuration Manager
 * Handles API key setup and testing from the frontend
 */

class DeepSeekConfigManager {
    constructor() {
        this.isConfigured = false;
        const baseUrl = window.apiBaseUrl || 'https://fengshui-ai.onrender.com';
        this.apiUrl = `${baseUrl}/api`;
        this.init();
    }
    
    async init() {
        await this.checkConfigStatus();
        this.createSettingsUI();
        this.attachEventListeners();
    }
    
    async checkConfigStatus() {
        try {
            const response = await fetch(`${this.apiUrl}/config/deepseek-status`);
            const data = await response.json();
            
            if (data.success) {
                this.isConfigured = data.data.configured;
                console.log('🔧 DeepSeek Config Status:', data.data);
                
                // Show notification if not configured
                if (!this.isConfigured) {
                    this.showConfigNotification();
                }
            }
        } catch (error) {
            console.warn('Could not check DeepSeek status:', error);
        }
    }
    
    createSettingsUI() {
        // Create settings button
        const settingsBtn = document.createElement('button');
        settingsBtn.id = 'api-settings-btn';
        settingsBtn.className = 'api-settings-btn';
        settingsBtn.title = 'API Configuration';
        settingsBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="3" fill="currentColor"/>
                <path d="M12 1V4M12 20V23M23 12H20M4 12H1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M20.485 3.515L18.364 5.636M5.636 18.364L3.515 20.485M20.485 20.485L18.364 18.364M5.636 5.636L3.515 3.515" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
        `;
        
        // Create settings modal
        const modal = document.createElement('div');
        modal.id = 'api-settings-modal';
        modal.className = 'api-settings-modal api-modal-hidden';
        modal.innerHTML = `
            <div class="api-settings-content">
                <div class="api-settings-header">
                    <h2>🔐 API Configuration</h2>
                    <button class="api-close-btn" type="button">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>
                
                <div class="api-settings-body">
                    <!-- DeepSeek Section -->
                    <div class="api-config-section">
                        <h3>DeepSeek AI Chatbot</h3>
                        <p class="api-section-desc">Configure your DeepSeek API key to enable AI-powered feng shui recommendations</p>
                        
                        <div class="api-status-indicator" id="deepseek-status">
                            <span class="status-dot"></span>
                            <span class="status-text">Checking status...</span>
                        </div>
                        
                        <div class="api-input-group">
                            <label for="deepseek-api-key">API Key</label>
                            <div class="api-input-wrapper">
                                <input 
                                    type="password" 
                                    id="deepseek-api-key" 
                                    placeholder="sk-..."
                                    class="api-input"
                                />
                                <button class="api-toggle-visibility" type="button" title="Show/Hide">
                                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                                        <circle cx="12" cy="12" r="3" fill="currentColor"/>
                                    </svg>
                                </button>
                            </div>
                            <p class="api-help-text">
                                Get your key from: <a href="https://platform.deepseek.com/api_keys" target="_blank">DeepSeek API Keys</a>
                            </p>
                        </div>
                        
                        <div class="api-button-group">
                            <button id="test-deepseek-btn" class="api-btn api-btn-secondary" type="button">
                                🧪 Test Connection
                            </button>
                            <button id="save-deepseek-btn" class="api-btn api-btn-primary" type="button">
                                💾 Save & Activate
                            </button>
                        </div>
                        
                        <div id="deepseek-test-result" class="api-test-result api-hidden"></div>
                        
                        <div class="api-pricing-info">
                            <h4>Pricing Information</h4>
                            <ul>
                                <li><strong>Free Tier:</strong> Usually $5-10 in free credits for new users</li>
                                <li><strong>Input Token:</strong> $0.14 per million tokens</li>
                                <li><strong>Output Token:</strong> $0.28 per million tokens</li>
                                <li><strong>Estimated Cost:</strong> ~$0.50-1.00 per 1000 user conversations</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="api-settings-footer">
                    <p>Your API keys are stored locally in <code>backend/.env</code>. They are never sent to our servers.</p>
                </div>
            </div>
        </div>
        `;
        
        // Add to page
        document.body.appendChild(settingsBtn);
        document.body.appendChild(modal);
        
        this.settingsBtn = settingsBtn;
        this.modal = modal;
    }
    
    attachEventListeners() {
        // Open modal
        this.settingsBtn.addEventListener('click', () => this.openModal());
        
        // Close modal
        this.modal.querySelector('.api-close-btn').addEventListener('click', () => this.closeModal());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });
        
        // Toggle visibility
        const visibilityBtn = this.modal.querySelector('.api-toggle-visibility');
        const keyInput = this.modal.querySelector('#deepseek-api-key');
        
        visibilityBtn.addEventListener('click', () => {
            const isPassword = keyInput.type === 'password';
            keyInput.type = isPassword ? 'text' : 'password';
            visibilityBtn.classList.toggle('visible');
        });
        
        // Test button
        this.modal.querySelector('#test-deepseek-btn').addEventListener('click', () => this.testDeepSeekAPI());
        
        // Save button
        this.modal.querySelector('#save-deepseek-btn').addEventListener('click', () => this.saveDeepSeekAPI());
        
        // Update status when modal opens
        this.modal.addEventListener('shown', () => this.updateStatus());
    }
    
    openModal() {
        this.modal.classList.remove('api-modal-hidden');
        this.updateStatus();
    }
    
    closeModal() {
        this.modal.classList.add('api-modal-hidden');
    }
    
    async updateStatus() {
        const statusEl = this.modal.querySelector('#deepseek-status');
        
        try {
            const response = await fetch(`${this.apiUrl}/config/deepseek-status`);
            const data = await response.json();
            
            if (data.success) {
                const status = data.data;
                const dot = statusEl.querySelector('.status-dot');
                const text = statusEl.querySelector('.status-text');
                
                if (status.configured) {
                    dot.className = 'status-dot configured';
                    text.textContent = `✓ Configured (${status.key_preview})`;
                    statusEl.className = 'api-status-indicator success';
                } else {
                    dot.className = 'status-dot not-configured';
                    text.textContent = '✗ Not Configured';
                    statusEl.className = 'api-status-indicator warning';
                }
            }
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }
    
    async testDeepSeekAPI() {
        const keyInput = this.modal.querySelector('#deepseek-api-key');
        const resultDiv = this.modal.querySelector('#deepseek-test-result');
        const testBtn = this.modal.querySelector('#test-deepseek-btn');
        
        const apiKey = keyInput.value.trim();
        
        if (!apiKey) {
            this.showTestResult('❌ Error: Please enter an API key first', 'error');
            return;
        }
        
        testBtn.disabled = true;
        testBtn.textContent = '⏳ Testing...';
        
        try {
            const response = await fetch(`${this.apiUrl}/config/test-deepseek`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showTestResult(
                    `✅ Success! API is working.\n\n${data.data.test_response}`,
                    'success'
                );
            } else {
                this.showTestResult(
                    `❌ ${data.error || 'Connection failed'}`,
                    'error'
                );
            }
        } catch (error) {
            this.showTestResult(
                `❌ Connection error: ${error.message}`,
                'error'
            );
        } finally {
            testBtn.disabled = false;
            testBtn.textContent = '🧪 Test Connection';
        }
    }
    
    async saveDeepSeekAPI() {
        const keyInput = this.modal.querySelector('#deepseek-api-key');
        const saveBtn = this.modal.querySelector('#save-deepseek-btn');
        
        const apiKey = keyInput.value.trim();
        
        if (!apiKey) {
            alert('Please enter an API key');
            return;
        }
        
        saveBtn.disabled = true;
        saveBtn.textContent = '⏳ Saving...';
        
        try {
            // In a real app, you'd have a backend endpoint to save this
            // For now, we'll just show instructions
            const instructions = `
To set up your DeepSeek API key, please follow these steps:

1. Open terminal in the project directory
2. Navigate to backend folder: cd backend
3. Run the setup script: python3 setup.py
4. Follow the prompts to enter your API key
5. The key will be saved to .env file
6. Restart your Flask server

Alternatively, manually edit backend/.env and add:
DEEPSEEK_API_KEY=${apiKey}

After setup, restart the Flask backend and reload this page.
            `;
            
            alert(instructions);
            
            // Clear the input
            keyInput.value = '';
            this.showTestResult('', '');
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = '💾 Save & Activate';
        }
    }
    
    showTestResult(message, type) {
        const resultDiv = this.modal.querySelector('#deepseek-test-result');
        
        if (!message) {
            resultDiv.classList.add('api-hidden');
            return;
        }
        
        resultDiv.className = `api-test-result ${type} api-visible`;
        resultDiv.textContent = message;
    }
    
    showConfigNotification() {
        // Show a subtle notification if API is not configured
        const notification = document.createElement('div');
        notification.className = 'api-config-notification';
        notification.innerHTML = `
            <div class="api-notification-content">
                <span>🤖 DeepSeek API not configured. Set it up to use the AI chatbot.</span>
                <button class="api-notification-btn">Configure Now</button>
            </div>
        `;
        
        notification.querySelector('.api-notification-btn').addEventListener('click', () => {
            this.openModal();
            notification.remove();
        });
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 8000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.deepSeekConfigManager = new DeepSeekConfigManager();
});
