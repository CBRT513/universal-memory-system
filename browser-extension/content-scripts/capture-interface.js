/**
 * Universal AI Memory Capture - Enhanced Interface
 * Provides rich capture modal with tagging, categorization, and editing
 */

class AICaptureInterface {
    constructor(monitor) {
        this.monitor = monitor;
        this.modal = null;
        this.currentContent = '';
        this.suggestedTags = [];
        this.suggestedCategory = 'insight';
        this.suggestedImportance = 6;
        
        this.setupModal();
        this.setupEventListeners();
    }
    
    /**
     * Create the capture modal interface
     */
    setupModal() {
        // Create modal container
        this.modal = document.createElement('div');
        this.modal.className = 'ai-memory-modal';
        this.modal.innerHTML = `
            <div class="ai-memory-modal-content">
                <div class="ai-memory-modal-header">
                    <h3 class="ai-memory-modal-title">
                        🧠 Capture AI Insight
                    </h3>
                    <button class="ai-memory-modal-close" type="button">×</button>
                </div>
                
                <div class="ai-memory-modal-body">
                    <!-- Content Preview -->
                    <div class="ai-memory-preview">
                        <div class="ai-memory-preview-label">Content to Capture:</div>
                        <div class="ai-memory-preview-content" id="capture-content-preview">
                            <!-- Preview text will be inserted here -->
                        </div>
                    </div>
                    
                    <!-- Capture Form -->
                    <form id="ai-memory-capture-form">
                        <!-- Article Checkbox -->
                        <div class="ai-memory-form-group ai-memory-article-section">
                            <label class="ai-memory-checkbox-label">
                                <input type="checkbox" id="capture-is-article" checked>
                                <span>📰 This is an article</span>
                            </label>
                            <div class="ai-memory-article-subcategory" id="article-subcategory" style="margin-top: 10px;">
                                <label class="ai-memory-form-label">Article Type:</label>
                                <select class="ai-memory-form-select" id="article-type" name="article-type">
                                    <option value="action-required">🚀 Action Required - Needs implementation</option>
                                    <option value="reference">📚 Reference - Keep for future</option>
                                    <option value="learning">🎓 Learning - Educational content</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Category Selection (for non-articles) -->
                        <div class="ai-memory-form-group" id="category-section" style="display: none;">
                            <label class="ai-memory-form-label" for="capture-category">Category</label>
                            <select class="ai-memory-form-select" id="capture-category" name="category">
                                <option value="insight">💡 Insight</option>
                                <option value="solution">🔧 Solution</option>
                                <option value="code">💻 Code</option>
                                <option value="pattern">🎨 Pattern</option>
                                <option value="configuration">⚙️ Configuration</option>
                                <option value="documentation">📚 Documentation</option>
                                <option value="debugging">🐛 Debugging</option>
                                <option value="performance">⚡ Performance</option>
                            </select>
                        </div>
                        
                        <!-- Tags Input -->
                        <div class="ai-memory-form-group">
                            <label class="ai-memory-form-label" for="capture-tags">Tags</label>
                            <div class="ai-memory-tags-input" id="capture-tags-container">
                                <input type="text" id="capture-tags-input" placeholder="Add tags (press Enter)" />
                            </div>
                            <div class="ai-memory-suggested-tags" id="suggested-tags" style="margin-top: 8px;">
                                <!-- Suggested tags will appear here -->
                            </div>
                        </div>
                        
                        <!-- Importance Slider -->
                        <div class="ai-memory-form-group">
                            <label class="ai-memory-form-label" for="capture-importance">Importance Level: <span id="importance-value">6</span>/10</label>
                            <input type="range" class="ai-memory-importance-slider" id="capture-importance" 
                                   min="1" max="10" value="6" step="1" />
                            <div class="ai-memory-importance-labels">
                                <span class="ai-memory-importance-label">Low</span>
                                <span class="ai-memory-importance-label">Medium</span>
                                <span class="ai-memory-importance-label">High</span>
                                <span class="ai-memory-importance-label">Critical</span>
                            </div>
                        </div>
                        
                        <!-- Content Editor -->
                        <div class="ai-memory-form-group">
                            <label class="ai-memory-form-label" for="capture-content">Edit Content (Optional)</label>
                            <textarea class="ai-memory-form-textarea" id="capture-content" 
                                      placeholder="Edit the content if needed..." rows="4"></textarea>
                        </div>
                        
                        <!-- Form Actions -->
                        <div class="ai-memory-form-actions">
                            <button type="button" class="ai-memory-btn ai-memory-btn-secondary" id="capture-cancel">
                                Cancel
                            </button>
                            <button type="submit" class="ai-memory-btn ai-memory-btn-primary" id="capture-submit">
                                💾 Save to Memory
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
    }
    
    /**
     * Set up event listeners for the modal
     */
    setupEventListeners() {
        // Close modal handlers
        const closeBtn = this.modal.querySelector('.ai-memory-modal-close');
        const cancelBtn = this.modal.querySelector('#capture-cancel');
        
        closeBtn.addEventListener('click', () => this.hideModal());
        cancelBtn.addEventListener('click', () => this.hideModal());
        
        // Click outside to close
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hideModal();
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('visible')) {
                this.hideModal();
            }
        });
        
        // Form submission
        const form = this.modal.querySelector('#ai-memory-capture-form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Tags input handling
        this.setupTagsInput();
        
        // Importance slider
        const importanceSlider = this.modal.querySelector('#capture-importance');
        const importanceValue = this.modal.querySelector('#importance-value');
        
        importanceSlider.addEventListener('input', (e) => {
            importanceValue.textContent = e.target.value;
        });
        
        // Article checkbox handling
        const articleCheckbox = this.modal.querySelector('#capture-is-article');
        const articleSubcategory = this.modal.querySelector('#article-subcategory');
        const categorySection = this.modal.querySelector('#category-section');
        
        articleCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                // Show article subcategory, hide regular category
                articleSubcategory.style.display = 'block';
                categorySection.style.display = 'none';
            } else {
                // Hide article subcategory, show regular category
                articleSubcategory.style.display = 'none';
                categorySection.style.display = 'block';
            }
        });
        
        // Auto-resize textarea
        const textarea = this.modal.querySelector('#capture-content');
        textarea.addEventListener('input', this.autoResizeTextarea);
    }
    
    /**
     * Set up the tags input system
     */
    setupTagsInput() {
        const container = this.modal.querySelector('#capture-tags-container');
        const input = this.modal.querySelector('#capture-tags-input');
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                this.addTag(input.value.trim());
                input.value = '';
            } else if (e.key === 'Backspace' && input.value === '') {
                // Remove last tag on backspace
                this.removeLastTag();
            }
        });
        
        input.addEventListener('blur', () => {
            if (input.value.trim()) {
                this.addTag(input.value.trim());
                input.value = '';
            }
        });
    }
    
    /**
     * Add a tag to the current selection
     */
    addTag(tagText) {
        if (!tagText || this.getTags().includes(tagText.toLowerCase())) {
            return;
        }
        
        const container = this.modal.querySelector('#capture-tags-container');
        const input = this.modal.querySelector('#capture-tags-input');
        
        const tag = document.createElement('div');
        tag.className = 'ai-memory-tag';
        tag.innerHTML = `
            ${tagText}
            <button type="button" class="ai-memory-tag-remove">×</button>
        `;
        
        // Add remove handler
        tag.querySelector('.ai-memory-tag-remove').addEventListener('click', () => {
            tag.remove();
        });
        
        container.insertBefore(tag, input);
    }
    
    /**
     * Remove the last tag
     */
    removeLastTag() {
        const tags = this.modal.querySelectorAll('.ai-memory-tag');
        if (tags.length > 0) {
            tags[tags.length - 1].remove();
        }
    }
    
    /**
     * Get current tags as array
     */
    getTags() {
        const tagElements = this.modal.querySelectorAll('.ai-memory-tag');
        return Array.from(tagElements).map(tag => 
            tag.textContent.replace('×', '').trim().toLowerCase()
        );
    }
    
    /**
     * Auto-resize textarea based on content
     */
    autoResizeTextarea(event) {
        const textarea = event.target;
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(60, textarea.scrollHeight) + 'px';
    }
    
    /**
     * Show the capture modal with content
     */
    showModal(content, suggestedData = {}) {
        this.currentContent = content;
        this.suggestedTags = suggestedData.tags || [];
        this.suggestedCategory = suggestedData.category || 'insight';
        this.suggestedImportance = suggestedData.importance || 6;
        
        // Populate preview
        const preview = this.modal.querySelector('#capture-content-preview');
        preview.textContent = content.length > 300 ? 
            content.substring(0, 300) + '...' : content;
        
        // Set suggested values
        const categorySelect = this.modal.querySelector('#capture-category');
        categorySelect.value = this.suggestedCategory;
        
        const importanceSlider = this.modal.querySelector('#capture-importance');
        const importanceValue = this.modal.querySelector('#importance-value');
        importanceSlider.value = this.suggestedImportance;
        importanceValue.textContent = this.suggestedImportance;
        
        const contentTextarea = this.modal.querySelector('#capture-content');
        contentTextarea.value = content;
        
        // Clear existing tags
        this.modal.querySelectorAll('.ai-memory-tag').forEach(tag => tag.remove());
        
        // Add suggested tags
        this.suggestedTags.forEach(tag => this.addTag(tag));
        
        // Show suggested tags for selection
        this.renderSuggestedTags();
        
        // Show modal
        this.modal.classList.add('visible');
        
        // Focus on first input
        setTimeout(() => {
            this.modal.querySelector('#capture-tags-input').focus();
        }, 100);
    }
    
    /**
     * Render suggested tags for easy selection
     */
    renderSuggestedTags() {
        const container = this.modal.querySelector('#suggested-tags');
        
        // Get additional suggested tags based on content analysis
        const additionalTags = this.analyzeTags(this.currentContent);
        const currentTags = this.getTags();
        
        // Filter out already selected tags
        const availableTags = additionalTags.filter(tag => 
            !currentTags.includes(tag.toLowerCase())
        );
        
        if (availableTags.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        const html = availableTags.slice(0, 6).map(tag => 
            `<span class="ai-memory-suggested-tag" data-tag="${tag}">${tag}</span>`
        ).join(' ');
        
        container.innerHTML = `
            <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">Suggested:</div>
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                ${html}
            </div>
        `;
        
        // Add click handlers for suggested tags
        container.querySelectorAll('.ai-memory-suggested-tag').forEach(tagBtn => {
            tagBtn.style.cssText = `
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 2px 8px;
                font-size: 11px;
                cursor: pointer;
                transition: all 0.2s ease;
            `;
            
            tagBtn.addEventListener('click', () => {
                this.addTag(tagBtn.dataset.tag);
                tagBtn.remove();
            });
            
            tagBtn.addEventListener('mouseenter', () => {
                tagBtn.style.background = '#e5e7eb';
                tagBtn.style.borderColor = '#9ca3af';
            });
            
            tagBtn.addEventListener('mouseleave', () => {
                tagBtn.style.background = '#f3f4f6';
                tagBtn.style.borderColor = '#d1d5db';
            });
        });
    }
    
    /**
     * Analyze content to suggest relevant tags
     */
    analyzeTags(content) {
        const tags = [];
        const contentLower = content.toLowerCase();
        
        // Technology tags
        const techMap = {
            'react': ['react', 'jsx', 'component', 'hook', 'usestate', 'useeffect'],
            'vue': ['vue', 'vuejs', 'composition api'],
            'angular': ['angular', 'typescript', 'rxjs'],
            'python': ['python', 'def ', 'import ', 'pip install'],
            'javascript': ['javascript', 'js', 'const ', 'let ', 'function'],
            'typescript': ['typescript', 'ts', 'interface', 'type '],
            'css': ['css', 'style', 'flexbox', 'grid'],
            'html': ['html', 'dom', 'element', 'attribute'],
            'node': ['node', 'nodejs', 'npm', 'express'],
            'database': ['database', 'sql', 'query', 'table'],
            'mongodb': ['mongodb', 'mongoose', 'collection'],
            'postgresql': ['postgresql', 'postgres', 'pg'],
            'mysql': ['mysql', 'mariadb'],
            'redis': ['redis', 'cache', 'session'],
            'docker': ['docker', 'container', 'dockerfile'],
            'kubernetes': ['kubernetes', 'k8s', 'pod', 'deployment'],
            'aws': ['aws', 'ec2', 's3', 'lambda'],
            'git': ['git', 'commit', 'branch', 'merge'],
            'testing': ['test', 'testing', 'jest', 'cypress', 'unit test'],
            'api': ['api', 'endpoint', 'rest', 'graphql'],
            'authentication': ['auth', 'authentication', 'jwt', 'oauth', 'login'],
            'security': ['security', 'encryption', 'ssl', 'https'],
            'performance': ['performance', 'optimization', 'speed', 'cache'],
            'deployment': ['deploy', 'deployment', 'production', 'ci/cd'],
            'debugging': ['debug', 'error', 'bug', 'fix', 'troubleshoot']
        };
        
        for (const [tag, keywords] of Object.entries(techMap)) {
            if (keywords.some(keyword => contentLower.includes(keyword))) {
                tags.push(tag);
            }
        }
        
        // Context-based tags
        if (contentLower.includes('error') || contentLower.includes('fix')) {
            tags.push('debugging');
        }
        
        if (contentLower.includes('optimize') || contentLower.includes('performance')) {
            tags.push('optimization');
        }
        
        if (contentLower.includes('config') || contentLower.includes('setup')) {
            tags.push('configuration');
        }
        
        if (content.includes('```')) {
            tags.push('code-example');
        }
        
        // Platform-specific tags
        const platform = this.monitor.platform;
        if (platform !== 'unknown') {
            tags.push(platform);
        }
        
        return [...new Set(tags)]; // Remove duplicates
    }
    
    /**
     * Hide the capture modal
     */
    hideModal() {
        this.modal.classList.remove('visible');
    }
    
    /**
     * Handle form submission
     */
    async handleSubmit(event) {
        event.preventDefault();
        
        const submitBtn = this.modal.querySelector('#capture-submit');
        const originalText = submitBtn.textContent;
        
        try {
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.textContent = '💾 Saving...';
            
            // Get form data
            const formData = this.getFormData();
            
            // Validate
            if (!formData.content || formData.content.trim().length < 10) {
                throw new Error('Content too short. Please provide more meaningful content.');
            }
            
            // Capture to memory service
            const result = await this.captureToMemory(formData);
            
            // Show success
            this.showToast(`✅ Captured as ${result.category}! (ID: ${result.id.slice(-8)})`, 'success');
            
            // Hide modal
            this.hideModal();
            
            // Hide capture button temporarily
            if (this.monitor.captureButton) {
                this.monitor.captureButton.style.display = 'none';
                setTimeout(() => {
                    if (this.monitor.captureButton) {
                        this.monitor.captureButton.style.display = 'flex';
                    }
                }, 3000);
            }
            
        } catch (error) {
            console.error('Capture submission error:', error);
            this.showToast(`❌ Capture failed: ${error.message}`, 'error');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
    
    /**
     * Get form data from modal
     */
    getFormData() {
        const isArticle = this.modal.querySelector('#capture-is-article').checked;
        const importance = parseInt(this.modal.querySelector('#capture-importance').value);
        const content = this.modal.querySelector('#capture-content').value.trim();
        const tags = this.getTags();
        
        let category, articleType;
        
        if (isArticle) {
            category = 'article';
            articleType = this.modal.querySelector('#article-type').value;
            
            // Add article type as a tag
            if (articleType === 'action-required') {
                tags.push('actionable');
                tags.push('implement-now');
            } else if (articleType === 'reference') {
                tags.push('reference');
                tags.push('keep-for-later');
            } else if (articleType === 'learning') {
                tags.push('learning');
                tags.push('educational');
            }
        } else {
            category = this.modal.querySelector('#capture-category').value;
        }
        
        return {
            content,
            category,
            importance,
            tags,
            isArticle,
            articleType
        };
    }
    
    /**
     * Capture content to memory service
     */
    async captureToMemory(formData) {
        const response = await fetch(`${this.monitor.apiBase}/api/memory/capture-ai`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: formData.content,
                ai_context: {
                    platform: this.monitor.platform,
                    url: window.location.href,
                    timestamp: new Date().toISOString(),
                    context_snippet: this.monitor.getContextSnippet(),
                    user_category: formData.category,
                    user_importance: formData.importance,
                    user_tags: formData.tags
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.ai-memory-toast').forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = `ai-memory-toast ${type}`;
        toast.innerHTML = `<div class="ai-memory-toast-message">${message}</div>`;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('visible');
        }, 10);
        
        // Auto-remove
        const delay = type === 'error' ? 5000 : 3000;
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, delay);
    }
    
    /**
     * Handle quick capture (without modal)
     */
    async quickCapture(content, options = {}) {
        try {
            this.showToast('⏳ Quick capturing...', 'info');
            
            const result = await this.captureToMemory({
                content: content,
                category: options.category || 'insight',
                importance: options.importance || 6,
                tags: options.tags || []
            });
            
            this.showToast(`✅ Quick captured! (ID: ${result.id.slice(-8)})`, 'success');
            return result;
            
        } catch (error) {
            console.error('Quick capture error:', error);
            this.showToast(`❌ Quick capture failed: ${error.message}`, 'error');
            throw error;
        }
    }
}

// Export for use in ai-monitor.js
window.AICaptureInterface = AICaptureInterface;