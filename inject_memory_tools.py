#!/usr/bin/env python3
"""
Inject Memory Tools into Vader R&D Lab
Creates a floating panel with memory system tools
"""

import webbrowser
import time
import subprocess

def create_browser_script():
    """Create the JavaScript to inject memory tools"""
    
    script = """
// Vader R&D Lab Memory Tools
console.log('🧠 Adding Memory Tools to Vader R&D Lab...');

// Remove existing panel if present
const existing = document.getElementById('memory-tools-panel');
if (existing) existing.remove();

// Create floating memory tools panel
const panel = document.createElement('div');
panel.id = 'memory-tools-panel';
panel.style.cssText = `
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
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
`;

panel.innerHTML = `
    <div style="margin-bottom: 12px; font-weight: 600; color: #22c55e; display: flex; align-items: center;">
        🧠 Memory System
        <button onclick="this.parentElement.parentElement.remove()" style="margin-left: auto; background: none; border: none; color: #94a3b8; cursor: pointer;">×</button>
    </div>
    <div>
        <button onclick="openImplQueue()" style="
            width: 100%; background: linear-gradient(45deg, #f97316, #ea580c);
            border: none; color: white; padding: 10px; border-radius: 6px;
            cursor: pointer; font-weight: 500; margin-bottom: 8px;
        ">🚀 Implementation Queue</button>
        
        <button onclick="openMemoryDash()" style="
            width: 100%; background: linear-gradient(45deg, #3b82f6, #2563eb);
            border: none; color: white; padding: 10px; border-radius: 6px;
            cursor: pointer; font-weight: 500; margin-bottom: 8px;
        ">📊 Memory Dashboard</button>
        
        <button onclick="askMemoryQ()" style="
            width: 100%; background: linear-gradient(45deg, #8b5cf6, #7c3aed);
            border: none; color: white; padding: 10px; border-radius: 6px;
            cursor: pointer; font-weight: 500; margin-bottom: 8px;
        ">🤖 Ask Memory Q&A</button>
        
        <button onclick="capturePage()" style="
            width: 100%; background: linear-gradient(45deg, #10b981, #059669);
            border: none; color: white; padding: 10px; border-radius: 6px;
            cursor: pointer; font-weight: 500; margin-bottom: 8px;
        ">📝 Capture This Page</button>
    </div>
`;

document.body.appendChild(panel);

// Define button functions
window.openImplQueue = () => {
    // Try multiple methods to open Implementation Queue
    try {
        window.open('file:///Applications/Implementation Queue.app');
    } catch(e) {
        alert(`Implementation Queue Options:
        
1. 🖱️  Click rocket icon in Dock
2. ⌨️  Press ⌘Space → type "OpenImpl" → Enter  
3. 💻 Terminal: type "implq"
4. 📁 Open /Applications/Implementation Queue.app

Queue has your pending implementations!`);
    }
};

window.openMemoryDash = () => {
    window.open('http://localhost:8091/dashboard', '_blank');
};

window.askMemoryQ = () => {
    const question = prompt('Ask a question about your memories:');
    if (question) {
        window.open(`http://localhost:8091/qa?q=${encodeURIComponent(question)}`, '_blank');
    }
};

window.capturePage = () => {
    const data = {
        url: location.href,
        title: document.title,
        content: document.body.innerText.substring(0, 3000),
        project: 'vader-r-and-d-lab',
        category: 'lab_session',
        tags: ['vader-lab', 'development', 'r-and-d']
    };
    
    fetch('http://localhost:8091/api/memory/store', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(() => {
        const notif = document.createElement('div');
        notif.style.cssText = `
            position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
            background: #22c55e; color: white; padding: 12px 24px;
            border-radius: 8px; z-index: 10001; font-weight: 500;
        `;
        notif.textContent = '✅ Lab session captured!';
        document.body.appendChild(notif);
        setTimeout(() => notif.remove(), 3000);
    }).catch(() => alert('Memory API not available at localhost:8091'));
};

console.log('✅ Memory Tools Added! Look for panel in top-right corner.');
"""
    
    return script

def inject_into_browser():
    """Inject the memory tools into the browser"""
    
    script = create_browser_script()
    
    # Create a data URL with the script
    script_encoded = script.replace('\n', '').replace("'", "\\'")
    
    # Create bookmarklet
    bookmarklet = f"javascript:(function(){{{script_encoded}}})();"
    
    print("🧠 Memory Tools for Vader R&D Lab")
    print("=" * 50)
    print()
    print("🎯 To add memory tools to your Vader R&D Lab:")
    print()
    print("Method 1 - Copy this bookmarklet:")
    print("─" * 30)
    print(bookmarklet[:100] + "...")
    print()
    print("Method 2 - Run in browser console:")
    print("─" * 30)
    print("1. Go to localhost:5175 (your Vader R&D Lab)")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to Console tab")
    print("4. Paste this script and press Enter:")
    print()
    
    # Save script to file for easy copying
    with open('/tmp/vader_memory_tools.js', 'w') as f:
        f.write(script)
    
    print("📄 Script saved to: /tmp/vader_memory_tools.js")
    print()
    print("5. A floating panel should appear with these tools:")
    print("   🚀 Implementation Queue")
    print("   📊 Memory Dashboard") 
    print("   🤖 Ask Memory Q&A")
    print("   📝 Capture This Page")
    print()
    print("✅ The tools will integrate seamlessly with your lab!")

if __name__ == "__main__":
    inject_into_browser()