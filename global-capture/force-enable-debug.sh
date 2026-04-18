#!/bin/bash
#
# Force Enable Debug - Immediate Fix for Grayed Out Menu Issue
#

echo "🔧 Force Enable Debug - Global Capture Menu Fix"
echo "══════════════════════════════════════════════════"

# Step 1: Test current permission status
echo "1️⃣ Testing current accessibility permission..."
swift permission-debug.swift

echo ""
echo "2️⃣ Checking if app is running..."
if pgrep -f "Universal Memory Capture" > /dev/null; then
    echo "✅ App is running (PID: $(pgrep -f 'Universal Memory Capture'))"
    
    echo ""
    echo "3️⃣ Checking Console logs for permission detection..."
    echo "Last 10 permission-related log entries:"
    log show --predicate 'process == "Universal Memory Capture"' --last 5m | grep -E "(permission|Accessibility|GRANTED|NOT GRANTED)" | tail -10 || echo "   No permission logs found"
    
else
    echo "❌ App is not running"
    echo "   Starting app..."
    open "/Applications/Universal Memory Capture.app"
    sleep 3
fi

echo ""
echo "4️⃣ Quick diagnosis based on screenshot:"
echo "   Menu shows: 'Memory Service Connected' ✅"
echo "   But all items grayed out ❌"
echo ""
echo "   This means:"
echo "   • API connection is working"
echo "   • Permission detection is failing"
echo "   • OR menu update logic has bug"

echo ""
echo "5️⃣ Immediate fixes to try:"
echo ""
echo "   🔧 Fix A: Grant permission manually"
echo "   1. Open System Settings"
echo "   2. Go to Privacy & Security → Accessibility"  
echo "   3. Find 'Universal Memory Capture' and enable it"
echo "   4. Wait 2-3 seconds for auto-detection"
echo ""
echo "   🔧 Fix B: Force app restart"
echo "   pkill -f 'Universal Memory Capture' && sleep 1 && open '/Applications/Universal Memory Capture.app'"
echo ""
echo "   🔧 Fix C: Rebuild with enhanced debugging"
echo "   cd .. && ./build.sh && cd build && ./install.sh"

echo ""
echo "6️⃣ Testing permission detection directly..."

# Create a test script to verify permission
cat > test-permission.swift << 'EOF'
#!/usr/bin/env swift
import ApplicationServices

let trusted = AXIsProcessTrusted()
print("Direct AXIsProcessTrusted() test: \(trusted)")

if trusted {
    print("✅ PERMISSION IS GRANTED")
    print("   → The Swift app's detection logic has a bug")
    print("   → Menu should be enabled but isn't")
} else {
    print("❌ PERMISSION NOT GRANTED")  
    print("   → Need to enable in System Settings")
    print("   → Privacy & Security → Accessibility")
}
EOF

swift test-permission.swift
rm test-permission.swift

echo ""
echo "7️⃣ Next steps based on result:"
echo ""
echo "   If permission IS granted:"
echo "   • The app has a detection bug"
echo "   • Rebuild with enhanced logging: ./build.sh"
echo "   • Check Console app for 'Universal Memory Capture' logs"
echo ""
echo "   If permission NOT granted:"
echo "   • Open System Settings → Privacy & Security → Accessibility"
echo "   • Add and enable 'Universal Memory Capture'"
echo "   • App should auto-detect within 2-3 seconds"

echo ""
echo "💡 The most likely issue:"
echo "   Based on your screenshot, permission detection logic"
echo "   in the Swift app is not working correctly."