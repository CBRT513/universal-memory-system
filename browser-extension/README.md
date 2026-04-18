# Universal AI Memory Capture - Browser Extension

**Seamlessly capture insights from any AI platform directly to your Universal Memory System**

## 🎯 Overview

The Universal AI Memory Capture browser extension automatically detects valuable AI responses and provides one-click capture functionality across all major AI platforms:

- **ChatGPT** (OpenAI)
- **Claude** (Anthropic) 
- **Perplexity**
- **Bard** (Google)
- **Bing Chat** (Microsoft)
- **Hugging Face**

## ✨ Features

### 🤖 Intelligent Detection
- **Auto-detection** of valuable AI responses
- **Smart highlighting** of capture-worthy content
- **Platform-aware** selectors for each AI service
- **Pattern matching** to identify solutions, code, insights

### 💾 One-Click Capture
- **Floating capture button** appears when valuable content is detected
- **Rich modal interface** with tagging and categorization
- **Quick capture** via keyboard shortcut (Ctrl+M)
- **Context menu integration** for right-click capture

### 🏷️ Smart Categorization
- **Auto-categorization** based on content analysis
- **Intelligent tagging** with technology detection
- **Custom categories**: Solution, Code, Pattern, Configuration, Insight
- **Platform tags** automatically applied

### ⚙️ Seamless Integration
- **Real-time sync** with local memory service
- **Background processing** with service worker
- **Extension popup** for quick actions and stats
- **Settings management** with user preferences

## 🚀 Installation

### Prerequisites

1. **Universal Memory Service** must be running:
   ```bash
   cd /path/to/universal-memory-system
   ./start-memory-service.sh
   ```

2. **Browser**: Chrome, Edge, or Chromium-based browser with Manifest V3 support

### Install Extension

#### Development Mode (Recommended)

1. **Clone and navigate**:
   ```bash
   git clone /path/to/universal-memory-system
   cd universal-memory-system/browser-extension
   ```

2. **Open Chrome Extensions**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (top right)
   
3. **Load extension**:
   - Click "Load unpacked"
   - Select the `browser-extension` folder
   
4. **Pin extension**:
   - Click the Extensions icon (puzzle piece)
   - Pin "Universal AI Memory Capture"

#### Chrome Web Store (Future)
Extension will be published to Chrome Web Store for easy installation.

## 📖 Usage Guide

### Initial Setup

1. **Start Memory Service**:
   ```bash
   ./start-memory-service.sh
   ```

2. **Verify Connection**:
   - Click extension icon in toolbar
   - Check connection status (should show green ✅)
   - View memory statistics

3. **Configure Settings**:
   - Enable/disable auto-detection
   - Toggle notifications
   - Adjust smart tagging preferences

### Capturing AI Insights

#### Method 1: Auto-Detection (Recommended)
1. Visit any supported AI platform
2. Ask questions and get AI responses
3. Extension automatically highlights valuable content
4. Click the floating "Remember" button when it appears
5. Review and edit in the capture modal
6. Add custom tags if desired
7. Click "Save to Memory"

#### Method 2: Manual Selection
1. Select text on any AI platform page
2. Right-click → "🧠 Capture to Memory"
3. Or use keyboard shortcut `Ctrl+M`

#### Method 3: Quick Note
1. Click extension icon in toolbar
2. Click "Quick Note"
3. Type your insight
4. Add tags (optional)
5. Save to memory

#### Method 4: Page Capture
1. Right-click on page → "📄 Capture Page Info"
2. Or click extension icon → "Capture Page"

### Managing Captures

- **View all memories**: Click "Dashboard" in extension popup
- **Search memories**: Use the web interface at http://localhost:8092
- **Statistics**: View capture counts in extension popup

## 🎮 Keyboard Shortcuts

- **Ctrl+M (Cmd+M)**: Quick capture selected text or current response
- **Escape**: Close capture modal
- **Enter**: Submit capture form

## 🔧 Configuration

### Extension Settings

Available in extension popup:

- **Auto-detect valuable responses**: Automatically highlight capture-worthy content
- **Show capture notifications**: Display success/error notifications  
- **Smart auto-tagging**: Apply technology and context tags automatically

### Memory Service Settings

Configure in `config/settings.json`:

```json
{
  "memory": {
    "auto_project_detection": true,
    "embedding_provider": "sentence_transformers"
  },
  "api": {
    "host": "127.0.0.1",
    "port": 8091,
    "cors_enabled": true
  }
}
```

### Advanced Configuration

#### Custom Platform Support

Add new AI platforms by editing `content-scripts/ai-monitor.js`:

```javascript
// Add platform detection
if (hostname.includes('newai.com')) return 'newai';

// Add platform selectors
case 'newai':
    selectors = [
        '.ai-response',
        '[data-ai-message]'
    ];
    break;
```

#### Capture Patterns

Customize value detection in `ai-monitor.js`:

```javascript
const highValuePatterns = [
    'custom pattern',
    'solution indicator',
    'important insight'
];
```

## 🎯 Platform-Specific Features

### ChatGPT Integration
- Detects GPT-4 responses specifically
- Captures conversation context
- Handles code blocks and step-by-step solutions

### Claude Integration  
- Optimized for Claude's response format
- Captures thinking process and reasoning
- Handles multi-turn conversations

### Perplexity Integration
- Captures sources and citations
- Handles research-style responses
- Includes search context

## 🛠️ Development

### Architecture

```
browser-extension/
├── manifest.json              # Extension configuration
├── background/
│   └── service-worker.js      # Background processes
├── content-scripts/
│   ├── ai-monitor.js          # Main content script
│   ├── capture-interface.js   # Capture modal
│   └── capture-ui.css        # Styling
├── popup/
│   ├── popup.html            # Extension popup
│   ├── popup.js              # Popup functionality
│   └── popup.css             # Popup styling
└── icons/                    # Extension icons
```

### Key Components

1. **AI Monitor** (`ai-monitor.js`):
   - Detects AI platforms
   - Monitors for new responses  
   - Identifies valuable content
   - Shows capture interface

2. **Capture Interface** (`capture-interface.js`):
   - Rich modal for capture editing
   - Smart tagging system
   - Category selection
   - API communication

3. **Service Worker** (`service-worker.js`):
   - Background processing
   - Keyboard shortcuts
   - Context menus
   - Health checks

4. **Extension Popup** (`popup.js`):
   - Quick actions
   - Statistics display
   - Settings management
   - Dashboard access

### API Integration

Extension communicates with memory service via REST API:

```javascript
// Capture endpoint
POST /api/memory/capture-ai
{
  "content": "AI response text",
  "ai_context": {
    "platform": "chatgpt",
    "url": "https://chat.openai.com/...",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Testing

1. **Load extension** in development mode
2. **Visit AI platforms**: ChatGPT, Claude, etc.
3. **Verify auto-detection** works
4. **Test capture flow** end-to-end
5. **Check memory service** receives data correctly

### Debugging

- **Extension console**: Right-click extension → Inspect popup
- **Content script logs**: Open DevTools on AI platform pages  
- **Service worker logs**: chrome://extensions → Service worker
- **Memory service logs**: Check terminal running the service

## 🔐 Privacy & Security

### Local-Only Processing
- All data stays on your local machine
- No cloud storage or external services
- Direct communication with local memory service

### Permissions Explained
- **activeTab**: Access current tab for capture functionality
- **storage**: Save extension settings locally
- **scripting**: Inject content scripts on AI platforms
- **host_permissions**: Access specific AI platform domains only

### Data Collection
- **None**: Extension doesn't collect analytics or usage data
- **Local storage only**: Settings saved in browser's local storage
- **Memory service**: Data sent only to your local memory service

## 🐛 Troubleshooting

### Extension Not Working

1. **Check memory service**:
   ```bash
   curl http://localhost:8091/api/health
   ```

2. **Verify extension permissions**:
   - Go to chrome://extensions/
   - Check Universal AI Memory Capture has required permissions

3. **Reload extension**:
   - Click reload button in chrome://extensions/

### Capture Button Not Appearing

1. **Check platform support**: Ensure you're on a supported AI platform
2. **Verify content detection**: Try manually selecting text and right-click
3. **Check settings**: Ensure "Auto-detect" is enabled in extension popup

### Connection Issues

1. **Memory service status**:
   - Check extension popup for connection status
   - Restart memory service if needed

2. **Port conflicts**: 
   - Verify service running on port 8091
   - Check firewall settings

3. **CORS issues**:
   - Ensure memory service has CORS enabled
   - Check browser console for CORS errors

### Performance Issues

1. **Disable on unused sites**: Extension only runs on AI platforms
2. **Check content script injection**: Should not affect other websites
3. **Memory usage**: Service worker is lightweight and efficient

## 📋 Changelog

### v1.0.0 (Current)
- ✅ Initial release
- ✅ Support for 6 major AI platforms
- ✅ Auto-detection and manual capture
- ✅ Rich capture interface with tagging
- ✅ Extension popup with statistics
- ✅ Keyboard shortcuts and context menus
- ✅ Smart categorization and tagging

### Planned Features
- 🔄 Chrome Web Store publication
- 🔄 Firefox support
- 🔄 More AI platform integrations
- 🔄 Advanced capture filters
- 🔄 Export functionality
- 🔄 Team sharing features

## 📞 Support

### Getting Help

1. **Documentation**: Check this README and memory system docs
2. **Logs**: Check browser console and service worker logs
3. **GitHub Issues**: Report bugs and feature requests
4. **Community**: Join discussions about AI memory systems

### Common Resources

- **Memory Service Docs**: `../README.md`
- **API Documentation**: http://localhost:8091/docs
- **Web Interface**: http://localhost:8092
- **Health Check**: http://localhost:8091/api/health

---

**Made with 🧠 for AI-powered productivity**

Transform your AI conversations into a searchable, intelligent knowledge base that grows with you.