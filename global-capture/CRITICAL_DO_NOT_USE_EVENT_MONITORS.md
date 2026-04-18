# ⚠️ CRITICAL: Never Use NSEvent Monitors for Global Hotkeys

## Problem Discovered (2025-08-14)
The Universal Memory Capture app was causing severe keyboard focus interference across all macOS applications, manifesting as:
- Colored focus rings appearing randomly
- Keyboard input interference
- Focus stealing from active applications
- General typing disruption

## Root Cause
The app was using NSEvent monitors to capture global hotkeys:

```swift
// ❌ NEVER DO THIS - CAUSES SYSTEM-WIDE INTERFERENCE
globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
    // This intercepts EVERY keypress system-wide!
}

localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
    // This also interferes with keyboard focus
}
```

## Why This Is Bad
1. **Intercepts ALL keyboard events** - Not just your hotkey
2. **Causes focus issues** - Creates colored focus rings and steals focus
3. **Degrades system performance** - Processing every keypress
4. **Poor user experience** - Interferes with normal typing
5. **Security concerns** - Appears like a keylogger

## The Correct Solution
Use Carbon's HotKey API for global hotkeys:

```swift
// ✅ CORRECT WAY - Only responds to specific hotkey
var hotkeyRef: EventHotKeyRef?
let hotkeyID = EventHotKeyID(signature: OSType("UMCS".fourCharCodeValue), id: 1)

// Register ⌘⇧M without interfering with other keys
RegisterEventHotKey(
    46,  // M key
    UInt32(cmdKey + shiftKey),
    hotkeyID,
    GetApplicationEventTarget(),
    0,
    &hotkeyRef
)
```

## Benefits of Carbon HotKey API
- **No interference** - Only triggers on exact hotkey combination
- **System integrated** - Works with macOS hotkey system
- **Performance** - No overhead of monitoring all events
- **Professional** - This is how pro apps handle global hotkeys

## Alternative Approaches (If Carbon Not Available)
1. **Menu bar shortcuts** - Use NSMenuItem key equivalents
2. **Local shortcuts only** - When app is focused
3. **Service shortcuts** - Register as system service
4. **Distributed notifications** - For inter-app communication

## Testing for Interference
Before deploying any keyboard monitoring:
1. Test typing in multiple apps
2. Look for focus rings or highlights
3. Check CPU usage during typing
4. Verify no input lag
5. Test with accessibility tools

## References
- [Apple Developer: Event Handling](https://developer.apple.com/documentation/appkit/mouse_keyboard_and_trackpad)
- [Carbon Event Manager Reference](https://developer.apple.com/documentation/carbon/carbon_event_manager)
- Original issue: User reported colored focus rings interfering with typing (2025-08-14)

## Remember
**If you're monitoring ALL keyboard events, you're doing it wrong.**
Global hotkeys should ONLY respond to their specific key combination.

---
*This documentation is critical for preventing future keyboard interference issues. Never use NSEvent monitors for global hotkeys.*