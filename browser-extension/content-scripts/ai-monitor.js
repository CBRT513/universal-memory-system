/**
 * Universal AI Memory Capture - AI Response Monitor
 * Monitors AI chat platforms and detects valuable responses for capture
 */

class UniversalAIMonitor {
    constructor() {
        this.apiBase = 'http://localhost:8091';
        this.platform = this.detectPlatform();
        this.lastProcessedResponse = null;
        this.captureInterface = null;
        
        console.log(`🧠 Universal AI Memory Monitor initialized for ${this.platform}`);
        
        this.init();
    }
    
    /**
     * Initialize the monitoring system
     */
    init() {
        // Wait for page to fully load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startMonitoring());
        } else {
            this.startMonitoring();
        }
    }
    
    /**
     * Start monitoring AI responses on the page
     */
    startMonitoring() {
        // Create capture interface
        this.createCaptureInterface();
        
        // Start observing DOM changes for new AI responses
        this.observeAIResponses();
        
        // Add keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Test memory service connection
        this.testConnection();
        
        console.log('🎯 AI response monitoring active');
    }
    
    /**
     * Detect which AI platform we're on
     */
    detectPlatform() {
        const hostname = window.location.hostname;
        const pathname = window.location.pathname;
        
        if (hostname.includes('openai.com')) return 'chatgpt';
        if (hostname.includes('claude.ai')) return 'claude';
        if (hostname.includes('perplexity.ai')) return 'perplexity';
        if (hostname.includes('bard.google.com')) return 'bard';
        if (hostname.includes('bing.com') && pathname.includes('chat')) return 'bing';
        if (hostname.includes('huggingface.co')) return 'huggingface';
        
        return 'unknown';
    }
    
    /**
     * Create floating capture interface
     */
    createCaptureInterface() {
        // Create floating capture button
        const captureButton = document.createElement('div');
        captureButton.id = 'ai-memory-capture-btn';
        captureButton.innerHTML = `
            <div class="capture-icon">💾</div>
            <div class="capture-text">Remember</div>
        `;
        
        // Add to page
        document.body.appendChild(captureButton);
        
        // Set up event listeners
        captureButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.initiateCapture();
        });
        
        // Mouse over effects
        captureButton.addEventListener('mouseenter', () => {
            captureButton.style.transform = 'scale(1.05)';
        });
        
        captureButton.addEventListener('mouseleave', () => {
            captureButton.style.transform = 'scale(1)';
        });
        
        this.captureButton = captureButton;
        
        // Initially hidden - show when valuable content detected
        this.hideCaptureButton();
    }
    
    /**
     * Observe DOM for new AI responses
     */
    observeAIResponses() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length > 0) {
                    // Check if new content contains AI responses
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.checkForAIResponse(node);
                        }
                    });
                }
            });
        });
        
        // Observe entire document for changes
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: false
        });
        
        // Also check existing content on page load
        setTimeout(() => {
            this.checkForAIResponse(document.body);
        }, 2000);
    }
    
    /**
     * Check if element contains AI response worth capturing
     */
    checkForAIResponse(element) {
        const responses = this.findAIResponses(element);
        
        responses.forEach(response => {
            const responseText = this.extractResponseText(response);
            
            if (this.isValuableResponse(responseText)) {
                console.log('🎯 Valuable AI response detected:', responseText.substring(0, 100) + '...');
                this.highlightResponse(response);
                this.showCaptureButton();
                this.lastProcessedResponse = {
                    element: response,
                    text: responseText,
                    timestamp: new Date().toISOString()
                };
            }
        });
    }
    
    /**
     * Find AI response elements based on platform
     */
    findAIResponses(element) {
        let selectors = [];
        
        switch (this.platform) {
            case 'chatgpt':
                selectors = [
                    '[data-message-author-role="assistant"]',
                    '.group.w-full.text-gray-800.dark\\:text-gray-100.border-b',
                    '.group.w-full.text-token-text-primary'
                ];
                break;
                
            case 'claude':
                selectors = [
                    '[data-testid="message"]',
                    '.font-claude-message',
                    '.prose.max-w-none'
                ];
                break;
                
            case 'perplexity':
                selectors = [
                    '[data-testid="copilot_answer"]',
                    '.prose.prose-slate',
                    '.answer-content'
                ];
                break;
                
            case 'bard':
                selectors = [
                    '[data-test-id="conversation-turn"]',
                    '.model-response-text'
                ];
                break;
                
            default:
                // Generic selectors for unknown platforms
                selectors = [
                    '[role="assistant"]',
                    '.ai-response',
                    '.bot-message',
                    '.assistant-message',
                    'div[class*="response"]',
                    'div[class*="answer"]'
                ];
        }
        
        const responses = [];
        selectors.forEach(selector => {
            try {
                const elements = element.querySelectorAll ? 
                    element.querySelectorAll(selector) : 
                    document.querySelectorAll(selector);
                responses.push(...Array.from(elements));
            } catch (e) {
                // Ignore selector errors
            }
        });
        
        // Filter out already processed responses
        return responses.filter(el => !el.hasAttribute('data-ai-memory-processed'));
    }
    
    /**
     * Extract clean text from AI response element
     */
    extractResponseText(element) {
        // Mark as processed to avoid duplicates
        element.setAttribute('data-ai-memory-processed', 'true');
        
        // Clone element to avoid modifying original
        const clone = element.cloneNode(true);
        
        // Remove unwanted elements
        const unwanted = clone.querySelectorAll('script, style, .copy-button, .actions, [class*="button"]');
        unwanted.forEach(el => el.remove());
        
        // Get text content and clean it up
        let text = clone.textContent || clone.innerText || '';
        
        // Clean up whitespace and formatting
        text = text
            .replace(/\\s+/g, ' ')              // Multiple whitespace to single space
            .replace(/\\n\\s*\\n/g, '\\n\\n')    // Clean up line breaks
            .trim();
        
        return text;
    }
    
    /**
     * Determine if response is valuable enough to capture
     */
    isValuableResponse(text) {
        // Minimum length check
        if (text.length < 50) return false;
        
        // Already processed this exact text
        if (this.lastProcessedResponse && this.lastProcessedResponse.text === text) {
            return false;
        }
        
        const lowerText = text.toLowerCase();
        
        // High-value indicators
        const highValuePatterns = [
            '```',                           // Code blocks
            'here\\'s how',                   // Solution indicators
            'step 1', 'first,',             // Step-by-step instructions
            'solution', 'fix', 'resolve',   // Problem-solving
            'configuration', 'config',      // Configuration help
            'implementation',               // Technical implementation
            'best practice',                // Best practices
            'important to note',            // Important insights
            'key point'                     // Key insights
        ];
        
        // Check for high-value patterns
        const hasHighValue = highValuePatterns.some(pattern => 
            lowerText.includes(pattern)
        );
        
        // Medium-value indicators (require longer text)
        const mediumValuePatterns = [
            'approach', 'method', 'technique',
            'understanding', 'concept', 'principle',
            'remember that', 'keep in mind',
            'framework', 'architecture'
        ];
        
        const hasMediumValue = text.length > 150 && mediumValuePatterns.some(pattern =>
            lowerText.includes(pattern)
        );
        
        return hasHighValue || hasMediumValue;
    }
    
    /**
     * Highlight valuable response
     */
    highlightResponse(element) {
        element.style.boxShadow = '0 0 0 2px rgba(102, 126, 234, 0.3)';
        element.style.borderRadius = '8px';
        
        // Remove highlight after a few seconds
        setTimeout(() => {
            if (element.style.boxShadow.includes('rgba(102, 126, 234, 0.3)')) {
                element.style.boxShadow = '';
            }
        }, 5000);
    }
    
    /**
     * Show capture button
     */
    showCaptureButton() {
        if (this.captureButton) {
            this.captureButton.style.display = 'flex';
            this.captureButton.style.opacity = '1';
        }
    }
    
    /**
     * Hide capture button
     */
    hideCaptureButton() {
        if (this.captureButton) {
            this.captureButton.style.display = 'none';
            this.captureButton.style.opacity = '0';
        }
    }
    
    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Cmd/Ctrl + M to capture
            if ((e.metaKey || e.ctrlKey) && e.key === 'm') {
                e.preventDefault();
                this.initiateCapture();
            }
        });
    }
    
    /**
     * Test connection to memory service
     */
    async testConnection() {
        try {
            const response = await fetch(`${this.apiBase}/api/health`);
            if (response.ok) {
                console.log('✅ Memory service connection established');
                this.showConnectionStatus(true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.warn('⚠️ Memory service connection failed:', error.message);
            this.showConnectionStatus(false);
        }
    }
    
    /**
     * Show connection status to user
     */
    showConnectionStatus(connected) {
        // Create temporary status indicator
        const status = document.createElement('div');
        status.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 10000;
            padding: 10px 15px;
            border-radius: 5px;
            color: white;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: ${connected ? '#48bb78' : '#f56565'};
            transition: all 0.3s ease;
        `;
        
        status.textContent = connected ? 
            '🧠 AI Memory Capture Ready' : 
            '⚠️ Memory Service Offline';
        
        document.body.appendChild(status);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (status.parentNode) {
                status.remove();
            }
        }, 3000);
    }
    
    /**
     * Initiate capture process
     */
    initiateCapture() {
        console.log('🎯 Initiating AI response capture...');
        
        // Get selected text or last detected response
        const selection = window.getSelection().toString().trim();
        let contentToCapture = '';
        
        if (selection.length > 20) {
            contentToCapture = selection;
            console.log('📝 Capturing selected text');
        } else if (this.lastProcessedResponse) {
            contentToCapture = this.lastProcessedResponse.text;
            console.log('📝 Capturing last detected AI response');
        } else {
            this.showFeedback('❌ No content selected. Please select text or wait for AI response detection.', 'error');
            return;
        }
        
        if (contentToCapture.length < 20) {
            this.showFeedback('❌ Content too short to capture. Please select more text.', 'error');
            return;
        }
        
        // Capture the content
        this.captureContent(contentToCapture);
    }
    
    /**
     * Capture content to memory service
     */
    async captureContent(content) {
        try {
            this.showFeedback('⏳ Capturing to memory...', 'info');
            
            const response = await fetch(`${this.apiBase}/api/memory/capture-ai`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    ai_context: {
                        platform: this.platform,
                        url: window.location.href,
                        timestamp: new Date().toISOString(),
                        context_snippet: this.getContextSnippet()
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Show success feedback
            this.showFeedback(
                `✅ Captured as ${result.category}! (ID: ${result.id.slice(-8)})`, 
                'success'
            );
            
            // Log successful capture
            console.log('✅ Successfully captured:', result);
            
            // Hide capture button temporarily
            this.hideCaptureButton();
            setTimeout(() => this.showCaptureButton(), 3000);
            
        } catch (error) {
            console.error('❌ Capture failed:', error);
            this.showFeedback(`❌ Capture failed: ${error.message}`, 'error');
        }
    }
    
    /**
     * Get context snippet from surrounding conversation
     */
    getContextSnippet() {
        // Try to find previous user message for context
        const messages = document.querySelectorAll('[data-message-author-role], [data-testid="message"], .user-message, .assistant-message');
        
        if (messages.length >= 2) {
            const lastUserMessage = Array.from(messages)
                .reverse()
                .find(msg => {
                    const text = msg.textContent || '';
                    return text.length > 10 && !msg.hasAttribute('data-ai-memory-processed');
                });
            
            if (lastUserMessage) {
                const context = lastUserMessage.textContent || '';
                return context.length > 200 ? context.substring(0, 200) + '...' : context;
            }
        }
        
        return '';
    }
    
    /**
     * Show feedback to user
     */
    showFeedback(message, type = 'info') {
        // Create feedback element
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            z-index: 10001;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            background: ${type === 'success' ? '#48bb78' : 
                        type === 'error' ? '#f56565' : '#667eea'};
        `;
        
        feedback.textContent = message;
        document.body.appendChild(feedback);
        
        // Animate in
        setTimeout(() => {
            feedback.style.transform = 'translateY(0)';
            feedback.style.opacity = '1';
        }, 10);
        
        // Auto-remove after delay
        const delay = type === 'error' ? 5000 : 3000;
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.style.opacity = '0';
                feedback.style.transform = 'translateY(-20px)';
                setTimeout(() => feedback.remove(), 300);
            }
        }, delay);
    }
}

// Initialize when content script loads
if (typeof window !== 'undefined' && window.location) {
    // Small delay to ensure page is ready
    setTimeout(() => {
        window.aiMemoryMonitor = new UniversalAIMonitor();
    }, 1000);
}