#!/bin/bash
#
# Universal AI Memory - Global Capture Build Script
# Compiles and packages the macOS Global Capture Service
#

set -e

echo "🧠 Building Universal AI Memory - Global Capture Service"
echo "════════════════════════════════════════════════════════"

# Configuration
APP_NAME="Universal Memory Capture"
BUNDLE_ID="com.universalmemory.globalcapture"
VERSION="1.0.0"
BUILD_DIR="./build"
APP_DIR="$BUILD_DIR/$APP_NAME.app"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create app bundle structure
echo "📁 Creating app bundle structure..."
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Compile Swift code
echo "⚡ Compiling Swift code..."

# Detect architecture for universal binary support
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    TARGET="arm64-apple-macos11.0"
    MIN_VERSION="11.0"
else
    TARGET="x86_64-apple-macos10.15"
    MIN_VERSION="10.15"
fi

echo "Building for architecture: $ARCH, target: $TARGET"

swiftc -O \
    -target "$TARGET" \
    -framework Cocoa \
    -framework AppKit \
    -framework Foundation \
    main.swift \
    ImplementationQueueWindow.swift \
    -o "$APP_DIR/Contents/MacOS/$APP_NAME"

# Check compilation result
if [ $? -eq 0 ]; then
    echo "✅ Swift compilation successful"
else
    echo "❌ Swift compilation failed"
    exit 1
fi

# Create Info.plist
echo "📄 Creating Info.plist..."
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>$MIN_VERSION</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>LSBackgroundOnly</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>NSAccessibilityEnabled</key>
    <true/>
    <key>NSAppleEventsUsageDescription</key>
    <string>Universal Memory Capture needs Apple Events access to capture text selections from other applications for your personal memory system.</string>
    <key>NSSystemAdministrationUsageDescription</key>
    <string>Universal Memory Capture needs system access to monitor global hotkeys and capture text from any application for your personal memory system.</string>
    <key>NSUserNotificationUsageDescription</key>
    <string>Universal Memory Capture shows notifications when memories are captured successfully.</string>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsLocalNetworking</key>
        <true/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>localhost</key>
            <dict>
                <key>NSExceptionAllowsInsecureHTTPLoads</key>
                <true/>
            </dict>
        </dict>
    </dict>
</dict>
</plist>
EOF

# Create application icon (using SF Symbols)
echo "🎨 Creating application icon..."
# Note: In a full implementation, you'd use iconutil to create proper .icns files
# For now, we'll use the system brain symbol in the app

# Create uninstaller script
echo "🗑️  Creating uninstaller script..."
cat > "$BUILD_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
echo "🗑️  Uninstalling Universal Memory Capture..."

# Kill the app if running
pkill -f "Universal Memory Capture" || true

# Remove from Applications
if [ -d "/Applications/Universal Memory Capture.app" ]; then
    rm -rf "/Applications/Universal Memory Capture.app"
    echo "✅ Removed from Applications folder"
fi

# Remove from Login Items (requires user action)
echo "ℹ️  Please remove 'Universal Memory Capture' from:"
echo "   System Preferences > Users & Groups > Login Items"

echo "✅ Uninstall complete"
EOF
chmod +x "$BUILD_DIR/uninstall.sh"

# Create installer script
echo "📦 Creating installer script..."
cat > "$BUILD_DIR/install.sh" << 'EOF'
#!/bin/bash
echo "🧠 Installing Universal Memory Capture..."

# Check if Universal Memory System is running
if ! curl -s "http://localhost:8091/api/health" > /dev/null; then
    echo "⚠️  Warning: Universal Memory System API not detected at localhost:8091"
    echo "   Please ensure the memory service is running before using Global Capture"
fi

# Copy to Applications folder
if [ -d "/Applications/Universal Memory Capture.app" ]; then
    echo "🔄 Removing existing installation..."
    rm -rf "/Applications/Universal Memory Capture.app"
fi

cp -R "Universal Memory Capture.app" "/Applications/"
echo "✅ Copied to Applications folder"

# Set permissions
chmod +x "/Applications/Universal Memory Capture.app/Contents/MacOS/Universal Memory Capture"

echo "🎉 Installation complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Launch 'Universal Memory Capture' from Applications"
echo "2. Grant Accessibility permissions when prompted"
echo "3. Look for the brain icon (🧠) in your menu bar"
echo "4. Use ⌘⇧M (Cmd+Shift+M) to capture anywhere in macOS"
echo ""
echo "🔐 Security Note:"
echo "This app requires Accessibility access to capture text selections"
echo "and monitor clipboard across all applications."
EOF
chmod +x "$BUILD_DIR/install.sh"

# Create README for distribution
echo "📖 Creating distribution README..."
cat > "$BUILD_DIR/README.md" << 'EOF'
# Universal AI Memory - Global Capture Service

System-wide memory capture for macOS that seamlessly integrates with your Universal AI Memory System.

## ✨ Features

- **Global Hotkey**: Press `⌘⇧M` anywhere to capture selected text or current context
- **Smart Clipboard Monitoring**: Automatically captures meaningful clipboard content
- **Context-Aware**: Detects active applications and projects for intelligent categorization  
- **Cross-App Integration**: Works with Xcode, VS Code, Terminal, browsers, and any macOS app
- **OCR Support**: Extracts text from screenshots and images
- **Menu Bar Interface**: Quick access to capture functions and settings

## 🚀 Installation

1. Run the installer: `./install.sh`
2. Launch "Universal Memory Capture" from Applications
3. Grant Accessibility permissions when prompted
4. Look for the brain icon (🧠) in your menu bar

## 🔥 Usage

### Global Hotkey
- **⌘⇧M**: Capture selected text or current window context

### Menu Bar Features
- 📝 Quick Note: Create instant memory notes
- 📸 Capture Selection: Manual text capture
- 🖼️ Capture Screen Area: OCR text from screenshots
- 📋 Toggle clipboard monitoring
- ⚙️ Settings and preferences

### Smart Features
- **Project Detection**: Automatically detects git repositories, Xcode projects, VS Code workspaces
- **App-Aware Categorization**: Different behavior for development tools, browsers, text editors
- **Content Filtering**: Skips passwords, API keys, and sensitive data
- **Intelligent Tagging**: Auto-tags based on content and context

## 🔧 Configuration

The service connects to your Universal Memory System API at `localhost:8091` by default.

### Settings Access
- Click the brain icon in menu bar → Settings
- Configure clipboard monitoring, hotkeys, and filters

## 🔐 Security & Privacy

- **Local Processing**: All analysis happens on your Mac
- **Accessibility Required**: Needed to read text selections across apps
- **Smart Filtering**: Automatically skips sensitive content like passwords
- **No Network Data**: Only communicates with your local memory service

## 🗑️ Uninstallation

Run the uninstaller: `./uninstall.sh`

## 🆘 Troubleshooting

### Common Issues

**"Accessibility Access Required" Dialog**
- Go to System Preferences > Security & Privacy > Accessibility
- Add "Universal Memory Capture" to the allowed applications

**Global Hotkey Not Working**
- Ensure Accessibility permissions are granted
- Check for conflicts with other global hotkey apps
- Try restarting the application

**Memory Service Connection Failed**
- Verify Universal Memory System is running: `curl localhost:8091/api/health`
- Check memory service logs for connection issues
- Ensure no firewall blocking localhost:8091

**Clipboard Monitoring Not Capturing**
- Content must be >10 characters and meaningful text
- Sensitive patterns (passwords, tokens) are automatically filtered
- Check menu bar toggle for clipboard monitoring status

### Debug Information
- Check Console app for "Universal Memory Capture" logs
- Memory service logs available in your Universal Memory System directory
- Use menu bar → Help for feature overview

## 🔗 Integration

Works seamlessly with:
- Universal AI Memory System (required)
- Browser Extension for AI platforms
- GitHub Integration for repository context
- Any macOS application that supports text selection

## 📊 System Requirements

- macOS 10.15 (Catalina) or later
- Universal Memory System running locally
- Accessibility permissions for cross-app capture
EOF

# Create distribution package
echo "📦 Creating distribution package..."
tar -czf "$BUILD_DIR/universal-memory-capture-macos.tar.gz" -C "$BUILD_DIR" \
    "Universal Memory Capture.app" \
    "install.sh" \
    "uninstall.sh" \
    "README.md"

echo "✅ Build complete!"
echo ""
echo "📁 Files created:"
echo "   - $APP_DIR"
echo "   - $BUILD_DIR/install.sh"
echo "   - $BUILD_DIR/uninstall.sh" 
echo "   - $BUILD_DIR/README.md"
echo "   - $BUILD_DIR/universal-memory-capture-macos.tar.gz"
echo ""
echo "🚀 To install: cd $BUILD_DIR && ./install.sh"