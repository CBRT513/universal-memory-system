#!/usr/bin/env swift

import Foundation
import ApplicationServices

// Direct permission test to diagnose the issue
func testAccessibilityPermission() {
    print("🔍 Direct Accessibility Permission Test")
    print("═══════════════════════════════════════")
    
    // Test 1: Basic AXIsProcessTrusted check
    let isTrusted = AXIsProcessTrusted()
    print("AXIsProcessTrusted(): \(isTrusted)")
    
    // Test 2: Check with prompt option
    let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): false] // Don't prompt
    let isTrustedNoPrompt = AXIsProcessTrustedWithOptions(options as CFDictionary)
    print("AXIsProcessTrustedWithOptions (no prompt): \(isTrustedNoPrompt)")
    
    // Test 3: System Events test
    do {
        let script = """
        tell application "System Events"
            set processList to name of every process
            return count of processList
        end tell
        """
        
        let appleScript = NSAppleScript(source: script)
        var error: NSDictionary?
        let result = appleScript?.executeAndReturnError(&error)
        
        if let error = error {
            print("AppleScript test: ❌ Failed - \(error)")
        } else if let result = result {
            print("AppleScript test: ✅ Success - Found \(result.stringValue ?? "unknown") processes")
        }
    }
    
    print("\n🔧 Diagnosis:")
    if isTrusted {
        print("✅ Accessibility permission is GRANTED")
        print("   The issue is likely in the Swift app's detection logic")
    } else {
        print("❌ Accessibility permission is NOT granted")
        print("   Need to grant permission in System Preferences")
        print("   Location: System Settings → Privacy & Security → Accessibility")
    }
    
    print("\n💡 Next Steps:")
    if isTrusted {
        print("1. The permission detection in the Swift app needs to be fixed")
        print("2. Check console output from the running app")
        print("3. The app may not be calling AXIsProcessTrusted() correctly")
    } else {
        print("1. Open System Settings")
        print("2. Go to Privacy & Security → Accessibility") 
        print("3. Add 'Universal Memory Capture' and enable it")
        print("4. Restart the app after granting permission")
    }
}

testAccessibilityPermission()