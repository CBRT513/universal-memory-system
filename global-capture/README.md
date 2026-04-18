# Universal AI Memory - Global Capture Service

**System-wide memory capture for macOS that works with any application**

## 🌟 What It Does

The Global Capture Service extends your Universal AI Memory System beyond browsers to capture knowledge from anywhere in macOS:

- **⌘⇧M Global Hotkey**: Capture selected text from any application instantly
- **📋 Smart Clipboard Monitoring**: Automatically captures meaningful clipboard content
- **🖼️ OCR Screenshot Capture**: Extract text from images and non-selectable content
- **🧠 Context-Aware Intelligence**: Automatically detects projects, categorizes content, and generates smart tags
- **📱 Menu Bar Interface**: Quick access to all capture functions and settings

## 🚀 Quick Start

```bash
# Build the application
./build.sh

# Install the service  
cd build && ./install.sh

# Grant Accessibility permissions when prompted
# Look for the brain icon 🧠 in your menu bar
# Press ⌘⇧M anywhere in macOS to capture!
```

## ✨ Key Features

### Global Hotkey Capture
- Press `⌘⇧M` (Cmd+Shift+M) anywhere in macOS
- Captures selected text from any application
- Falls back to window context if no selection
- Smart clipboard management (saves and restores original content)

### Smart Clipboard Monitoring  
- Monitors clipboard changes every second
- Automatically filters out sensitive data (passwords, API keys, tokens)
- Skips short/meaningless content
- Captures only meaningful text with context

### Context Intelligence
- **Project Detection**: Automatically identifies git repos, Xcode projects, VS Code workspaces
- **App Categorization**: Different behavior for development tools vs browsers vs text editors
- **Smart Tagging**: Technology keywords, project names, content types
- **Importance Scoring**: Prioritizes technical content, solutions, and code

### OCR Screenshot Capture
- Interactive screen area selection
- Apple Vision framework for text recognition
- Automatic categorization of extracted text
- Perfect for PDFs, error dialogs, non-selectable content

### Menu Bar Interface
- Brain icon (🧠) provides instant access
- Quick actions: capture, notes, screenshot OCR
- Settings and preferences
- Connection status monitoring
- Help and troubleshooting

## 🏗️ Technical Architecture

```
macOS Global Capture Service (Swift)
├── Global Hotkey Handler (Carbon Events API)
├── Clipboard Monitor (NSPasteboard polling)  
├── OCR Processor (Vision framework)
├── Context Detector (NSWorkspace + Accessibility)
├── Menu Bar Interface (NSStatusItem)
└── Smart Categorizer (content analysis)
                    │
                    │ HTTP API
                    ▼
Universal Memory System (FastAPI)
├── Memory Storage (SQLite + FTS5)
├── Vector Search (HNSW embeddings)
├── GitHub Integration  
├── Browser Extension Support
└── Web Dashboard Interface
```

## 📁 Project Structure

```
global-capture/
├── main.swift                 # Core application logic
├── build.sh                   # Compilation and packaging script
├── auto-start-setup.sh        # LaunchAgent configuration
├── launch-daemon.plist        # Auto-start configuration template
├── USER_INSTRUCTIONS.md       # End-user setup and usage guide
└── build/                     # Generated after running build.sh
    ├── Universal Memory Capture.app
    ├── install.sh             # Installation script
    ├── uninstall.sh           # Removal script
    └── README.md              # Distribution documentation
```

## 🔧 Development

### Requirements
- macOS 10.15+ (Catalina or later)
- Xcode Command Line Tools
- Swift 5.0+
- Universal Memory System running on localhost:8091

### Building
```bash
# Compile and package
./build.sh

# This creates:
# - Universal Memory Capture.app
# - Installation scripts
# - Distribution package
```

### Customization
Edit `main.swift` to modify:
- Global hotkey combination (currently ⌘⇧M)
- Clipboard polling interval (currently 1 second)
- Content filtering rules and patterns
- API endpoint configuration
- Menu bar interface and actions

## 🔐 Security & Privacy

### Permissions Required
- **Accessibility Access**: Required to read text selections across applications
- **No network access**: Only communicates with localhost:8091
- **No file system access**: Beyond clipboard and active window detection

### Data Protection  
- **Local processing only**: All analysis happens on your Mac
- **Smart filtering**: Automatically detects and skips sensitive content
- **Pattern-based exclusion**: API keys, passwords, tokens, hashes
- **App-based exclusion**: Configurable list of apps to ignore
- **User control**: All features can be disabled

### Sensitive Content Detection
Automatically skips content matching:
- Base64 encoded strings (potential tokens)
- Hexadecimal hashes (API keys, secrets)
- Content containing: password, token, secret, key
- Very short text (< 10 characters)
- Single words without context

## 🎯 Integration

### Works With
- **Any macOS Application**: Xcode, VS Code, Terminal, Safari, Chrome, Notes, Slack, etc.
- **Universal Memory System**: Core memory storage and search
- **Browser Extension**: Complements AI platform capture
- **GitHub Integration**: Enhanced project context detection
- **CLI Interface**: Command-line memory management

### API Integration
Connects to existing Universal Memory System endpoints:
- `POST /api/memory/store` - Store captured content
- `GET /api/health` - Check service connection
- `GET /api/memory/stats` - Usage statistics

### Data Format
Captured memories include rich metadata:
```json
{
  "content": "Selected text or context",
  "category": "development|research|troubleshooting|configuration|note",
  "importance": 5,
  "tags": ["global-capture", "xcode", "swift", "debugging"],
  "source": "global_capture_hotkey",
  "metadata": {
    "app_name": "Xcode",
    "bundle_id": "com.apple.dt.Xcode", 
    "window_title": "MyProject — ViewController.swift",
    "project_context": "MyProject",
    "capture_method": "hotkey_selection",
    "platform": "macos_global"
  }
}
```

## 🔧 Configuration

### Runtime Settings (Menu Bar)
- Toggle clipboard monitoring on/off
- Adjust content filtering sensitivity  
- Configure excluded applications
- Enable/disable OCR functionality
- Connection status and health check

### Build-Time Settings (main.swift)
```swift
struct GlobalCaptureSettings {
    var hotkeyEnabled: Bool = true
    var clipboardMonitorEnabled: Bool = true
    var memoryAPIBase: String = "http://localhost:8091"
    var excludedApps: [String] = ["Keychain Access", "1Password"]
    var minimumClipboardLength: Int = 10
    var ocrEnabled: Bool = true
}
```

## 🗑️ Uninstallation

### Using Script
```bash
cd build && ./uninstall.sh
```

### Manual Removal
1. Quit the application
2. Remove from Applications folder
3. Remove LaunchAgent (if configured):
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.universalmemory.globalcapture.plist
   rm ~/Library/LaunchAgents/com.universalmemory.globalcapture.plist
   ```
4. Remove from Accessibility permissions

## 🚨 Troubleshooting

### Common Issues

#### Accessibility Permissions
1. System Preferences → Security & Privacy → Accessibility
2. Add "Universal Memory Capture" to allowed apps
3. Ensure it's enabled/checked
4. Restart the application

#### Global Hotkey Conflicts
- Check for other apps using ⌘⇧M (Magnet, Rectangle, etc.)
- Consider customizing hotkey in source code
- Verify Accessibility permissions are granted

#### Memory Service Connection  
```bash
# Check if memory service is running
curl localhost:8091/api/health

# Start memory service if needed
cd universal-memory-system/src
python3 api_service.py --port 8091
```

#### Performance Issues
- Adjust clipboard polling interval in source
- Add more apps to exclusion list
- Disable OCR if not needed
- Monitor Console app for errors

## 📊 Monitoring

### Health Checks
```bash
# Check if app is running
ps aux | grep "Universal Memory Capture"

# Test memory service connection
curl localhost:8091/api/health

# View recent captures
curl "localhost:8091/api/memory/search?q=global-capture&limit=10"
```

### Debug Information
- **Console App**: Search "Universal Memory Capture" for logs
- **Menu Bar Status**: Connection indicator in menu
- **LaunchAgent Logs**: `~/Library/Logs/UniversalMemoryCapture.log`

## 🔮 Future Enhancements

### Planned Features
- **Custom Hotkey Configuration**: User-definable keyboard shortcuts
- **Advanced OCR**: Formula and diagram recognition
- **Voice Memo Capture**: Audio transcription and storage
- **Smart Scheduling**: Presentation mode detection
- **Team Features**: Shared memory systems

### Contributing
This is part of your personal Universal AI Memory System. Modify the Swift code to:
- Add new capture methods
- Improve context detection
- Enhance content filtering
- Customize categorization logic
- Add new integrations

## 📖 Documentation

- **[USER_INSTRUCTIONS.md](USER_INSTRUCTIONS.md)**: End-user setup and usage guide
- **[GLOBAL_CAPTURE_DOCUMENTATION.md](../GLOBAL_CAPTURE_DOCUMENTATION.md)**: Complete technical documentation
- **[QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md)**: System-wide setup instructions

---

**🧠 Never lose context again - capture knowledge from anywhere in macOS!**