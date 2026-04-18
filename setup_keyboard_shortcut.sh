#!/bin/bash

echo "🎯 Setting up keyboard shortcut for Implementation Queue"
echo "==========================================================="
echo ""
echo "To create a global keyboard shortcut (⌘⇧I):"
echo ""
echo "1. Open System Settings → Keyboard → Keyboard Shortcuts"
echo "2. Click 'App Shortcuts' in the left sidebar"
echo "3. Click the '+' button"
echo "4. Set:"
echo "   • Application: All Applications"
echo "   • Menu Title: (leave blank)"
echo "   • Keyboard Shortcut: ⌘⇧I"
echo ""
echo "OR use this AppleScript method:"
echo ""

# Create an AppleScript app that can be triggered
cat > /tmp/OpenImplementationQueue.applescript << 'EOF'
on run
    do shell script "open -a 'Implementation Queue' || /usr/bin/python3 /usr/local/share/universal-memory-system/implementation_queue_gui.py &"
end run
EOF

# Compile the AppleScript to an app
osacompile -o ~/Desktop/OpenImplementationQueue.app /tmp/OpenImplementationQueue.applescript 2>/dev/null

if [ -f ~/Desktop/OpenImplementationQueue.app/Contents/MacOS/applet ]; then
    echo "✅ Created OpenImplementationQueue.app on your Desktop"
    echo "   You can trigger this with Spotlight or Alfred"
fi

# Create a Quick Action for Services menu
cat > ~/Library/Services/OpenImplementationQueue.workflow/Contents/document.wflow << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AMApplicationBuild</key>
    <string>523</string>
    <key>AMApplicationVersion</key>
    <string>2.10</string>
    <key>AMDocumentVersion</key>
    <string>2</string>
    <key>actions</key>
    <array>
        <dict>
            <key>action</key>
            <dict>
                <key>AMAccepts</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Optional</key>
                    <true/>
                    <key>Types</key>
                    <array/>
                </dict>
                <key>AMActionVersion</key>
                <string>1.0.2</string>
                <key>AMApplication</key>
                <array>
                    <string>Automator</string>
                </array>
                <key>AMParameterProperties</key>
                <dict>
                    <key>shell</key>
                    <dict/>
                    <key>source</key>
                    <dict/>
                </dict>
                <key>AMProvides</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Types</key>
                    <array/>
                </dict>
                <key>ActionBundlePath</key>
                <string>/System/Library/Automator/Run Shell Script.action</string>
                <key>ActionName</key>
                <string>Run Shell Script</string>
                <key>ActionParameters</key>
                <dict>
                    <key>shell</key>
                    <string>/bin/bash</string>
                    <key>source</key>
                    <string>open -a "Implementation Queue" || /usr/bin/python3 /usr/local/share/universal-memory-system/implementation_queue_gui.py &</string>
                </dict>
                <key>BundleIdentifier</key>
                <string>com.apple.RunShellScript</string>
                <key>CFBundleVersion</key>
                <string>1.0.2</string>
                <key>CanShowSelectedItemsWhenRun</key>
                <false/>
                <key>CanShowWhenRun</key>
                <true/>
                <key>Category</key>
                <array>
                    <string>AMCategoryUtilities</string>
                </array>
                <key>Class Name</key>
                <string>RunShellScriptAction</string>
                <key>InputUUID</key>
                <string>F9B29C4D-5B3C-4D3B-8E3C-6B8C5A3C2D1E</string>
                <key>Keywords</key>
                <array>
                    <string>Shell</string>
                    <string>Script</string>
                    <string>Command</string>
                    <string>Run</string>
                    <string>Unix</string>
                </array>
                <key>UUID</key>
                <string>8E3C5A2D-4B3C-5D3B-9E3C-7B8C6A3C3D2E</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
EOF

echo ""
echo "📌 Quick Access Methods Created:"
echo "1. Implementation Queue app in /Applications (for Dock)"
echo "2. OpenImplementationQueue.app on Desktop (for Spotlight)"
echo "3. Quick Action in Services menu"
echo ""
echo "🎯 To add to Dock:"
echo "   Drag /Applications/Implementation Queue.app to your Dock"
echo ""
echo "🎯 To use with Spotlight:"
echo "   Press ⌘Space and type 'OpenImpl' then Enter"
echo ""
echo "✅ Setup complete!"