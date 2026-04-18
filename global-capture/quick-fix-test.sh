#!/bin/bash
#
# Quick Fix Test Script for Global Capture Permission Issues
# This script rebuilds the app with the fixes and provides testing instructions
#

set -e

echo "🔧 Global Capture Permission Debug - Quick Fix"
echo "══════════════════════════════════════════════"

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ This fix is macOS-only"
    exit 1
fi

# Check if memory service is running
echo "🔍 Checking Memory Service status..."
if curl -s "http://localhost:8091/api/health" > /dev/null; then
    echo "✅ Memory Service is running"
else
    echo "⚠️  Memory Service not detected - make sure it's running:"
    echo "   cd ../src && python3 api_service.py --port 8091"
fi

# Kill existing app if running
echo "🔄 Stopping existing Global Capture app..."
pkill -f "Universal Memory Capture" || echo "   (No existing app running)"

# Rebuild with fixes
echo "🔨 Rebuilding with permission fixes..."
if ./build.sh; then
    echo "✅ Build successful"
else
    echo "❌ Build failed - check Swift compilation errors above"
    exit 1
fi

# Install the updated app
echo "📦 Installing updated app..."
if cd build && ./install.sh; then
    echo "✅ Installation successful"
else
    echo "❌ Installation failed"
    exit 1
fi

# Launch the app
echo "🚀 Launching Global Capture with fixes..."
open "/Applications/Universal Memory Capture.app"

# Wait for app to start
sleep 2

echo ""
echo "🧪 Testing Instructions:"
echo "═══════════════════════════"
echo ""
echo "1. 📋 Check Menu Bar:"
echo "   • Look for brain icon 🧠 in menu bar"
echo "   • Click it to open menu"
echo "   • Check if items are enabled (not grayed out)"
echo ""
echo "2. 🔐 Check Permissions:"
echo "   • Menu should show permission status"
echo "   • If 'Need Accessibility Access' - click to open System Preferences"
echo "   • Grant permission and wait 2-3 seconds for auto-detection"
echo ""
echo "3. ⌨️  Test Global Hotkey:"
echo "   • Select some text anywhere (Terminal, Safari, etc.)"
echo "   • Press ⌘⇧M (Cmd+Shift+M)"
echo "   • Should show capture dialog with text preview"
echo ""
echo "4. 📝 Test Menu Functions:"
echo "   • Click brain icon → Quick Note (should work)"
echo "   • Click brain icon → Capture Selection (should work)"
echo ""
echo "5. 🔍 Verify in Memory System:"
echo "   • Run: python3 ../src/memory_cli.py ask \"What are my recent captures?\""
echo "   • Should show captured content"
echo ""
echo "📊 Debug Information:"
echo "═════════════════════"
echo ""
echo "Memory Service Health:"
curl -s "http://localhost:8091/api/health" | python3 -m json.tool 2>/dev/null || echo "   Memory service not responding"
echo ""
echo "App Process Status:"
ps aux | grep "Universal Memory Capture" | grep -v grep || echo "   App not running"
echo ""
echo "Permission Check:"
if command -v osascript &> /dev/null; then
    osascript -e 'tell application "System Events" to get processes' > /dev/null 2>&1 && \
        echo "   ✅ osascript accessibility test passed" || \
        echo "   ❌ osascript accessibility test failed"
fi
echo ""
echo "📚 If Issues Persist:"
echo "═══════════════════════"
echo "1. Check Console app for 'Universal Memory Capture' logs"
echo "2. Verify System Preferences → Security & Privacy → Accessibility"
echo "3. Try restarting the app: pkill -f 'Universal Memory Capture' && open '/Applications/Universal Memory Capture.app'"
echo "4. Check memory service: curl localhost:8091/api/health"
echo ""
echo "🎯 Expected Working State:"
echo "• Brain icon visible in menu bar"
echo "• Menu items enabled (not grayed out)"
echo "• ⌘⇧M shows capture dialog"
echo "• Captures appear in memory system"
echo ""
echo "Good luck! The fixes should resolve the permission detection issues."