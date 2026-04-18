# Universal AI Memory - Global Capture Service
## 📱 User Instructions & Setup Guide

### 🚀 Quick Installation

1. **Build the app**:
   ```bash
   cd global-capture
   ./build.sh
   ```

2. **Install**:
   ```bash
   cd build
   ./install.sh
   ```

3. **Grant permissions when prompted** (System Preferences → Security & Privacy → Accessibility)

4. **Look for the brain icon 🧠 in your menu bar**

### ⌨️ Basic Usage

#### Global Hotkey: **⌘⇧M** (Cmd+Shift+M)
- **Select text in any app** → Press ⌘⇧M → Text saved to memory
- **No selection** → Press ⌘⇧M → Current window context saved
- Works in: Xcode, VS Code, Terminal, Safari, Chrome, Notes, Slack, anywhere!

#### Menu Bar Features (Click the 🧠 icon)
- **📝 Quick Note**: Instantly save a thought or reminder
- **📸 Capture Selection**: Manually trigger text capture  
- **🖼️ Capture Screen Area**: OCR text from screenshots
- **📋 Toggle Clipboard Monitoring**: Auto-capture clipboard changes
- **⚙️ Settings**: Configure capture preferences
- **📊 Open Dashboard**: View your memories in web browser

### 🧠 Smart Features

#### Automatic Project Detection
The app knows what you're working on:
- **Xcode**: "MyProject — ViewController.swift" → Project: "MyProject"
- **VS Code**: "frontend - Visual Studio Code" → Project: "frontend"  
- **Terminal**: "~/Code/my-app" → Project: "my-app"
- **GitHub**: "github.com/user/repo" → Project: "repo"

#### Intelligent Content Filtering  
Automatically skips sensitive content:
- ❌ Passwords and API keys
- ❌ Base64 tokens  
- ❌ Very short text (< 10 characters)
- ✅ Code snippets and solutions
- ✅ Documentation and notes
- ✅ Error messages and fixes

#### Smart Categorization
Content is automatically sorted:
- **Development**: Code from Xcode, Terminal, VS Code
- **Research**: Content from browsers
- **Troubleshooting**: Error messages and solutions
- **Configuration**: Settings and config files
- **Notes**: Quick thoughts and reminders

### 📋 Clipboard Monitoring

When enabled (default), the app watches your clipboard:
- **Copies meaningful text** (>10 chars, multiple words)
- **Skips sensitive data** (passwords, tokens, hashes)
- **Adds context** (what app you copied from)
- **Prevents duplicates** (won't save same text twice)

Toggle on/off: Menu bar 🧠 → "📋 Clipboard Monitoring"

### 🖼️ Screenshot Text Capture

1. Click menu bar 🧠 → "🖼️ Capture Screen Area"
2. **Select area of screen** with text
3. **OCR automatically extracts text** using Apple's Vision
4. **Text saved to memory** with screenshot context

Great for:
- Capturing text from PDFs
- Error dialogs and alerts  
- Non-selectable web content
- Images with text
- Code in videos/presentations

### ⚙️ Settings & Configuration

#### Menu Bar Settings
- **📋 Clipboard Monitoring**: Enable/disable automatic clipboard capture
- **Memory API Connection**: Shows if connected to your memory system
- **Quick Actions**: Fast access to capture functions

#### Advanced Settings (Click ⚙️)
- **API Base URL**: Default localhost:8091 (change if memory service runs elsewhere)
- **Excluded Apps**: Apps to ignore during monitoring
- **Content Filters**: Adjust sensitivity for sensitive data detection  
- **OCR Settings**: Enable/disable screenshot text extraction

#### Auto-Start Setup (Optional)
To start automatically when you log in:
```bash
cd global-capture
./auto-start-setup.sh
```

### 🔐 Privacy & Security

#### What Data is Captured
- **Selected text** from any application
- **Meaningful clipboard content** (filtered for safety)  
- **Window titles** and app names for context
- **Project context** (git repos, workspace folders)
- **Screenshot text** via OCR

#### What is NOT Captured  
- ❌ Passwords or sensitive form data
- ❌ API keys, tokens, or secrets
- ❌ Content from excluded apps (Keychain, 1Password)
- ❌ Very short or meaningless text
- ❌ Duplicate content

#### Data Security
- ✅ **All data stays on your Mac** - no cloud uploads
- ✅ **Only talks to your local memory service** (localhost:8091)
- ✅ **Smart filtering** prevents sensitive data capture  
- ✅ **Accessibility permissions only** - minimal system access
- ✅ **You control everything** - disable any feature anytime

### 🔧 Troubleshooting

#### "Accessibility Access Required" 
1. **System Preferences** → **Security & Privacy** → **Accessibility**
2. **Click lock** to make changes (enter password)
3. **Add "Universal Memory Capture"** to the list
4. **Make sure it's checked/enabled**
5. **Restart the app**

#### Global Hotkey ⌘⇧M Not Working
- ✅ **Check Accessibility permissions** (see above)
- ✅ **Look for other apps** using same hotkey (Magnet, Rectangle, etc.)
- ✅ **Restart the capture service** (quit and relaunch from Applications)
- ✅ **Check Console app** for error messages

#### Menu Bar Icon Missing
- ✅ **Check if app is running**: `ps aux | grep "Universal Memory Capture"`  
- ✅ **Launch from Applications folder**: "Universal Memory Capture"
- ✅ **Check menu bar overflow**: Arrow icon on right side of menu bar

#### "Memory Service Offline"
1. **Check if memory service is running**:
   ```bash
   curl localhost:8091/api/health
   ```
2. **Start the memory service**:
   ```bash
   cd universal-memory-system/src
   python3 api_service.py
   ```
3. **Check firewall settings** (shouldn't block localhost)

#### Clipboard Monitoring Not Working
- ✅ **Check toggle**: Menu bar → "📋 Clipboard Monitoring" should be ✓
- ✅ **Content too short**: Must be >10 characters with multiple words
- ✅ **Sensitive content**: Passwords/tokens are automatically filtered
- ✅ **Excluded app**: Check if current app is in exclusion list

### 🎯 Usage Tips

#### For Developers
- **Copy error messages** → Automatic capture with context
- **Select code snippets** → ⌘⇧M → Saved with project context  
- **Documentation browsing** → Clipboard monitoring captures useful info
- **Terminal commands** → Select and ⌘⇧M for command reference

#### For Research
- **Reading articles** → Select key points → ⌘⇧M  
- **Video tutorials** → Screenshot OCR for code examples
- **PDF documents** → OCR capture for non-selectable text
- **Stack Overflow** → Auto-capture solutions while browsing

#### For Note-Taking
- **Quick thoughts** → Menu bar → "📝 Quick Note"
- **Meeting notes** → Select and capture important points
- **Todo items** → Quick note capture for later action
- **References** → Capture URLs, quotes, and sources

### 📊 Monitoring Your Captures

#### View Recent Captures
- **Web Dashboard**: Open localhost:8092 in browser
- **Menu Bar**: Click 🧠 → "📊 Open Dashboard"  
- **Command Line**: `python3 src/memory_cli.py "What did I capture recently?"`

#### Search Your Memories
- **Natural Language**: "Show me React optimization tips"
- **By Project**: Filter memories by detected project context
- **By Category**: development, research, troubleshooting, etc.
- **By App**: memories captured from specific applications

### 🗑️ Uninstalling

#### Quick Uninstall
```bash
cd global-capture/build
./uninstall.sh
```

#### Manual Uninstall
1. **Quit the app**: Menu bar 🧠 → "🚪 Quit"
2. **Remove from Applications**: Delete "Universal Memory Capture.app"  
3. **Remove auto-start** (if configured):
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.universalmemory.globalcapture.plist
   rm ~/Library/LaunchAgents/com.universalmemory.globalcapture.plist
   ```
4. **Remove from Accessibility**: System Preferences → Security & Privacy → Accessibility

### 🆘 Need Help?

#### Built-in Help
- **Menu bar** 🧠 → "📖 Help" for feature overview
- **Settings dialog** shows current configuration
- **Status indicator** shows connection health

#### Troubleshooting Commands
```bash
# Check if app is running
ps aux | grep "Universal Memory Capture"

# Check memory service connection  
curl localhost:8091/api/health

# View app logs
grep "Universal Memory Capture" /var/log/system.log

# Test memory storage
curl -X POST localhost:8091/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"content": "Test capture", "source": "manual_test"}'
```

#### Log Locations
- **App Console**: Applications → Utilities → Console → search "Universal Memory Capture"
- **Memory Service**: Check your universal-memory-system directory
- **System Logs**: `/var/log/system.log` and Console app

---

## 🧠 Welcome to Universal Memory Capture!

**Never lose important information again. Capture knowledge from anywhere in macOS with a simple ⌘⇧M keystroke.**

The brain icon 🧠 in your menu bar is your gateway to system-wide memory capture. Start capturing context from every app you use!