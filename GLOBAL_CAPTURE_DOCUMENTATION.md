# Universal AI Memory System - Global Capture Service

## 🌍 Overview

The Global Capture Service extends your Universal AI Memory System to capture insights from anywhere in macOS - not just browsers, but every application on your system. It provides seamless, intelligent memory capture with context awareness and smart filtering.

## ✨ Key Features

### 🔥 Global Hotkey Capture
- **⌘⇧M (Cmd+Shift+M)**: Instantly capture selected text from any application
- **Fallback Context**: If no text is selected, captures current window/app context
- **Smart Selection**: Automatically copies and restores clipboard content

### 📋 Smart Clipboard Monitoring
- **Intelligent Filtering**: Automatically skips passwords, API keys, and sensitive data
- **Content Analysis**: Only captures meaningful content (>10 characters, multiple words)
- **Duplicate Detection**: Avoids storing the same content multiple times
- **Configurable**: Can be enabled/disabled via menu bar

### 🧠 Context-Aware Intelligence
- **App Detection**: Recognizes and categorizes content based on source application
- **Project Context**: Automatically detects git repositories, Xcode projects, VS Code workspaces
- **Window Title Analysis**: Extracts project names from development tool titles
- **Smart Categorization**: Different behavior for development tools, browsers, text editors

### 🖼️ OCR Screenshot Capture
- **Screen Area Selection**: Capture and extract text from any part of your screen
- **Vision Framework**: Uses Apple's advanced text recognition
- **Automatic Processing**: Extracted text is automatically categorized and stored

### 📱 Menu Bar Interface
- **Quick Actions**: One-click capture, notes, and settings
- **Status Monitoring**: Visual indication of memory service connection
- **Settings Access**: Toggle features and configure preferences
- **Help Integration**: Built-in help and troubleshooting

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    macOS Global Capture Service                 │
│                        (Swift/Objective-C)                     │
├─────────────────────────────────────────────────────────────────┤
│  🔥 Global Hotkey Handler    📋 Clipboard Monitor              │
│  • Carbon Event API          • NSPasteboard monitoring         │
│  • ⌘⇧M registration         • 1-second polling                 │
│  • Text selection copy       • Content filtering               │
│                                                                 │
│  🖼️ OCR Processing           🧠 Context Detection              │
│  • Vision Framework          • NSWorkspace API                 │
│  • Screenshot analysis       • Active app identification       │
│  • Text extraction           • Project context detection       │
│                                                                 │
│  📱 Menu Bar Interface       ⚙️ Smart Categorization          │
│  • NSStatusItem              • Content analysis                │
│  • Quick actions menu        • App-based tagging              │
│  • Settings management       • Importance scoring              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP API (localhost:8091)
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              Universal AI Memory System                         │
│                  (Existing FastAPI Service)                    │
├─────────────────────────────────────────────────────────────────┤
│  💾 Memory Storage           🔍 Vector Search                   │
│  🏷️ Tagging System           📊 Statistics                     │
│  🔄 GitHub Integration       🌐 Browser Extension               │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Installation & Setup

### Prerequisites
- macOS 10.15 (Catalina) or later
- Universal AI Memory System running on localhost:8091
- Xcode Command Line Tools (for compilation)

### Installation Steps

1. **Build the Application**:
   ```bash
   cd global-capture
   ./build.sh
   ```

2. **Install the Service**:
   ```bash
   cd build
   ./install.sh
   ```

3. **Grant Permissions**:
   - Launch "Universal Memory Capture" from Applications
   - System will prompt for Accessibility permissions
   - Go to System Preferences > Security & Privacy > Accessibility
   - Add "Universal Memory Capture" to allowed applications

4. **Configure Auto-Start** (Optional):
   ```bash
   cd global-capture
   ./auto-start-setup.sh
   ```

## 🎯 Usage Guide

### Basic Operation

1. **Look for the Brain Icon**: After installation, you'll see a brain icon (🧠) in your menu bar
2. **Global Capture**: Press `⌘⇧M` anywhere in macOS to capture selected text or current context
3. **Menu Access**: Click the brain icon for quick actions and settings

### Capture Methods

#### 1. Hotkey Capture (⌘⇧M)
- **With Selection**: Captures the currently selected text from any app
- **Without Selection**: Captures current window title and app context
- **Smart Restore**: Automatically restores your original clipboard content

#### 2. Clipboard Monitoring
- **Automatic**: Monitors clipboard changes every second
- **Filtered**: Skips sensitive content, short text, and duplicates
- **Configurable**: Toggle on/off via menu bar

#### 3. Screenshot OCR
- **Interactive**: Click menu bar → "Capture Screen Area"
- **OCR Processing**: Extracts text using Apple's Vision framework
- **Automatic Storage**: Recognized text is automatically categorized

#### 4. Quick Notes
- **Menu Access**: Click menu bar → "Quick Note"
- **Instant Storage**: Direct input for quick thoughts and reminders

### Smart Features

#### Project Detection
The service automatically detects your current project context:

- **Xcode**: Extracts project name from window title
- **VS Code/Cursor**: Identifies workspace folder
- **Terminal**: Detects current directory
- **Git Repositories**: Recognizes git project context
- **GitHub**: Extracts repository names from browser URLs

#### Content Categorization
Content is automatically categorized based on:

- **Source App**: Development tools → `development`, browsers → `research`
- **Content Analysis**: Code snippets → `code`, errors → `troubleshooting`
- **Keywords**: Configuration files → `configuration`, solutions → `solution`

#### Smart Tagging
Automatic tags are generated from:

- **Technology Keywords**: Swift, JavaScript, Python, React, etc.
- **App Names**: xcode, terminal, safari, etc.
- **Project Names**: Detected from context
- **Content Type**: debugging, optimization, configuration

## ⚙️ Configuration

### Menu Bar Settings

Access via brain icon → Settings:

- **Clipboard Monitoring**: Enable/disable automatic clipboard capture
- **Memory API Base**: Configure connection to memory service
- **Excluded Apps**: Apps to skip during monitoring
- **OCR Settings**: Enable/disable screenshot text extraction

### Advanced Configuration

The service can be configured by modifying the `GlobalCaptureSettings` struct in the source code:

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

## 🔐 Security & Privacy

### Data Protection
- **Local Processing**: All analysis happens on your Mac
- **No Cloud Communication**: Only talks to your local memory service
- **Smart Filtering**: Automatically detects and skips sensitive content
- **Accessibility Only**: Minimal system permissions required

### Sensitive Content Detection
The service automatically skips content matching these patterns:
- Base64 encoded strings (potential tokens)
- Hash-like strings (API keys)
- Content containing words: password, token, secret, key
- Very short content (< 10 characters)
- Single words without context

### Permission Requirements
- **Accessibility Access**: Required to read text selections across applications
- **No Network Access**: Only communicates with localhost
- **No File System Access**: Beyond reading clipboard and active window info

## 🔧 Troubleshooting

### Common Issues

#### "Accessibility Access Required" Dialog
**Problem**: App requests accessibility permissions repeatedly
**Solution**:
1. Open System Preferences > Security & Privacy > Accessibility
2. Click the lock to make changes
3. Add "Universal Memory Capture" to the list
4. Ensure it's checked/enabled
5. Restart the application

#### Global Hotkey Not Working
**Problem**: ⌘⇧M doesn't trigger capture
**Solutions**:
- Verify accessibility permissions are granted
- Check for conflicts with other global hotkey applications
- Try restarting the capture service
- Check Console app for error messages

#### Memory Service Connection Failed
**Problem**: "Memory service offline" in menu bar
**Solutions**:
1. Verify memory service is running:
   ```bash
   curl http://localhost:8091/api/health
   ```
2. Check memory service logs for errors
3. Ensure no firewall is blocking localhost:8091
4. Restart the Universal Memory System API service

#### Clipboard Monitoring Not Working
**Problem**: Clipboard changes not being captured
**Causes**:
- Content is too short (< 10 characters)
- Content matches sensitive data patterns
- Clipboard monitoring is disabled in settings
- App is in excluded applications list

**Solutions**:
- Check menu bar for clipboard monitoring toggle
- Verify content meets minimum length requirements
- Check excluded apps list in settings

### Debug Information

#### Logs Location
- **Application Logs**: Console app → search "Universal Memory Capture"
- **Memory Service Logs**: Your Universal Memory System directory
- **LaunchAgent Logs**: `~/Library/Logs/UniversalMemoryCapture.log`

#### Useful Commands
```bash
# Check if app is running
ps aux | grep "Universal Memory Capture"

# Check LaunchAgent status
launchctl list | grep universalmemory

# Test memory service connection
curl -s http://localhost:8091/api/health | jq

# View recent captures
curl -s "http://localhost:8091/api/memory/search?q=global-capture&limit=5" | jq
```

## 🔗 Integration

### Works With
- **Universal AI Memory System**: Primary integration point
- **Browser Extension**: Complements web-based AI platform capture
- **GitHub Integration**: Enhanced project context detection
- **Any macOS App**: Text selection from any application

### API Integration
The service integrates with your existing memory API endpoints:

- **Storage**: `POST /api/memory/store`
- **Health Check**: `GET /api/health`
- **Statistics**: `GET /api/memory/stats`

### Data Format
Captured memories include enhanced metadata:

```json
{
  "content": "Selected text or context",
  "category": "development|research|note|troubleshooting",
  "tags": ["global-capture", "app-name", "project-name", "tech-keywords"],
  "importance": 5,
  "source": "global_capture_hotkey|clipboard_monitor|screenshot_ocr",
  "metadata": {
    "app_name": "Xcode",
    "bundle_id": "com.apple.dt.Xcode",
    "window_title": "MyProject — main.swift",
    "project_context": "MyProject",
    "capture_method": "hotkey_selection",
    "timestamp": "2024-08-10T14:30:00Z",
    "platform": "macos_global"
  }
}
```

## 🗑️ Uninstallation

### Complete Removal

1. **Stop the Service**:
   ```bash
   pkill -f "Universal Memory Capture"
   ```

2. **Remove Auto-Start** (if configured):
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.universalmemory.globalcapture.plist
   rm ~/Library/LaunchAgents/com.universalmemory.globalcapture.plist
   ```

3. **Remove Application**:
   ```bash
   rm -rf "/Applications/Universal Memory Capture.app"
   ```

4. **Remove Logs** (optional):
   ```bash
   rm ~/Library/Logs/UniversalMemoryCapture.*
   ```

### Using Uninstaller Script
```bash
cd global-capture/build
./uninstall.sh
```

## 🚨 Important Security Notes

### Permission Requirements
- **Accessibility Access**: Required for cross-app text selection
- **This is a powerful permission**: The app can read text from any application
- **Use Only Trusted Versions**: Only install from your own compilation
- **Review Source Code**: All code is open and reviewable

### Data Privacy
- **Local Only**: No data leaves your Mac
- **Memory Service Only**: Only communicates with your local API
- **Smart Filtering**: Actively avoids capturing sensitive information
- **User Control**: All features can be disabled via menu bar

## 🔄 Updates & Maintenance

### Updating the Service
1. Pull latest code from your Universal Memory System
2. Rebuild: `./build.sh`
3. Reinstall: `cd build && ./install.sh`
4. Service will automatically restart

### Monitoring Health
- Check menu bar status indicator
- Monitor memory service connection
- Review logs in Console app
- Use built-in help for troubleshooting

## 🎯 Performance Optimization

### Resource Usage
- **Memory**: ~10-15MB typical usage
- **CPU**: Minimal impact, only active during captures
- **Battery**: Negligible impact on MacBook battery life
- **Polling**: 1-second clipboard checks (configurable)

### Optimization Tips
- Disable clipboard monitoring if not needed
- Add frequently used apps to exclusion list
- Adjust minimum content length threshold
- Use OCR sparingly for better performance

## 🔮 Future Enhancements

### Planned Features
- **Custom Hotkey Configuration**: User-definable keyboard shortcuts
- **Advanced Filtering**: More sophisticated sensitive content detection
- **Integration Improvements**: Better project context detection
- **Performance Optimizations**: Reduced polling frequency
- **UI Enhancements**: Native settings window

### Contributing
This is part of your Universal AI Memory System. Modify the Swift code to add features, improve performance, or fix issues based on your specific needs.

---

**🧠 Universal AI Memory System - Never lose context again, anywhere in macOS!**