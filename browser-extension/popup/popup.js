/**
 * Universal AI Memory Capture - Popup Interface Script
 * Handles popup functionality, settings, and quick actions
 */

class MemoryPopup {
    constructor() {
        this.apiBase = 'http://localhost:8091';
        this.isConnected = false;
        this.currentTab = null;
        this.platform = 'unknown';
        this.stats = {};
        
        this.init();
    }
    
    /**
     * Initialize popup interface
     */
    async init() {
        console.log('🧠 Memory popup initializing...');
        
        // Get current tab information
        await this.getCurrentTab();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load settings
        this.loadSettings();
        
        // Check memory service connection
        await this.checkConnection();
        
        // Update interface
        this.updateInterface();
        
        // Load statistics
        await this.loadStatistics();
        
        console.log('✅ Memory popup initialized');
    }
    
    /**
     * Get current active tab information
     */
    async getCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            this.currentTab = tab;
            this.platform = this.detectPlatform(tab.url);
            console.log(`📍 Current tab: ${this.platform} at ${tab.url}`);
        } catch (error) {
            console.error('Error getting current tab:', error);
        }
    }
    
    /**
     * Detect AI platform from URL
     */
    detectPlatform(url) {
        if (!url) return 'unknown';
        
        const hostname = new URL(url).hostname;
        
        if (hostname.includes('openai.com')) return 'chatgpt';
        if (hostname.includes('claude.ai')) return 'claude';
        if (hostname.includes('perplexity.ai')) return 'perplexity';
        if (hostname.includes('bard.google.com')) return 'bard';
        if (hostname.includes('bing.com') && url.includes('chat')) return 'bing';
        if (hostname.includes('huggingface.co')) return 'huggingface';
        
        return 'unknown';
    }
    
    /**
     * Set up event listeners for UI elements
     */
    setupEventListeners() {
        // Quick actions
        document.getElementById('capture-selection').addEventListener('click', () => this.captureSelection());
        document.getElementById('capture-page').addEventListener('click', () => this.capturePage());
        document.getElementById('quick-note').addEventListener('click', () => this.showQuickNote());
        document.getElementById('search-memories').addEventListener('click', () => this.openSearch());
        document.getElementById('copy-ai-context').addEventListener('click', () => this.copyAIContext());
        
        // Footer actions
        document.getElementById('open-dashboard').addEventListener('click', () => this.openDashboard());
        document.getElementById('view-help').addEventListener('click', () => this.openHelp());
        document.getElementById('open-settings').addEventListener('click', () => this.openSettings());
        
        // Settings checkboxes
        document.getElementById('auto-detect').addEventListener('change', (e) => this.saveSetting('autoDetect', e.target.checked));
        document.getElementById('show-notifications').addEventListener('change', (e) => this.saveSetting('showNotifications', e.target.checked));
        document.getElementById('smart-tagging').addEventListener('change', (e) => this.saveSetting('smartTagging', e.target.checked));
        
        // Quick note modal
        document.getElementById('quick-note-close').addEventListener('click', () => this.hideQuickNote());
        document.getElementById('quick-note-cancel').addEventListener('click', () => this.hideQuickNote());
        document.getElementById('quick-note-save').addEventListener('click', () => this.saveQuickNote());
        
        // Close modal on overlay click
        document.getElementById('quick-note-modal').addEventListener('click', (e) => {
            if (e.target.id === 'quick-note-modal') {
                this.hideQuickNote();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideQuickNote();
            }
        });
    }
    
    /**
     * Load settings from storage
     */
    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get({
                autoDetect: true,
                showNotifications: true,
                smartTagging: true
            });
            
            document.getElementById('auto-detect').checked = result.autoDetect;
            document.getElementById('show-notifications').checked = result.showNotifications;
            document.getElementById('smart-tagging').checked = result.smartTagging;
            
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    /**
     * Save a setting to storage
     */
    async saveSetting(key, value) {
        try {
            await chrome.storage.sync.set({ [key]: value });
            console.log(`Setting saved: ${key} = ${value}`);
        } catch (error) {
            console.error('Error saving setting:', error);
        }
    }
    
    /**
     * Check connection to memory service
     */
    async checkConnection() {
        const statusIndicator = document.getElementById('status-indicator');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');
        const statusDetails = document.getElementById('status-details');
        
        try {
            // Create timeout controller for proper fetch timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${this.apiBase}/api/health`, {
                method: 'GET',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const health = await response.json();
                
                this.isConnected = true;
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Memory service connected';
                statusDetails.innerHTML = `
                    <div>Server: ${this.apiBase}</div>
                    <div>Status: ${health.status}</div>
                    <div>Embedding: ${health.embedding_provider || 'N/A'}</div>
                `;
                
                // Enable capture actions
                document.getElementById('capture-selection').disabled = false;
                
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('Memory service connection failed:', error);
            
            this.isConnected = false;
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Memory service offline';
            statusDetails.innerHTML = `
                <div>Error: ${error.name === 'AbortError' ? 'Connection timeout' : error.message}</div>
                <div>Make sure the memory service is running at ${this.apiBase}</div>
            `;
            
            // Disable capture actions
            document.getElementById('capture-selection').disabled = true;
        }
    }
    
    /**
     * Update platform information display
     */
    updateInterface() {
        const platformIcon = document.getElementById('platform-icon');
        const platformName = document.getElementById('platform-name');
        const platformUrl = document.getElementById('platform-url');
        
        // Platform-specific data
        const platformData = {
            chatgpt: { name: 'ChatGPT', icon: '🤖', color: 'platform-chatgpt' },
            claude: { name: 'Claude', icon: '🎭', color: 'platform-claude' },
            perplexity: { name: 'Perplexity', icon: '🔍', color: 'platform-perplexity' },
            bard: { name: 'Bard', icon: '🎨', color: 'platform-bard' },
            bing: { name: 'Bing Chat', icon: '💬', color: 'platform-bing' },
            huggingface: { name: 'Hugging Face', icon: '🤗', color: 'platform-huggingface' },
            unknown: { name: 'Unknown Platform', icon: '🌐', color: 'platform-unknown' }
        };
        
        const data = platformData[this.platform] || platformData.unknown;
        
        platformIcon.textContent = data.icon;
        platformIcon.className = `platform-icon ${data.color}`;
        platformName.textContent = data.name;
        platformUrl.textContent = this.currentTab ? new URL(this.currentTab.url).hostname : 'Not detected';
        
        // Enable/disable platform-specific features
        const captureSelection = document.getElementById('capture-selection');
        if (this.platform !== 'unknown' && this.isConnected) {
            captureSelection.disabled = false;
        }
    }
    
    /**
     * Load and display statistics
     */
    async loadStatistics() {
        const totalMemories = document.getElementById('total-memories');
        const totalProjects = document.getElementById('total-projects');
        const recentCaptures = document.getElementById('recent-captures');
        
        try {
            if (!this.isConnected) {
                totalMemories.textContent = '--';
                totalProjects.textContent = '--';
                recentCaptures.textContent = '--';
                return;
            }
            
            const response = await fetch(`${this.apiBase}/api/memory/stats`);
            if (response.ok) {
                const data = await response.json();
                this.stats = data.stats;
                
                totalMemories.textContent = this.stats.overall?.total_memories || 0;
                totalProjects.textContent = this.stats.overall?.total_projects || 0;
                
                // Calculate today's captures
                const today = new Date().toISOString().split('T')[0];
                let todayCount = 0;
                
                if (this.stats.by_date && this.stats.by_date[today]) {
                    todayCount = this.stats.by_date[today];
                }
                
                recentCaptures.textContent = todayCount;
                
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('Error loading statistics:', error);
            totalMemories.textContent = '?';
            totalProjects.textContent = '?';
            recentCaptures.textContent = '?';
        }
    }
    
    /**
     * Capture selected text from current page
     */
    async captureSelection() {
        if (!this.isConnected) {
            this.showToast('❌ Memory service not connected', 'error');
            return;
        }
        
        try {
            // Execute script in current tab to get selection
            const [result] = await chrome.scripting.executeScript({
                target: { tabId: this.currentTab.id },
                function: () => {
                    const selection = window.getSelection().toString().trim();
                    return selection;
                }
            });
            
            const selectedText = result.result;
            
            if (!selectedText || selectedText.length < 10) {
                this.showToast('❌ Please select some text first', 'error');
                return;
            }
            
            // Send to content script for processing
            await chrome.tabs.sendMessage(this.currentTab.id, {
                action: 'capture-selection',
                content: selectedText
            });
            
            this.showToast('✅ Selection captured!', 'success');
            window.close();
            
        } catch (error) {
            console.error('Error capturing selection:', error);
            this.showToast(`❌ Capture failed: ${error.message}`, 'error');
        }
    }
    
    /**
     * Capture current page information
     */
    async capturePage() {
        if (!this.isConnected) {
            this.showToast('❌ Memory service not connected', 'error');
            return;
        }
        
        try {
            // Get page info
            const pageInfo = {
                title: this.currentTab.title,
                url: this.currentTab.url,
                platform: this.platform,
                timestamp: new Date().toISOString()
            };
            
            const content = `Page: ${pageInfo.title}\nURL: ${pageInfo.url}\nPlatform: ${pageInfo.platform}`;
            
            // Send directly to memory service
            const response = await fetch(`${this.apiBase}/api/memory/store`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    category: 'reference',
                    tags: [this.platform, 'page-capture'],
                    source: 'browser_extension_popup',
                    source_url: pageInfo.url,
                    metadata: pageInfo
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.showToast('✅ Page captured!', 'success');
            await this.loadStatistics();
            
        } catch (error) {
            console.error('Error capturing page:', error);
            this.showToast(`❌ Capture failed: ${error.message}`, 'error');
        }
    }
    
    /**
     * Show quick note modal
     */
    showQuickNote() {
        const modal = document.getElementById('quick-note-modal');
        const textarea = document.getElementById('quick-note-text');
        
        modal.classList.add('visible');
        textarea.focus();
    }
    
    /**
     * Hide quick note modal
     */
    hideQuickNote() {
        const modal = document.getElementById('quick-note-modal');
        modal.classList.remove('visible');
        
        // Clear form
        document.getElementById('quick-note-text').value = '';
        document.getElementById('quick-note-tags').value = '';
    }
    
    /**
     * Save quick note to memory
     */
    async saveQuickNote() {
        const content = document.getElementById('quick-note-text').value.trim();
        const tagsText = document.getElementById('quick-note-tags').value.trim();
        
        if (!content) {
            this.showToast('❌ Please enter some content', 'error');
            return;
        }
        
        if (!this.isConnected) {
            this.showToast('❌ Memory service not connected', 'error');
            return;
        }
        
        try {
            const tags = tagsText ? tagsText.split(',').map(tag => tag.trim()) : [];
            tags.push('quick-note');
            
            if (this.platform !== 'unknown') {
                tags.push(this.platform);
            }
            
            const response = await fetch(`${this.apiBase}/api/memory/store`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    category: 'note',
                    tags: tags,
                    source: 'browser_extension_popup',
                    source_url: this.currentTab?.url,
                    metadata: {
                        platform: this.platform,
                        captured_from: 'quick_note',
                        timestamp: new Date().toISOString()
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.showToast('✅ Note saved to memory!', 'success');
            this.hideQuickNote();
            await this.loadStatistics();
            
        } catch (error) {
            console.error('Error saving quick note:', error);
            this.showToast(`❌ Save failed: ${error.message}`, 'error');
        }
    }
    
    /**
     * Open memory search in new tab
     */
    openSearch() {
        chrome.tabs.create({ url: `${this.apiBase.replace('8091', '8092')}` });
        window.close();
    }
    
    /**
     * Open memory dashboard
     */
    openDashboard() {
        chrome.tabs.create({ url: `${this.apiBase.replace('8091', '8092')}` });
        window.close();
    }
    
    /**
     * Open help page
     */
    openHelp() {
        chrome.tabs.create({ url: `${this.apiBase}/docs` });
        window.close();
    }
    
    /**
     * Open extension settings
     */
    openSettings() {
        chrome.runtime.openOptionsPage();
        window.close();
    }
    
    /**
     * Copy AI context message to clipboard
     */
    async copyAIContext() {
        try {
            console.log('🤖 Generating AI context message...');
            this.showToast('🤖 Generating AI context...', 'info');
            
            // Generate the AI context message
            const contextMessage = await this.generateAIContextMessage();
            
            // Copy to clipboard
            await navigator.clipboard.writeText(contextMessage);
            
            this.showToast('✅ AI Context copied to clipboard!', 'success');
            console.log('✅ AI context copied to clipboard');
            
        } catch (error) {
            console.error('Error copying AI context:', error);
            this.showToast(`❌ Failed to copy AI context: ${error.message}`, 'error');
        }
    }
    
    /**
     * Generate comprehensive AI context message
     */
    async generateAIContextMessage() {
        // Get recent memories and stats
        const recentMemories = await this.fetchRecentMemories();
        const currentPlatform = this.getPlatformInfo();
        const memoryStats = this.stats;
        
        const message = `I'm working on the Universal AI Memory System project. Please read the AGENT.md file to understand the system architecture and development patterns.

## Project Files & Context
• **AGENT.md Location**: \`/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/AGENT.md\`
• **Project Root**: \`/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/\`
• **If you cannot access files**: This is a Universal AI Memory System (Encyclopedia Galactica for AI development) with components: Global Capture (macOS app), Memory API (FastAPI), Browser Extension, CLI tools, and GitHub integration.

## Project Context
• **System**: Universal AI Memory System (Encyclopedia Galactica for AI development)
• **Components**: Global Capture (macOS), Memory API, Browser Extension, CLI
• **Memory Stats**: ${memoryStats.totalMemories || 0} memories, ${memoryStats.recentCaptures || 0} captured today
• **Current Platform**: ${currentPlatform.name} (${currentPlatform.url})

## Quick Reference Commands
• **Build Global Capture**: \`cd global-capture && ./build.sh && cd build && ./install.sh\`
• **Start Memory API**: \`python3 src/api_service.py --port 8091\`
• **CLI Interface**: \`python3 src/memory_cli.py <command>\`
• **Health Check**: \`curl http://localhost:8091/api/health\`
• **AI Context**: \`python3 src/ai_context_generator.py --copy\`

## Recent Relevant Memories
${this.formatRecentMemories(recentMemories)}

## Browser Context
• **Current Page**: ${this.currentTab?.title || 'Unknown Page'}
• **URL**: ${this.currentTab?.url || 'N/A'}
• **AI Platform Detected**: ${currentPlatform.name}

## Architecture Summary (if AGENT.md not accessible)
This is a comprehensive memory system with:
- **Global Capture**: macOS app with ⌘⇧M hotkey for system-wide text capture
- **Memory API**: FastAPI service (localhost:8091) for storage/retrieval  
- **Browser Extension**: Chrome/Firefox extension for web content capture
- **CLI Tools**: Command-line interface for memory management
- **AGENT.md Integration**: Universal format for AI tool compatibility

Now I need help with: [DESCRIBE YOUR TASK HERE]

Please read the AGENT.md file at the path above for complete context, or use the architecture summary if file access is unavailable.`;

        return message;
    }
    
    /**
     * Fetch recent memories for context
     */
    async fetchRecentMemories() {
        try {
            const response = await fetch(`${this.apiBase}/api/search?limit=5&sort=recent`);
            if (!response.ok) throw new Error('Failed to fetch memories');
            
            const data = await response.json();
            return data.results || [];
        } catch (error) {
            console.warn('Could not fetch recent memories:', error);
            return [];
        }
    }
    
    /**
     * Get current platform information
     */
    getPlatformInfo() {
        const platformNames = {
            'chatgpt': 'ChatGPT',
            'claude': 'Claude AI',
            'perplexity': 'Perplexity AI',
            'bard': 'Google Bard',
            'bing': 'Bing Chat',
            'huggingface': 'Hugging Face',
            'unknown': 'Browser'
        };
        
        return {
            name: platformNames[this.platform] || 'Unknown Platform',
            url: this.currentTab?.url || 'N/A'
        };
    }
    
    /**
     * Format recent memories for display
     */
    formatRecentMemories(memories) {
        if (!memories || memories.length === 0) {
            return '• No recent memories found (check Memory API connection)';
        }
        
        return memories.map(memory => {
            const content = memory.content?.substring(0, 100) || 'No content';
            const tags = memory.tags?.join(', ') || 'No tags';
            return `• ${content}... [Tags: ${tags}]`;
        }).join('\n');
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 16px;
            right: 16px;
            z-index: 10000;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            transform: translateX(100%);
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto-remove
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize popup when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new MemoryPopup());
} else {
    new MemoryPopup();
}