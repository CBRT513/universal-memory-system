// Vader R&D Lab - Memory System Integration
// Adds Implementation Queue and memory tools to the lab interface

(function() {
    'use strict';
    
    console.log('🧠 Vader R&D Lab Memory Integration Loading...');
    
    // Wait for page to load
    function initMemoryIntegration() {
        // Find the navigation area or create one
        const nav = document.querySelector('nav') || document.querySelector('[class*="nav"]') || document.querySelector('[class*="menu"]');
        
        if (!nav) {
            console.log('Creating memory tools section...');
            createMemoryToolsSection();
            return;
        }
        
        console.log('Adding memory tools to existing navigation...');
        addMemoryToolsToNav(nav);
    }
    
    function createMemoryToolsSection() {
        // Create a floating memory tools panel
        const memoryPanel = document.createElement('div');
        memoryPanel.id = 'memory-tools-panel';
        memoryPanel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 12px;
            padding: 16px;
            min-width: 250px;
            backdrop-filter: blur(10px);
            z-index: 10000;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        `;
        
        memoryPanel.innerHTML = `
            <div style="margin-bottom: 12px; font-weight: 600; color: #22c55e; display: flex; align-items: center;">
                🧠 Memory System
                <button id="toggle-memory-panel" style="margin-left: auto; background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 18px;">−</button>
            </div>
            <div id="memory-tools-content">
                <div style="margin-bottom: 8px;">
                    <button onclick="openImplementationQueue()" style="
                        width: 100%;
                        background: linear-gradient(45deg, #f97316, #ea580c);
                        border: none;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 500;
                        margin-bottom: 6px;
                        transition: transform 0.2s;
                    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                        🚀 Implementation Queue
                    </button>
                </div>
                <div style="margin-bottom: 8px;">
                    <button onclick="openMemoryDashboard()" style="
                        width: 100%;
                        background: linear-gradient(45deg, #3b82f6, #2563eb);
                        border: none;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 500;
                        margin-bottom: 6px;
                        transition: transform 0.2s;
                    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                        📊 Memory Dashboard
                    </button>
                </div>
                <div style="margin-bottom: 8px;">
                    <button onclick="openQAEngine()" style="
                        width: 100%;
                        background: linear-gradient(45deg, #8b5cf6, #7c3aed);
                        border: none;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 500;
                        margin-bottom: 6px;
                        transition: transform 0.2s;
                    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                        🤖 Memory Q&A
                    </button>
                </div>
                <div style="margin-bottom: 8px;">
                    <button onclick="captureCurrentPage()" style="
                        width: 100%;
                        background: linear-gradient(45deg, #10b981, #059669);
                        border: none;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 500;
                        margin-bottom: 6px;
                        transition: transform 0.2s;
                    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                        📝 Capture This Page
                    </button>
                </div>
                <div style="font-size: 12px; color: #64748b; text-align: center; margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(100, 116, 139, 0.2);">
                    Universal Memory System
                </div>
            </div>
        `;
        
        document.body.appendChild(memoryPanel);
        
        // Add toggle functionality
        document.getElementById('toggle-memory-panel').addEventListener('click', function() {
            const content = document.getElementById('memory-tools-content');
            const button = this;
            if (content.style.display === 'none') {
                content.style.display = 'block';
                button.textContent = '−';
            } else {
                content.style.display = 'none';
                button.textContent = '+';
            }
        });
    }
    
    function addMemoryToolsToNav(nav) {
        // Add memory tools to existing navigation
        const memorySection = document.createElement('div');
        memorySection.innerHTML = `
            <div style="margin: 16px 0; padding: 8px; border: 1px solid #22c55e; border-radius: 8px;">
                <h3 style="margin: 0 0 8px 0; color: #22c55e; font-size: 14px;">🧠 Memory System</h3>
                <a href="#" onclick="openImplementationQueue(); return false;" style="display: block; margin: 4px 0; color: #f97316; text-decoration: none;">🚀 Implementation Queue</a>
                <a href="#" onclick="openMemoryDashboard(); return false;" style="display: block; margin: 4px 0; color: #3b82f6; text-decoration: none;">📊 Memory Dashboard</a>
                <a href="#" onclick="openQAEngine(); return false;" style="display: block; margin: 4px 0; color: #8b5cf6; text-decoration: none;">🤖 Memory Q&A</a>
                <a href="#" onclick="captureCurrentPage(); return false;" style="display: block; margin: 4px 0; color: #10b981; text-decoration: none;">📝 Capture Page</a>
            </div>
        `;
        nav.appendChild(memorySection);
    }
    
    // Define the global functions for the buttons
    window.openImplementationQueue = function() {
        console.log('🚀 Opening Implementation Queue...');
        
        // Try multiple methods to open the Implementation Queue
        fetch('/api/implementations/open', {method: 'POST'}).catch(() => {
            // Fallback to direct app launch
            fetch('http://localhost:8091/api/launch/implementation-queue', {method: 'POST'}).catch(() => {
                // Final fallback - show instructions
                alert(`To open Implementation Queue:
                
1. Click the rocket icon in your Dock
2. Or press ⌘Space, type "OpenImpl", press Enter
3. Or in Terminal: type "implq"
4. Or open /Applications/Implementation Queue.app

The Implementation Queue GUI should open in a new window.`);
            });
        });
    };
    
    window.openMemoryDashboard = function() {
        console.log('📊 Opening Memory Dashboard...');
        window.open('http://localhost:8091/dashboard', '_blank');
    };
    
    window.openQAEngine = function() {
        console.log('🤖 Opening Memory Q&A...');
        const question = prompt('Ask a question about your memories:');
        if (question) {
            // Open Q&A in new window with the question
            window.open(`http://localhost:8091/qa?q=${encodeURIComponent(question)}`, '_blank');
        }
    };
    
    window.captureCurrentPage = function() {
        console.log('📝 Capturing current page...');
        
        const pageData = {
            url: window.location.href,
            title: document.title,
            content: document.body.innerText.substring(0, 5000), // First 5000 chars
            timestamp: new Date().toISOString(),
            project: 'vader-r-and-d-lab',
            category: 'lab_session',
            tags: ['vader-lab', 'r-and-d', 'development']
        };
        
        // Send to memory API
        fetch('http://localhost:8091/api/memory/store', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(pageData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('✅ Page captured to memory system:', data);
            
            // Show success notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #22c55e;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                z-index: 10001;
                font-weight: 500;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            `;
            notification.textContent = '✅ Page captured to memory system!';
            document.body.appendChild(notification);
            
            setTimeout(() => notification.remove(), 3000);
        })
        .catch(error => {
            console.error('❌ Failed to capture page:', error);
            alert('Failed to capture page. Make sure the memory API is running at localhost:8091');
        });
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMemoryIntegration);
    } else {
        initMemoryIntegration();
    }
    
    console.log('✅ Vader R&D Lab Memory Integration Loaded');
})();