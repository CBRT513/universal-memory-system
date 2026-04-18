/**
 * Universal AI Memory Browser Capture
 * Bookmarklet for capturing insights from any AI platform
 */

(function() {
    'use strict';
    
    const MEMORY_API_URL = 'http://localhost:8091';
    
    // AI Platform Detection
    const detectAIPlatform = () => {
        const hostname = window.location.hostname;
        const url = window.location.href;
        
        if (hostname.includes('chat.openai.com')) {
            return { name: 'ChatGPT', platform: 'chatgpt' };
        } else if (hostname.includes('claude.ai')) {
            return { name: 'Claude', platform: 'claude' };
        } else if (hostname.includes('bard.google.com') || hostname.includes('gemini.google.com')) {
            return { name: 'Google Bard/Gemini', platform: 'bard' };
        } else if (hostname.includes('bing.com') && url.includes('chat')) {
            return { name: 'Bing Chat', platform: 'bing' };
        } else if (hostname.includes('perplexity.ai')) {
            return { name: 'Perplexity', platform: 'perplexity' };
        } else if (hostname.includes('poe.com')) {
            return { name: 'Poe', platform: 'poe' };
        } else if (hostname.includes('character.ai')) {
            return { name: 'Character.AI', platform: 'character' };
        } else if (hostname.includes('huggingface.co')) {
            return { name: 'Hugging Face', platform: 'huggingface' };
        }
        
        return { name: 'Unknown', platform: 'unknown' };
    };
    
    // Smart Content Extraction
    const extractContent = () => {
        const selection = window.getSelection().toString().trim();
        if (selection && selection.length > 10) {
            return selection;
        }
        
        // Platform-specific content extraction
        const platform = detectAIPlatform().platform;
        let content = '';
        
        switch (platform) {
            case 'chatgpt':
                // Try to get the last assistant message
                const chatgptMessages = document.querySelectorAll('[data-message-author-role="assistant"]');
                if (chatgptMessages.length > 0) {
                    const lastMessage = chatgptMessages[chatgptMessages.length - 1];
                    content = lastMessage.innerText;
                }
                break;
                
            case 'claude':
                // Claude's message structure
                const claudeMessages = document.querySelectorAll('.font-claude-message');
                if (claudeMessages.length > 0) {
                    const lastMessage = claudeMessages[claudeMessages.length - 1];
                    content = lastMessage.innerText;
                }
                break;
                
            case 'bard':
                // Google Bard structure
                const bardMessages = document.querySelectorAll('[data-test-id*="response"]');
                if (bardMessages.length > 0) {
                    const lastMessage = bardMessages[bardMessages.length - 1];
                    content = lastMessage.innerText;
                }
                break;
                
            case 'bing':
                // Bing Chat structure
                const bingMessages = document.querySelectorAll('.ac-textBlock');
                if (bingMessages.length > 0) {
                    const lastMessage = bingMessages[bingMessages.length - 1];
                    content = lastMessage.innerText;
                }
                break;
                
            default:
                // Generic extraction - look for common patterns
                const candidates = [
                    // Try common message selectors
                    document.querySelector('.message-content'),
                    document.querySelector('.response'),
                    document.querySelector('.answer'),
                    document.querySelector('.output'),
                    // Fallback to body text
                    document.querySelector('main'),
                    document.querySelector('.content'),
                    document.body
                ];
                
                for (const candidate of candidates) {
                    if (candidate && candidate.innerText.length > 50) {
                        content = candidate.innerText.slice(0, 2000);
                        break;
                    }
                }
        }
        
        return content.slice(0, 2000) || 'No content could be extracted';
    };
    
    // Auto-tag generation based on content and platform
    const generateAutoTags = (content, platform) => {
        const tags = [platform];
        const contentLower = content.toLowerCase();
        
        // Technical keywords
        const techKeywords = {
            'javascript': 'javascript', 'js': 'javascript', 'node': 'javascript',
            'python': 'python', 'py': 'python', 'django': 'python', 'flask': 'python',
            'react': 'react', 'vue': 'vue', 'angular': 'angular',
            'database': 'database', 'sql': 'sql', 'postgres': 'postgresql', 'mysql': 'mysql',
            'api': 'api', 'rest': 'api', 'graphql': 'graphql',
            'css': 'css', 'html': 'html', 'styling': 'css',
            'auth': 'authentication', 'login': 'authentication', 'jwt': 'authentication',
            'performance': 'performance', 'optimization': 'optimization', 'speed': 'performance',
            'security': 'security', 'bug': 'debugging', 'error': 'debugging',
            'test': 'testing', 'testing': 'testing', 'unit': 'testing',
            'docker': 'docker', 'kubernetes': 'kubernetes', 'k8s': 'kubernetes',
            'aws': 'aws', 'cloud': 'cloud', 'azure': 'azure', 'gcp': 'gcp'
        };
        
        for (const [keyword, tag] of Object.entries(techKeywords)) {
            if (contentLower.includes(keyword) && !tags.includes(tag)) {
                tags.push(tag);
                if (tags.length >= 6) break; // Limit tags
            }
        }
        
        return tags;
    };
    
    // Auto-categorize content
    const categorizeContent = (content) => {
        const contentLower = content.toLowerCase();
        
        if (contentLower.includes('solution') || contentLower.includes('fix') || 
            contentLower.includes('resolved') || contentLower.includes('works')) {
            return 'solution';
        } else if (contentLower.includes('pattern') || contentLower.includes('approach') ||
                  contentLower.includes('method') || contentLower.includes('technique')) {
            return 'pattern';
        } else if (contentLower.includes('decided') || contentLower.includes('choice') ||
                  contentLower.includes('selected') || contentLower.includes('architecture')) {
            return 'decision';
        } else if (contentLower.includes('reference') || contentLower.includes('documentation') ||
                  contentLower.includes('link') || contentLower.includes('resource')) {
            return 'reference';
        }
        
        return 'insight';
    };
    
    // Estimate importance based on content characteristics
    const estimateImportance = (content, platform) => {
        let importance = 5; // Base importance
        
        const contentLower = content.toLowerCase();
        const length = content.length;
        
        // Length-based adjustment
        if (length > 500) importance += 1;
        if (length > 1000) importance += 1;
        
        // Keyword-based importance boost
        const highValueKeywords = [
            'critical', 'important', 'key', 'essential', 'crucial',
            'performance', 'security', 'optimization', 'solution',
            'working', 'fixed', 'resolved', 'breakthrough'
        ];
        
        for (const keyword of highValueKeywords) {
            if (contentLower.includes(keyword)) {
                importance += 1;
                break;
            }
        }
        
        // Platform-based adjustment
        if (platform === 'chatgpt' || platform === 'claude') {
            importance += 1; // Premium AI platforms often have higher quality
        }
        
        // Cap at 10
        return Math.min(importance, 10);
    };
    
    // Main capture interface
    const createCaptureInterface = () => {
        // Remove existing interface if present
        const existing = document.getElementById('memory-capture-interface');
        if (existing) {
            existing.remove();
        }
        
        const platform = detectAIPlatform();
        const content = extractContent();
        const autoTags = generateAutoTags(content, platform.platform);
        const category = categorizeContent(content);
        const importance = estimateImportance(content, platform.platform);
        
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.id = 'memory-capture-interface';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            z-index: 999999;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        
        // Create modal content
        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            position: relative;
        `;
        
        modal.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e2e8f0;">
                <div style="font-size: 24px;">🧠</div>
                <div>
                    <h2 style="margin: 0; color: #2d3748; font-size: 1.5rem;">Capture AI Memory</h2>
                    <p style="margin: 5px 0 0 0; color: #718096; font-size: 0.9rem;">From ${platform.name}</p>
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2d3748;">Content to Remember:</label>
                <textarea id="memory-content" style="width: 100%; height: 120px; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 14px; line-height: 1.5; resize: vertical; font-family: inherit;" placeholder="What would you like to remember?">${content}</textarea>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2d3748;">Category:</label>
                    <select id="memory-category" style="width: 100%; padding: 10px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 14px;">
                        <option value="solution" ${category === 'solution' ? 'selected' : ''}>Solution</option>
                        <option value="pattern" ${category === 'pattern' ? 'selected' : ''}>Pattern</option>
                        <option value="decision" ${category === 'decision' ? 'selected' : ''}>Decision</option>
                        <option value="insight" ${category === 'insight' ? 'selected' : ''}>Insight</option>
                        <option value="reference" ${category === 'reference' ? 'selected' : ''}>Reference</option>
                    </select>
                </div>
                
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2d3748;">Status:</label>
                    <select id="memory-status" style="width: 100%; padding: 10px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 14px;">
                        <option value="active">Active</option>
                        <option value="working">Working (Protected)</option>
                        <option value="testing">Testing</option>
                        <option value="failed">Failed</option>
                    </select>
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2d3748;">Tags (comma-separated):</label>
                <input type="text" id="memory-tags" style="width: 100%; padding: 10px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 14px;" placeholder="ai, solution, optimization" value="${autoTags.join(', ')}">
            </div>
            
            <div style="margin-bottom: 25px;">
                <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2d3748;">Importance (1-10): <span id="importance-display">${importance}</span></label>
                <input type="range" id="memory-importance" min="1" max="10" value="${importance}" style="width: 100%; margin-bottom: 5px;" oninput="document.getElementById('importance-display').textContent = this.value">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #718096;">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button id="cancel-capture" style="padding: 12px 24px; background: #e2e8f0; color: #4a5568; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                    Cancel
                </button>
                <button id="save-memory" style="padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; position: relative;">
                    Save Memory
                </button>
            </div>
            
            <div id="capture-status" style="margin-top: 15px; padding: 10px; border-radius: 8px; display: none;"></div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Event handlers
        document.getElementById('cancel-capture').onclick = () => {
            overlay.remove();
        };
        
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        };
        
        document.getElementById('save-memory').onclick = async () => {
            const saveButton = document.getElementById('save-memory');
            const statusDiv = document.getElementById('capture-status');
            
            // Disable button and show loading
            saveButton.style.opacity = '0.7';
            saveButton.style.cursor = 'not-allowed';
            saveButton.innerHTML = 'Saving...';
            
            const memoryData = {
                content: document.getElementById('memory-content').value.trim(),
                category: document.getElementById('memory-category').value,
                status: document.getElementById('memory-status').value,
                tags: document.getElementById('memory-tags').value
                    .split(',')
                    .map(tag => tag.trim())
                    .filter(tag => tag.length > 0),
                importance: parseInt(document.getElementById('memory-importance').value),
                source: platform.platform,
                source_url: window.location.href,
                metadata: {
                    page_title: document.title,
                    platform_name: platform.name,
                    capture_timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent.split(' ')[0] // Browser info
                }
            };
            
            if (!memoryData.content) {
                statusDiv.style.cssText = 'display: block; background: #fed7d7; border: 1px solid #fc8181; color: #742a2a;';
                statusDiv.textContent = 'Please enter some content to remember.';
                
                // Re-enable button
                saveButton.style.opacity = '1';
                saveButton.style.cursor = 'pointer';
                saveButton.innerHTML = 'Save Memory';
                return;
            }
            
            try {
                const response = await fetch(`${MEMORY_API_URL}/api/memory/store`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(memoryData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    
                    if (result.status === 'stored') {
                        statusDiv.style.cssText = 'display: block; background: #c6f6d5; border: 1px solid #48bb78; color: #22543d;';
                        statusDiv.innerHTML = `
                            ✅ <strong>Memory saved successfully!</strong><br>
                            ID: ${result.id}<br>
                            Project: ${result.project || 'General'}
                        `;
                    } else if (result.status === 'duplicate') {
                        statusDiv.style.cssText = 'display: block; background: #feebc8; border: 1px solid #ed8936; color: #744210;';
                        statusDiv.innerHTML = `⚠️ <strong>Duplicate detected</strong><br>Memory already exists (ID: ${result.id})`;
                    }
                    
                    // Auto-close after success
                    setTimeout(() => {
                        overlay.remove();
                    }, 2500);
                    
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
            } catch (error) {
                console.error('Memory capture error:', error);
                
                let errorMessage = 'Failed to save memory. ';
                
                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    errorMessage += 'Memory service not running. Start with:<br><code style="background: #2d3748; color: #a0aec0; padding: 2px 4px; border-radius: 3px;">./start-memory-service.sh</code>';
                } else {
                    errorMessage += `Error: ${error.message}`;
                }
                
                statusDiv.style.cssText = 'display: block; background: #fed7d7; border: 1px solid #fc8181; color: #742a2a;';
                statusDiv.innerHTML = `❌ ${errorMessage}`;
            } finally {
                // Re-enable button
                saveButton.style.opacity = '1';
                saveButton.style.cursor = 'pointer';
                saveButton.innerHTML = 'Save Memory';
            }
        };
        
        // Focus on content area
        document.getElementById('memory-content').focus();
        
        // Auto-resize textarea
        const textarea = document.getElementById('memory-content');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    };
    
    // Quick capture function (for minimal UI)
    const quickCapture = async (content, options = {}) => {
        const platform = detectAIPlatform();
        const autoTags = generateAutoTags(content, platform.platform);
        
        const memoryData = {
            content: content,
            category: options.category || categorizeContent(content),
            status: options.status || 'active',
            tags: options.tags || autoTags,
            importance: options.importance || estimateImportance(content, platform.platform),
            source: platform.platform,
            source_url: window.location.href,
            metadata: {
                page_title: document.title,
                platform_name: platform.name,
                capture_timestamp: new Date().toISOString(),
                quick_capture: true
            }
        };
        
        try {
            const response = await fetch(`${MEMORY_API_URL}/api/memory/store`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(memoryData)
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Show brief notification
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${result.status === 'stored' ? '#48bb78' : '#ed8936'};
                    color: white;
                    padding: 15px 20px;
                    border-radius: 10px;
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-weight: 600;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                `;
                notification.textContent = result.status === 'stored' ? 
                    '✅ Memory saved!' : 
                    '⚠️ Duplicate detected';
                
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.remove();
                }, 3000);
                
                return result;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Quick capture error:', error);
            
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #f56565;
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                z-index: 999999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-weight: 600;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            `;
            notification.textContent = '❌ Failed to save memory';
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
            
            throw error;
        }
    };
    
    // Check if there's selected text for quick capture
    const selectedText = window.getSelection().toString().trim();
    
    if (selectedText.length > 50) {
        // Show quick capture option
        if (confirm(`Quick capture selected text to memory?\n\n"${selectedText.slice(0, 100)}${selectedText.length > 100 ? '...' : '"}"`)) {
            quickCapture(selectedText);
        } else {
            createCaptureInterface();
        }
    } else {
        // Show full interface
        createCaptureInterface();
    }
    
    // Make functions globally accessible for debugging
    window.memoryCapture = {
        detectAIPlatform,
        extractContent,
        createCaptureInterface,
        quickCapture
    };
    
})();