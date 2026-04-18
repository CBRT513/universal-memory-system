#!/usr/bin/env swift

import Foundation
import ApplicationServices

print("🔍 Testing Accessibility Permission Detection")
print("============================================")

// Test 1: Basic check
let basic = AXIsProcessTrusted()
print("1. AXIsProcessTrusted(): \(basic)")

// Test 2: Check with no prompt option
let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): false]
let noPrompt = AXIsProcessTrustedWithOptions(options as CFDictionary)
print("2. AXIsProcessTrustedWithOptions (no prompt): \(noPrompt)")

// Test 3: AppleScript test
do {
    let script = """
    tell application "System Events"
        return name of first process
    end tell
    """
    
    let appleScript = NSAppleScript(source: script)
    var error: NSDictionary?
    let result = appleScript?.executeAndReturnError(&error)
    
    if let error = error {
        print("3. AppleScript test: FAILED - \(error)")
    } else {
        print("3. AppleScript test: PASSED - \(result?.stringValue ?? "success")")
    }
}

print("")
print("🧠 For Universal Memory Capture app:")
if basic && noPrompt {
    print("✅ Permission is fully granted - app should work")
} else if basic || noPrompt {
    print("⚠️  Mixed results - possible detection issue")
} else {
    print("❌ Permission not granted - need to enable in System Settings")
}