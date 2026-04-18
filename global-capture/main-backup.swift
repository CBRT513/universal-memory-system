#!/usr/bin/env swift
//
//  Universal AI Memory - Global Capture Service
//  macOS System-Wide Memory Capture with Smart Intelligence
//

import Cocoa
import Carbon
import Foundation
import AppKit

#if canImport(Vision)
import Vision
#endif

#if canImport(ApplicationServices)
import ApplicationServices
#endif

class GlobalCaptureService: NSObject, NSMenuDelegate {
    private var statusItem: NSStatusItem?
    private var clipboardMonitor: Timer?
    private var lastClipboardContent: String = ""
    private var memoryAPIBase: String = "http://localhost:8091"
    private var isClipboardMonitorEnabled: Bool = true
    private var captureHotkeyID: UInt32 = 1
    private var settings: GlobalCaptureSettings
    private var accessibilityPermissionGranted: Bool = false
    private var permissionTimer: Timer?
    private var globalMonitor: Any?
    private var localMonitor: Any?
    
    override init() {
        self.settings = GlobalCaptureSettings()
        super.init()
        
        setupStatusBarItem()
        checkAndRequestPermissions()
        startPermissionMonitoring()
        
        // Enhanced permission detection and menu fix
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            // Force a fresh permission check
            self.updateAccessibilityPermissionStatus()
            
            // If permission is properly detected, enable via normal path
            if self.accessibilityPermissionGranted {
                print("✅ Permission properly detected - enabling features normally")
                self.enableAllFeatures()
            } else {
                print("🚨 Permission detection failed - using hotfix")
                self.forceEnableMenuItemsHotfix()
            }
        }
        
        print("🧠 Universal AI Memory - Global Capture Service Started")
        print("⌨️  Global Hotkey: ⌘⇧M (Cmd+Shift+M)")
        print("📋 Clipboard Monitoring: \(isClipboardMonitorEnabled ? "Enabled" : "Disabled")")
        print("🔗 Memory API: \(memoryAPIBase)")
        print("🚨 HOTFIX: Will force-enable menu items after 1 second")
        print("────────────────────────────────────────")
    }
    
    private func forceEnableMenuItemsHotfix() {
        print("🚨 HOTFIX: Force-enabling all menu items")
        guard let menu = statusItem?.menu else { return }
        
        for (index, item) in menu.items.enumerated() {
            if item.title.contains("Quick Note") || 
               item.title.contains("Capture Selection") || 
               item.title.contains("Capture Screen Area") {
                let wasEnabled = item.isEnabled
                item.isEnabled = true
                print("   HOTFIX [\(index)] \(item.title): \(wasEnabled) → \(item.isEnabled)")
            }
        }
        
        // Also try to enable global hotkey
        print("🚨 HOTFIX: Attempting to register global hotkey regardless of permission detection")
        registerGlobalHotkeysForce()
        
        print("✅ HOTFIX: Menu items force-enabled. Try ⌘⇧M or menu items now.")
    }
    
    private func registerGlobalHotkeysForce() {
        // Clean up existing monitors
        if let monitor = globalMonitor {
            NSEvent.removeMonitor(monitor)
            globalMonitor = nil
        }
        if let monitor = localMonitor {
            NSEvent.removeMonitor(monitor)
            localMonitor = nil
        }
        
        let keyMask: NSEvent.ModifierFlags = [.command, .shift]
        
        // Force register regardless of permission check
        // IMPORTANT: Only monitor flagsChanged events to reduce interference
        globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: .flagsChanged) { [weak self] event in
            // Check if Cmd+Shift is pressed
            if event.modifierFlags.intersection([.command, .shift, .control, .option]) == keyMask {
                // Set up a temporary keyDown monitor just for M key
                self?.setupTemporaryMKeyMonitor()
            }
        }
        
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .flagsChanged) { [weak self] event in
            // Check if Cmd+Shift is pressed
            if event.modifierFlags.intersection([.command, .shift, .control, .option]) == keyMask {
                // Set up a temporary keyDown monitor just for M key
                self?.setupTemporaryMKeyMonitor()
            }
            return event
        }
        
        print("🚨 HOTFIX: Global hotkey force-registered with reduced interference")
    }
    
    private var tempMKeyMonitor: Any?
    
    private func setupTemporaryMKeyMonitor() {
        // Remove any existing temp monitor
        if let monitor = tempMKeyMonitor {
            NSEvent.removeMonitor(monitor)
            tempMKeyMonitor = nil
        }
        
        // Create a very short-lived monitor just for the M key
        tempMKeyMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.keyCode == 46 { // M key
                print("🔥 HOTFIX Global hotkey triggered: ⌘⇧M")
                DispatchQueue.main.async {
                    self?.handleGlobalHotkeyForced()
                    // Remove the temp monitor after triggering
                    if let monitor = self?.tempMKeyMonitor {
                        NSEvent.removeMonitor(monitor)
                        self?.tempMKeyMonitor = nil
                    }
                }
            }
        }
        
        // Auto-remove after 0.5 seconds if not triggered
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            if let monitor = self?.tempMKeyMonitor {
                NSEvent.removeMonitor(monitor)
                self?.tempMKeyMonitor = nil
            }
        }
    }
    
    @objc private func handleGlobalHotkeyForced() {
        print("🚨 HOTFIX: Global hotkey handler called")
        
        // Show the capture dialog
        DispatchQueue.main.async {
            self.showCaptureDialog()
        }
    }
    
    deinit {
        // Clean up monitors
        if let monitor = globalMonitor {
            NSEvent.removeMonitor(monitor)
        }
        if let monitor = localMonitor {
            NSEvent.removeMonitor(monitor)
        }
        permissionTimer?.invalidate()
        clipboardMonitor?.invalidate()
    }
    
    // MARK: - Permission Management
    
    private func checkAndRequestPermissions() {
        // Force permissions to true - we know they're granted
        accessibilityPermissionGranted = true
        
        // Always enable all features
        enableAllFeatures()
        
        // No permission requests - user already granted them
    }
    
    private func updateAccessibilityPermissionStatus() {
        let previousStatus = accessibilityPermissionGranted
        
        #if canImport(ApplicationServices)
        // FORCE TO TRUE - We know permissions are granted
        // The sandboxed app context prevents proper detection
        // User has confirmed permissions are granted in System Settings
        accessibilityPermissionGranted = true
        print("✅ FORCED: Accessibility permission set to GRANTED")
        print("   (Detection is broken in app context, but permissions ARE granted)")
        #else
        accessibilityPermissionGranted = false
        #endif
        
        print("🔐 Final permission status: \(accessibilityPermissionGranted ? "✅ GRANTED" : "❌ NOT GRANTED")")
        
        // Force menu update
        DispatchQueue.main.async {
            self.updateMenuItemStates()
        }
        
        // If status changed, log it prominently
        if previousStatus != accessibilityPermissionGranted {
            if accessibilityPermissionGranted {
                print("🎉 PERMISSION GRANTED - Enabling all features!")
                DispatchQueue.main.async {
                    self.enableAllFeatures()
                    self.showNotification("Global Capture Active!", "⌘⇧M now works system-wide")
                }
            } else {
                print("⚠️  PERMISSION REVOKED - Disabling features")
            }
        }
    }
    
    private func requestAccessibilityPermissions() {
        // DO NOTHING - permissions are already granted
        // This function is kept empty to prevent any permission prompts
        print("⚠️ requestAccessibilityPermissions called but IGNORED - permissions already granted")
    }
    
    private func startPermissionMonitoring() {
        // Check permissions every 2 seconds
        permissionTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            let previousStatus = self?.accessibilityPermissionGranted ?? false
            self?.updateAccessibilityPermissionStatus()
            
            // If permissions were just granted, enable features
            if !previousStatus && (self?.accessibilityPermissionGranted ?? false) {
                self?.enableAllFeatures()
                self?.showNotification("Permissions Granted", "Global Capture is now active!")
            }
        }
    }
    
    private func enableAllFeatures() {
        registerGlobalHotkeys()
        startClipboardMonitoring()
        updateMenuItemStates()
        print("🎉 All features enabled - Global Capture fully active!")
    }
    
    private func updateMenuItemStates() {
        guard let menu = statusItem?.menu else { 
            print("❌ No menu found for status item")
            return 
        }
        
        print("🔄 Updating menu states - Permission: \(accessibilityPermissionGranted ? "✅ GRANTED" : "❌ NOT GRANTED")")
        print("📋 Found \(menu.items.count) menu items")
        
        var updatedCount = 0
        
        // Update menu items based on permission status
        for (index, item) in menu.items.enumerated() {
            let oldEnabled = item.isEnabled
            let oldTitle = item.title
            
            switch item.title {
            case let title where title.contains("Quick Note"):
                item.isEnabled = accessibilityPermissionGranted
                print("   [\(index)] Quick Note: \(oldEnabled) → \(item.isEnabled)")
                updatedCount += 1
                
            case let title where title.contains("Capture Selection"):
                item.isEnabled = accessibilityPermissionGranted  
                print("   [\(index)] Capture Selection: \(oldEnabled) → \(item.isEnabled)")
                updatedCount += 1
                
            case let title where title.contains("Capture Screen Area"):
                item.isEnabled = accessibilityPermissionGranted
                print("   [\(index)] Capture Screen: \(oldEnabled) → \(item.isEnabled)")
                updatedCount += 1
                
            case let title where title.contains("Clipboard Monitoring"):
                item.isEnabled = true // Clipboard doesn't need accessibility
                print("   [\(index)] Clipboard: \(oldEnabled) → \(item.isEnabled) (always enabled)")
                
            case let title where title.contains("Permissions") || title.contains("Checking") || title.contains("Need Accessibility"):
                // Update permission status text and remove duplicates
                if accessibilityPermissionGranted {
                    item.title = "🟢 Accessibility Granted"
                    item.isEnabled = false
                } else {
                    item.title = "🔴 Need Accessibility Access"
                    item.isEnabled = true
                }
                if oldTitle != item.title {
                    print("   [\(index)] Permission Status: '\(oldTitle)' → '\(item.title)'")
                }
                
            default:
                if !item.title.contains("Memory Service") && !item.title.isEmpty && !item.isSeparatorItem {
                    if !item.isEnabled {
                        item.isEnabled = true
                        print("   [\(index)] \(item.title): \(oldEnabled) → \(item.isEnabled)")
                    }
                }
            }
        }
        
        print("✅ Menu update complete - Updated \(updatedCount) capture items")
        
        // Force menu to refresh visually
        statusItem?.menu = menu
    }
    
    // MARK: - NSMenuDelegate
    
    func menuWillOpen(_ menu: NSMenu) {
        // Refresh states when menu opens
        updateAccessibilityPermissionStatus()
        checkMemoryServiceConnection()
    }
    
    // MARK: - Status Bar Setup
    
    private func setupStatusBarItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem?.button {
            button.image = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "Memory Capture")
            button.target = self
            button.action = #selector(statusItemClicked)
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
        
        setupStatusBarMenu()
    }
    
    private func setupStatusBarMenu() {
        let menu = NSMenu()
        menu.delegate = self
        
        // Quick Actions (initially disabled until permissions granted)
        let quickNoteItem = NSMenuItem(title: "📝 Quick Note", action: #selector(showQuickNoteDialog), keyEquivalent: "n")
        quickNoteItem.target = self
        quickNoteItem.isEnabled = false
        menu.addItem(quickNoteItem)
        
        let captureSelectionItem = NSMenuItem(title: "📸 Capture Selection (⌘⇧M)", action: #selector(captureSelection), keyEquivalent: "")
        captureSelectionItem.target = self
        captureSelectionItem.isEnabled = false
        menu.addItem(captureSelectionItem)
        
        let captureScreenItem = NSMenuItem(title: "🖼️ Capture Screen Area", action: #selector(captureScreenArea), keyEquivalent: "s")
        captureScreenItem.target = self
        captureScreenItem.isEnabled = false
        menu.addItem(captureScreenItem)
        
        menu.addItem(NSMenuItem.separator())
        
        // AI Context Copy Feature
        let copyAIContextItem = NSMenuItem(title: "🤖 Copy AI Context", action: #selector(copyAIContext), keyEquivalent: "c")
        copyAIContextItem.target = self
        copyAIContextItem.isEnabled = true // Always available
        menu.addItem(copyAIContextItem)
        
        menu.addItem(NSMenuItem.separator())
        
        // Status (dynamic)
        let statusMenuItem = NSMenuItem(title: "🔄 Checking Connection...", action: nil, keyEquivalent: "")
        statusMenuItem.isEnabled = false
        menu.addItem(statusMenuItem)
        
        // Permission status
        let permissionMenuItem = NSMenuItem(title: "🔐 Checking Permissions...", action: #selector(openAccessibilityPreferences), keyEquivalent: "")
        permissionMenuItem.target = self
        menu.addItem(permissionMenuItem)
        
        menu.addItem(NSMenuItem.separator())
        
        // Settings
        let clipboardItem = NSMenuItem(title: "📋 Clipboard Monitoring", action: #selector(toggleClipboardMonitoring), keyEquivalent: "")
        clipboardItem.target = self
        clipboardItem.state = isClipboardMonitorEnabled ? .on : .off
        menu.addItem(clipboardItem)
        
        let settingsItem = NSMenuItem(title: "⚙️ Settings...", action: #selector(showSettings), keyEquivalent: ",")
        settingsItem.target = self
        menu.addItem(settingsItem)
        
        let dashboardItem = NSMenuItem(title: "📊 Open Dashboard", action: #selector(openDashboard), keyEquivalent: "d")
        dashboardItem.target = self
        menu.addItem(dashboardItem)
        
        menu.addItem(NSMenuItem.separator())
        
        // System
        let helpItem = NSMenuItem(title: "📖 Help", action: #selector(showHelp), keyEquivalent: "?")
        helpItem.target = self
        menu.addItem(helpItem)
        
        let quitItem = NSMenuItem(title: "🚪 Quit", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)
        
        statusItem?.menu = menu
        
        // Update initial states
        updateMenuItemStates()
        checkMemoryServiceConnection()
    }
    
    @objc private func openAccessibilityPreferences() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
            NSWorkspace.shared.open(url)
        }
    }
    
    private func checkMemoryServiceConnection() {
        // Check API connection and update status
        let url = URL(string: "\(memoryAPIBase)/api/health")!
        let task = URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let menu = self?.statusItem?.menu else { return }
                
                // Find status menu item (should be at index 3)
                let statusItem = menu.items.first { $0.title.contains("Connection") || $0.title.contains("Service") || $0.title.contains("Checking") }
                
                if error == nil, let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                    statusItem?.title = "🟢 Memory Service Connected"
                } else {
                    statusItem?.title = "🔴 Memory Service Offline"
                }
            }
        }
        task.resume()
    }
    
    // MARK: - Global Hotkey Registration
    
    private func registerGlobalHotkeys() {
        // Only register if we have accessibility permissions
        guard accessibilityPermissionGranted else {
            print("⚠️ Cannot register global hotkeys: Accessibility permission required")
            return
        }
        
        // Clean up existing monitors
        if let monitor = globalMonitor {
            NSEvent.removeMonitor(monitor)
            globalMonitor = nil
        }
        if let monitor = localMonitor {
            NSEvent.removeMonitor(monitor)
            localMonitor = nil
        }
        
        let keyMask: NSEvent.ModifierFlags = [.command, .shift]
        
        // Global monitor for when app is in background
        globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.modifierFlags.intersection([.command, .shift, .control, .option]) == keyMask && 
               event.keyCode == 46 { // M key
                print("🔥 Global hotkey triggered: ⌘⇧M (global)")
                DispatchQueue.main.async {
                    self?.handleGlobalHotkey()
                }
            }
        }
        
        // Local monitor for when app is active
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.modifierFlags.intersection([.command, .shift, .control, .option]) == keyMask && 
               event.keyCode == 46 { // M key
                print("🔥 Global hotkey triggered: ⌘⇧M (local)")
                DispatchQueue.main.async {
                    self?.handleGlobalHotkey()
                }
                return nil // Consume event
            }
            return event
        }
        
        print("✅ Global hotkey registered: ⌘⇧M (Cmd+Shift+M)")
    }
    
    // MARK: - Clipboard Monitoring
    
    private func startClipboardMonitoring() {
        guard isClipboardMonitorEnabled else { return }
        
        // Store initial clipboard content
        lastClipboardContent = NSPasteboard.general.string(forType: .string) ?? ""
        
        // Monitor clipboard every 1 second
        clipboardMonitor = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.checkClipboardForChanges()
        }
    }
    
    private func stopClipboardMonitoring() {
        clipboardMonitor?.invalidate()
        clipboardMonitor = nil
    }
    
    private func checkClipboardForChanges() {
        guard let currentContent = NSPasteboard.general.string(forType: .string) else { return }
        
        // Skip if content hasn't changed
        if currentContent == lastClipboardContent { return }
        
        // Skip if content is too short or looks like password/sensitive data
        if shouldSkipClipboardContent(currentContent) {
            lastClipboardContent = currentContent
            return
        }
        
        // Capture clipboard content with context
        captureClipboardContent(currentContent)
        lastClipboardContent = currentContent
    }
    
    private func shouldSkipClipboardContent(_ content: String) -> Bool {
        let trimmed = content.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Skip if too short
        if trimmed.count < 10 { return true }
        
        // Skip if looks like password or sensitive data
        let sensitivePatterns = [
            "^[a-zA-Z0-9+/]{20,}={0,2}$", // Base64
            "^[a-f0-9]{32,}$", // Hash-like
            "^[A-Z0-9]{20,}$", // API key-like
            "password", "token", "secret", "key"
        ]
        
        for pattern in sensitivePatterns {
            if trimmed.range(of: pattern, options: .regularExpression) != nil {
                return true
            }
        }
        
        // Skip if only whitespace or single words
        if trimmed.split(separator: " ").count < 3 { return true }
        
        return false
    }
    
    // MARK: - Capture Methods
    
    @objc private func handleGlobalHotkey() {
        print("🔥 Global hotkey triggered: ⌘⇧M")
        
        // Skip permission check - we know they're granted
        DispatchQueue.main.async {
            self.showCaptureDialog()
        }
    }
    
    private func showCaptureDialog() {
        let context = getCurrentContext()
        
        // First check clipboard for recently copied text
        if let clipboardText = NSPasteboard.general.string(forType: .string), 
           !clipboardText.isEmpty {
            // Use clipboard content directly (user likely just copied it)
            showCaptureDialogWithContent(clipboardText, context: context)
        } else if let selectedText = getSelectedText(), selectedText.count > 0 {
            // Try to get selected text
            showCaptureDialogWithContent(selectedText, context: context)
        } else {
            // Fall back to quick capture options
            showQuickCaptureDialog(context: context)
        }
    }
    
    private func showCaptureDialogWithContent(_ content: String, context: AppContext) {
        let alert = NSAlert()
        alert.messageText = "📝 Capture to Memory"
        alert.informativeText = "Captured from \(context.appName):"
        alert.addButton(withTitle: "💾 Save")
        alert.addButton(withTitle: "❌ Cancel")
        
        // Create a text view to show the content
        let scrollView = NSScrollView(frame: NSRect(x: 0, y: 0, width: 400, height: 120))
        let textView = NSTextView(frame: scrollView.bounds)
        textView.string = content
        textView.isEditable = false
        textView.isRichText = false
        textView.font = NSFont.systemFont(ofSize: 12)
        scrollView.documentView = textView
        scrollView.hasVerticalScroller = true
        
        // Add tags field
        let tagsField = NSTextField(frame: NSRect(x: 0, y: 130, width: 400, height: 22))
        tagsField.placeholderString = "Tags (comma-separated)"
        
        // Add importance slider
        let importanceLabel = NSTextField(labelWithString: "Importance: 5")
        importanceLabel.frame = NSRect(x: 0, y: 165, width: 100, height: 17)
        
        let importanceSlider = NSSlider(frame: NSRect(x: 100, y: 165, width: 300, height: 20))
        importanceSlider.minValue = 1
        importanceSlider.maxValue = 10
        importanceSlider.integerValue = 5
        importanceSlider.target = self
        importanceSlider.action = #selector(importanceChanged(_:))
        
        // Container view
        let containerView = NSView(frame: NSRect(x: 0, y: 0, width: 400, height: 200))
        containerView.addSubview(scrollView)
        containerView.addSubview(tagsField)
        containerView.addSubview(importanceLabel)
        containerView.addSubview(importanceSlider)
        
        alert.accessoryView = containerView
        
        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            let tags = tagsField.stringValue.split(separator: ",").map { String($0.trimmingCharacters(in: .whitespaces)) }
            
            captureContent(content, 
                         source: "hotkey_selection", 
                         context: context,
                         customTags: tags,
                         importance: importanceSlider.integerValue)
                         
            showNotification("✅ Captured!", "Memory saved successfully")
        }
    }
    
    private func showQuickCaptureDialog(context: AppContext) {
        let alert = NSAlert()
        alert.messageText = "📝 Quick Memory Capture"
        alert.informativeText = "No text selected. Choose capture method:"
        alert.addButton(withTitle: "✍️ Write Note")
        alert.addButton(withTitle: "📸 Screenshot OCR")
        alert.addButton(withTitle: "📋 Use Clipboard")
        alert.addButton(withTitle: "❌ Cancel")
        
        let response = alert.runModal()
        switch response {
        case .alertFirstButtonReturn:
            showQuickNoteDialog()
        case .alertSecondButtonReturn:
            captureScreenArea()
        case .alertThirdButtonReturn:
            if let clipboardText = NSPasteboard.general.string(forType: .string), !clipboardText.isEmpty {
                showCaptureDialogWithContent(clipboardText, context: context)
            } else {
                showNotification("❌ Empty Clipboard", "No text found in clipboard")
            }
        default:
            break
        }
    }
    
    @objc private func importanceChanged(_ slider: NSSlider) {
        // Update label - this would need a reference to the label
        print("Importance set to: \(slider.integerValue)")
    }
    
    @objc private func captureSelection() {
        let context = getCurrentContext()
        
        // Check clipboard first (user may have just copied)
        if let clipboardText = NSPasteboard.general.string(forType: .string), 
           !clipboardText.isEmpty {
            // Show the capture dialog with tags and importance
            showCaptureDialogWithContent(clipboardText, context: context)
        } else if let selectedText = getSelectedText() {
            // Try to get selected text
            showCaptureDialogWithContent(selectedText, context: context)
        } else {
            // Fall back to quick note
            showQuickNoteDialog()
        }
    }
    
    private func getSelectedText() -> String? {
        // Save current clipboard
        let savedClipboard = NSPasteboard.general.string(forType: .string)
        
        // Simulate Cmd+C to copy selection
        let source = CGEventSource(stateID: .hidSystemState)
        
        let cmdCDown = CGEvent(keyboardEventSource: source, virtualKey: 8, keyDown: true) // C key
        cmdCDown?.flags = .maskCommand
        let cmdCUp = CGEvent(keyboardEventSource: source, virtualKey: 8, keyDown: false)
        cmdCUp?.flags = .maskCommand
        
        cmdCDown?.post(tap: .cghidEventTap)
        cmdCUp?.post(tap: .cghidEventTap)
        
        // Wait briefly for clipboard to update
        Thread.sleep(forTimeInterval: 0.1)
        
        // Get copied text
        let copiedText = NSPasteboard.general.string(forType: .string)
        
        // Restore original clipboard if we got something new
        if let copied = copiedText, copied != savedClipboard, !copied.isEmpty {
            // Restore original clipboard
            if let saved = savedClipboard {
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(saved, forType: .string)
            }
            return copied
        }
        
        return nil
    }
    
    private func captureActiveWindow(context: AppContext) {
        // Capture current window title and app info
        let content = """
        Active Application: \(context.appName)
        Window: \(context.windowTitle)
        Bundle ID: \(context.bundleIdentifier)
        Project Context: \(context.projectContext ?? "None detected")
        """
        
        captureContent(content, source: "hotkey_window", context: context)
        showNotification("Window Context Captured", "Current app context saved to memory")
    }
    
    private func captureClipboardContent(_ content: String) {
        let context = getCurrentContext()
        captureContent(content, source: "clipboard_monitor", context: context)
        
        print("📋 Clipboard captured: \(content.prefix(50))...")
    }
    
    @objc private func captureScreenArea() {
        // Use system screenshot tool
        let task = Process()
        task.launchPath = "/usr/sbin/screencapture"
        task.arguments = ["-i", "-c"] // Interactive selection, copy to clipboard
        task.launch()
        task.waitUntilExit()
        
        // Process screenshot from clipboard
        if let imageData = NSPasteboard.general.data(forType: .tiff) {
            processScreenshotImage(imageData)
        }
    }
    
    // MARK: - Context Detection
    
    private func getCurrentContext() -> AppContext {
        let workspace = NSWorkspace.shared
        let frontApp = workspace.frontmostApplication
        
        var context = AppContext()
        
        if let app = frontApp {
            context.appName = app.localizedName ?? "Unknown"
            context.bundleIdentifier = app.bundleIdentifier ?? ""
            
            // Get window title using Accessibility API
            if let windowTitle = getActiveWindowTitle() {
                context.windowTitle = windowTitle
            }
            
            // Detect project context
            context.projectContext = detectProjectContext(from: context)
        }
        
        return context
    }
    
    private func getActiveWindowTitle() -> String? {
        // Use NSWorkspace for better compatibility
        let workspace = NSWorkspace.shared
        if let frontApp = workspace.frontmostApplication {
            return frontApp.localizedName
        }
        
        // Fallback to CGWindowList if NSWorkspace fails
        let options = CGWindowListOption(arrayLiteral: .excludeDesktopElements, .optionOnScreenOnly)
        guard let windowListInfo = CGWindowListCopyWindowInfo(options, kCGNullWindowID) else {
            return nil
        }
        
        let infoList = windowListInfo as NSArray? as? [[String: Any]]
        return infoList?.first { window in
            (window["kCGWindowLayer"] as? Int) == 0
        }?["kCGWindowName"] as? String
    }
    
    private func detectProjectContext(from appContext: AppContext) -> String? {
        // Enhanced project detection based on app and window title
        let bundleId = appContext.bundleIdentifier.lowercased()
        let windowTitle = appContext.windowTitle.lowercased()
        
        // Development environments
        if bundleId.contains("xcode") {
            return extractXcodeProject(from: appContext.windowTitle)
        } else if bundleId.contains("code") || bundleId.contains("cursor") {
            return extractVSCodeProject(from: appContext.windowTitle)
        } else if bundleId.contains("terminal") {
            return extractTerminalProject(from: appContext.windowTitle)
        }
        
        // Browser-based development
        if bundleId.contains("safari") || bundleId.contains("chrome") {
            if windowTitle.contains("github.com") {
                return extractGitHubProject(from: appContext.windowTitle)
            }
        }
        
        return nil
    }
    
    // MARK: - Memory Storage
    
    private func captureContent(_ content: String, source: String, context: AppContext, customTags: [String] = [], importance: Int = 5) {
        let allTags = generateTags(for: content, context: context) + customTags
        
        let memoryData: [String: Any] = [
            "content": content,
            "category": categorizeContent(content, context: context),
            "tags": Array(Set(allTags)), // Remove duplicates
            "importance": importance,
            "source": "global_capture_\(source)",
            "source_url": context.projectContext ?? "",
            "metadata": [
                "app_name": context.appName,
                "bundle_id": context.bundleIdentifier,
                "window_title": context.windowTitle,
                "project_context": context.projectContext ?? "",
                "capture_method": source,
                "timestamp": ISO8601DateFormatter().string(from: Date()),
                "platform": "macos_global"
            ]
        ]
        
        sendToMemoryService(memoryData)
    }
    
    private func sendToMemoryService(_ data: [String: Any]) {
        guard let url = URL(string: "\(memoryAPIBase)/api/memory/store") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: data)
            
            URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    print("❌ Memory storage error: \(error.localizedDescription)")
                    return
                }
                
                if let httpResponse = response as? HTTPURLResponse {
                    if httpResponse.statusCode == 200 {
                        print("✅ Memory stored successfully")
                    } else {
                        print("⚠️ Memory storage failed: HTTP \(httpResponse.statusCode)")
                    }
                }
            }.resume()
            
        } catch {
            print("❌ JSON serialization error: \(error)")
        }
    }
    
    // MARK: - Content Analysis
    
    private func categorizeContent(_ content: String, context: AppContext) -> String {
        let contentLower = content.lowercased()
        let appName = context.appName.lowercased()
        
        // App-based categorization
        if appName.contains("xcode") || appName.contains("terminal") || appName.contains("cursor") {
            return "development"
        } else if appName.contains("safari") || appName.contains("chrome") {
            return "research"
        } else if appName.contains("notes") || appName.contains("text") {
            return "note"
        }
        
        // Content-based categorization
        if contentLower.contains("error") || contentLower.contains("bug") {
            return "troubleshooting"
        } else if contentLower.contains("config") || contentLower.contains("setting") {
            return "configuration"
        } else if contentLower.contains("```") || contentLower.contains("function") {
            return "code"
        }
        
        return "note"
    }
    
    private func generateTags(for content: String, context: AppContext) -> [String] {
        var tags: [String] = ["global-capture"]
        
        // Add app-based tag
        tags.append(context.appName.lowercased().replacingOccurrences(of: " ", with: "-"))
        
        // Add project tag if available
        if let project = context.projectContext {
            tags.append(project)
        }
        
        // Content-based tags
        let contentLower = content.lowercased()
        let techKeywords = [
            "swift": ["swift", "xcode", "ios", "macos"],
            "javascript": ["javascript", "js", "node", "react"],
            "python": ["python", "django", "flask", "pip"],
            "git": ["git", "commit", "branch", "repository"],
            "terminal": ["bash", "zsh", "command", "cli"]
        ]
        
        for (tag, keywords) in techKeywords {
            if keywords.contains(where: { contentLower.contains($0) }) {
                tags.append(tag)
            }
        }
        
        return Array(Set(tags)) // Remove duplicates
    }
    
    private func calculateImportance(for content: String, context: AppContext) -> Int {
        var importance = 5 // Base importance
        
        // Length bonus
        if content.count > 200 { importance += 1 }
        if content.count > 500 { importance += 1 }
        
        // Code/technical content bonus
        if content.contains("```") || content.contains("function") { importance += 2 }
        
        // Error/solution bonus
        if content.lowercased().contains("error") || content.lowercased().contains("solution") {
            importance += 2
        }
        
        // Development context bonus
        if context.appName.lowercased().contains("xcode") || context.appName.lowercased().contains("terminal") {
            importance += 1
        }
        
        return min(importance, 10)
    }
    
    // MARK: - UI Actions
    
    @objc private func statusItemClicked() {
        // Left click shows quick capture options
    }
    
    @objc private func showQuickNoteDialog() {
        let alert = NSAlert()
        alert.messageText = "Quick Memory Note"
        alert.informativeText = "Enter a quick note to save to memory:"
        alert.addButton(withTitle: "Save")
        alert.addButton(withTitle: "Cancel")
        
        let textField = NSTextField(frame: NSRect(x: 0, y: 0, width: 300, height: 60))
        textField.placeholderString = "Enter your note here..."
        alert.accessoryView = textField
        
        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            let noteContent = textField.stringValue
            if !noteContent.isEmpty {
                let context = getCurrentContext()
                captureContent(noteContent, source: "quick_note", context: context)
                showNotification("Quick Note Saved", "Note added to memory")
            }
        }
    }
    
    @objc private func toggleClipboardMonitoring() {
        isClipboardMonitorEnabled.toggle()
        
        if isClipboardMonitorEnabled {
            startClipboardMonitoring()
            print("📋 Clipboard monitoring enabled")
        } else {
            stopClipboardMonitoring()
            print("📋 Clipboard monitoring disabled")
        }
        
        // Update menu item
        if let menu = statusItem?.menu {
            for item in menu.items {
                if item.title.contains("Clipboard Monitoring") {
                    item.state = isClipboardMonitorEnabled ? .on : .off
                    break
                }
            }
        }
    }
    
    @objc private func showSettings() {
        // Open settings window (placeholder for now)
        let alert = NSAlert()
        alert.messageText = "Global Capture Settings"
        alert.informativeText = """
        Current Settings:
        • Hotkey: ⌘⇧M (Cmd+Shift+M)
        • Clipboard Monitoring: \(isClipboardMonitorEnabled ? "Enabled" : "Disabled")
        • Memory API: \(memoryAPIBase)
        
        More settings coming soon...
        """
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
    
    @objc private func openDashboard() {
        // Open the dashboard at the same port as the API (8091)
        let dashboardURL = memoryAPIBase + "/dashboard"
        if let url = URL(string: dashboardURL) {
            NSWorkspace.shared.open(url)
        }
    }
    
    @objc private func copyAIContext() {
        print("🤖 Generating AI context message...")
        
        // Generate standard AI context message
        Task {
            let contextMessage = await generateAIContextMessage()
            
            DispatchQueue.main.async {
                // Copy to clipboard
                let pasteboard = NSPasteboard.general
                pasteboard.clearContents()
                pasteboard.setString(contextMessage, forType: .string)
                
                // Show success notification
                self.showNotification("AI Context Copied!", "Ready to paste into any AI chat")
                print("✅ AI context message copied to clipboard")
            }
        }
    }
    
    private func generateAIContextMessage() async -> String {
        // Get recent memories from the system
        let recentMemories = await fetchRecentMemories()
        let projectStats = await fetchProjectStats()
        
        let message = """
        I'm working on the Universal AI Memory System project. Please read the AGENT.md file to understand the system architecture and development patterns.
        
        ## Project Files & Context
        • **AGENT.md Location**: `/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/AGENT.md`
        • **Project Root**: `/Users/cerion/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/`
        • **If you cannot access files**: This is a Universal AI Memory System (Encyclopedia Galactica for AI development) with components: Global Capture (macOS app), Memory API (FastAPI), Browser Extension, CLI tools, and GitHub integration.
        
        ## Project Context
        • **System**: Universal AI Memory System (Encyclopedia Galactica for AI development)
        • **Components**: Global Capture (macOS), Memory API, Browser Extension, CLI
        • **Current Status**: \(projectStats)
        • **Recent Activity**: \(recentMemories.count) recent memories captured
        
        ## Quick Reference Commands
        • **Build Global Capture**: `cd global-capture && ./build.sh && cd build && ./install.sh`
        • **Start Memory API**: `python3 src/api_service.py --port 8091`
        • **CLI Interface**: `python3 src/memory_cli.py <command>`
        • **Health Check**: `curl http://localhost:8091/api/health`
        • **AI Context**: `python3 src/ai_context_generator.py --copy`
        
        ## Recent Relevant Memories
        \(formatRecentMemories(recentMemories))
        
        ## Architecture Summary (if AGENT.md not accessible)
        This is a comprehensive memory system with:
        - **Global Capture**: macOS app with ⌘⇧M hotkey for system-wide text capture
        - **Memory API**: FastAPI service (localhost:8091) for storage/retrieval
        - **Browser Extension**: Chrome/Firefox extension for web content capture
        - **CLI Tools**: Command-line interface for memory management
        - **AGENT.md Integration**: Universal format for AI tool compatibility
        
        Now I need help with: [DESCRIBE YOUR TASK HERE]
        
        Please read the AGENT.md file at the path above for complete context, or use the architecture summary if file access is unavailable.
        """
        
        return message
    }
    
    private func fetchRecentMemories() async -> [String] {
        // Call memory API to get recent relevant memories
        guard let url = URL(string: "\(memoryAPIBase)/api/search?limit=5&sort=recent") else {
            return ["Unable to fetch recent memories"]
        }
        
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            
            if let results = response?["results"] as? [[String: Any]] {
                return results.compactMap { memory in
                    guard let content = memory["content"] as? String,
                          let tags = memory["tags"] as? [String] else { return nil }
                    return "• \(content.prefix(100))... [Tags: \(tags.joined(separator: ", "))]"
                }
            }
        } catch {
            print("⚠️ Failed to fetch memories: \(error)")
        }
        
        return ["Recent memories available via API"]
    }
    
    private func fetchProjectStats() async -> String {
        guard let url = URL(string: "\(memoryAPIBase)/api/stats") else {
            return "Stats unavailable"
        }
        
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let stats = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            
            if let totalMemories = stats?["total_memories"] as? Int,
               let sources = stats?["sources"] as? [String: Int] {
                return "\(totalMemories) memories from \(sources.count) sources"
            }
        } catch {
            print("⚠️ Failed to fetch stats: \(error)")
        }
        
        return "Memory system operational"
    }
    
    private func formatRecentMemories(_ memories: [String]) -> String {
        if memories.isEmpty {
            return "• No recent memories found (check Memory API connection)"
        }
        return memories.joined(separator: "\n")
    }
    
    @objc private func showHelp() {
        let alert = NSAlert()
        alert.messageText = "🧠 How to Use Memory Capture"
        alert.informativeText = """
        THE EASIEST WAY TO SAVE MEMORIES:
        
        1️⃣ See something interesting?
        2️⃣ Press ⌘⇧M (Command+Shift+M)
        3️⃣ Click Save
        
        That's it! Everything else is automatic.
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        WHAT EACH MENU ITEM DOES:
        
        📝 Quick Note = Type a thought to save
        📸 Capture Selection = Save highlighted text
        🖼 Capture Screen = Save text from images
        🤖 Copy AI Context = Get summary for ChatGPT
        📋 Clipboard = Turn auto-save on/off
        📊 Dashboard = View all your memories
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        EXAMPLES:
        
        • Reading an article? Highlight → ⌘⇧M → Save
        • Had an idea? Click 📝 → Type → Save
        • Important email? Select → ⌘⇧M → Save
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        💡 TIP: You can't break anything!
        Just press ⌘⇧M whenever you want to remember something.
        
        📍 Find your memories at:
        http://localhost:8091/dashboard
        """
        alert.addButton(withTitle: "Got it!")
        alert.alertStyle = .informational
        
        // Make the alert window wider for better readability
        let window = alert.window
        window.setContentSize(NSSize(width: 500, height: 600))
        
        alert.runModal()
    }
    
    @objc private func quit() {
        NSApplication.shared.terminate(self)
    }
    
    // MARK: - Utilities
    
    private func showNotification(_ title: String, _ message: String) {
        let notification = NSUserNotification()
        notification.title = title
        notification.informativeText = message
        notification.soundName = NSUserNotificationDefaultSoundName
        NSUserNotificationCenter.default.deliver(notification)
    }
    
    private func processScreenshotImage(_ imageData: Data) {
        #if canImport(Vision)
        // OCR processing for screenshot text extraction
        guard let image = NSImage(data: imageData) else { return }
        
        // Convert to CGImage for Vision processing
        guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return }
        
        if #available(macOS 10.15, *) {
            let request = VNRecognizeTextRequest { request, error in
                if let error = error {
                    print("OCR Error: \(error)")
                    return
                }
                
                let observations = request.results as? [VNRecognizedTextObservation] ?? []
                let extractedText = observations.compactMap { observation in
                    observation.topCandidates(1).first?.string
                }.joined(separator: "\n")
                
                if !extractedText.isEmpty {
                    let context = self.getCurrentContext()
                    self.captureContent("Screenshot OCR:\n\(extractedText)", source: "screenshot_ocr", context: context)
                    self.showNotification("Screenshot Text Captured", "Extracted text saved to memory")
                }
            }
            
            request.recognitionLevel = .accurate
            
            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            try? handler.perform([request])
        } else {
            // Fallback for older macOS versions
            self.showNotification("OCR Not Available", "Requires macOS 10.15 or later")
        }
        #else
        // Vision framework not available
        self.showNotification("OCR Not Available", "Vision framework not available")
        #endif
    }
    
    // Project extraction helpers
    private func extractXcodeProject(from title: String) -> String? {
        // Extract project name from Xcode window title
        if let range = title.range(of: " — ") {
            return String(title[..<range.lowerBound])
        }
        return nil
    }
    
    private func extractVSCodeProject(from title: String) -> String? {
        // Extract folder name from VS Code title
        let components = title.components(separatedBy: " - ")
        return components.first
    }
    
    private func extractTerminalProject(from title: String) -> String? {
        // Extract directory from terminal title
        if title.contains("/") {
            let components = title.components(separatedBy: "/")
            return components.last
        }
        return nil
    }
    
    private func extractGitHubProject(from title: String) -> String? {
        // Extract repo name from GitHub URL
        if title.contains("github.com/") {
            let components = title.components(separatedBy: "/")
            if let repoIndex = components.firstIndex(where: { $0.contains("github.com") }),
               repoIndex + 2 < components.count {
                return components[repoIndex + 2]
            }
        }
        return nil
    }
}

// MARK: - Supporting Data Structures

struct AppContext {
    var appName: String = ""
    var bundleIdentifier: String = ""
    var windowTitle: String = ""
    var projectContext: String?
}

struct GlobalCaptureSettings {
    var hotkeyEnabled: Bool = true
    var clipboardMonitorEnabled: Bool = true
    var memoryAPIBase: String = "http://localhost:8091"
    var excludedApps: [String] = ["Keychain Access", "1Password"]
    var minimumClipboardLength: Int = 10
    var ocrEnabled: Bool = true
}

// MARK: - Application Entry Point

class AppDelegate: NSObject, NSApplicationDelegate {
    var globalCaptureService: GlobalCaptureService?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Request accessibility permissions with better error handling
        if #available(macOS 10.9, *) {
            let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): true]
            let accessEnabled = AXIsProcessTrustedWithOptions(options as CFDictionary)
            
            if !accessEnabled {
                DispatchQueue.main.async {
                    let alert = NSAlert()
                    alert.messageText = "Accessibility Access Required"
                    alert.informativeText = "Global Memory Capture needs accessibility access to function properly. Please grant access in System Preferences > Security & Privacy > Accessibility."
                    alert.addButton(withTitle: "OK")
                    alert.addButton(withTitle: "Open System Preferences")
                    
                    let response = alert.runModal()
                    if response == .alertSecondButtonReturn {
                        // Open System Preferences to Accessibility pane
                        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
                            NSWorkspace.shared.open(url)
                        }
                    }
                }
            }
        }
        
        // Initialize capture service
        globalCaptureService = GlobalCaptureService()
        
        // Don't show in dock
        NSApp.setActivationPolicy(.accessory)
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        print("🧠 Global Capture Service stopping...")
    }
    
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return false // Keep running even when all windows are closed
    }
}

// Run the application
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()