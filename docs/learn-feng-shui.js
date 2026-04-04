(function () {
    // Chapter navigation
    var chapterButtons = Array.from(document.querySelectorAll('.chapter-btn'));
    var chapterContents = Array.from(document.querySelectorAll('.chapter-content'));

    function openChapter(chapterId) {
        chapterButtons.forEach(function (btn) {
            var isActive = btn.getAttribute('data-chapter') === chapterId;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', String(isActive));
        });

        chapterContents.forEach(function (content) {
            var isActive = content.id === chapterId;
            content.classList.toggle('active', isActive);
            content.hidden = !isActive;
        });
    }

    chapterButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            openChapter(btn.getAttribute('data-chapter'));
        });
    });

    // Embed chatbot in the right panel
    function embedChatbot() {
        // Wait for chatbot to be initialized
        var checkChatbot = setInterval(function () {
            var chatbotContainer = document.getElementById('fengshui-chatbot');
            if (chatbotContainer) {
                clearInterval(checkChatbot);
                
                // Move chatbot into the embedded container
                var embedContainer = document.getElementById('learnChatbotContainer');
                if (embedContainer) {
                    embedContainer.appendChild(chatbotContainer);
                    
                    // Auto-open the chat window
                    var chatWindow = document.getElementById('chat-window');
                    if (chatWindow) {
                        chatWindow.classList.remove('chat-hidden');
                    }
                    
                    // Update welcome message for learning context
                    setTimeout(function() {
                        var welcomeEl = document.querySelector('.chat-welcome');
                        if (welcomeEl) {
                            welcomeEl.innerHTML = `
                                <div class="welcome-icon">💡</div>
                                <h4>Learn Feng Shui with AI</h4>
                                <p>Ask me anything about the chapters, room setups, or how to apply Feng Shui principles.</p>
                            `;
                        }
                        
                        // Update quick action buttons for learning context
                        var quickActions = document.getElementById('quick-actions');
                        if (quickActions) {
                            quickActions.innerHTML = `
                                <button class="quick-action-btn" data-action="yin-yang">
                                    ☯️ Explain Yin and Yang
                                </button>
                                <button class="quick-action-btn" data-action="elements">
                                    🌿 Five Elements basics
                                </button>
                                <button class="quick-action-btn" data-action="beginner">
                                    🎯 Where should I start?
                                </button>
                            `;
                            
                            // Re-attach click handlers
                            quickActions.querySelectorAll('.quick-action-btn').forEach(function(btn) {
                                btn.addEventListener('click', function() {
                                    var action = btn.getAttribute('data-action');
                                    var query = '';
                                    switch(action) {
                                        case 'yin-yang':
                                            query = 'Explain Yin and Yang balance in simple terms for beginners.';
                                            break;
                                        case 'elements':
                                            query = 'What are the five elements in Feng Shui and how do I use them?';
                                            break;
                                        case 'beginner':
                                            query = 'I am new to Feng Shui. Where should I start and what is the most important thing to learn first?';
                                            break;
                                    }
                                    
                                    if (query && window.fengShuiChatbot) {
                                        var input = document.getElementById('chat-input');
                                        if (input) {
                                            input.value = query;
                                            window.fengShuiChatbot.sendMessage();
                                        }
                                    }
                                });
                            });
                        }
                    }, 100);
                }
            }
        }, 100);
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', embedChatbot);
    } else {
        embedChatbot();
    }
})();
