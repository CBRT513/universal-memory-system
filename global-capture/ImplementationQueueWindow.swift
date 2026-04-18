//
//  Implementation Queue Window
//  GUI for reviewing and approving pending implementations
//

import Cocoa
import Foundation

class ImplementationQueueWindow: NSObject, NSWindowDelegate, NSTableViewDataSource, NSTableViewDelegate {
    private var window: NSWindow!
    private var tableView: NSTableView!
    private var implementations: [[String: Any]] = []
    private var selectedImplementation: [String: Any]?
    private var detailsTextView: NSTextView!
    private var approveButton: NSButton!
    private var holdButton: NSButton!
    private var denyButton: NSButton!
    private var executeButton: NSButton!
    private var statusLabel: NSTextField!
    
    private let memoryAPIBase = "http://localhost:8091"
    
    override init() {
        super.init()
        setupWindow()
        loadPendingImplementations()
    }
    
    private func setupWindow() {
        // Create window
        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 900, height: 600),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        
        window.title = "🚀 Implementation Queue - Pending Approvals"
        window.center()
        window.delegate = self
        
        // Create content view
        let contentView = NSView(frame: window.contentRect(forFrameRect: window.frame))
        
        // Create split view
        let splitView = NSSplitView(frame: contentView.bounds)
        splitView.isVertical = true
        splitView.dividerStyle = .thin
        splitView.autoresizingMask = [.width, .height]
        
        // Left panel - List of implementations
        let leftPanel = NSView(frame: NSRect(x: 0, y: 0, width: 400, height: 600))
        
        // Title label
        let titleLabel = NSTextField(labelWithString: "Pending Implementations")
        titleLabel.font = NSFont.boldSystemFont(ofSize: 14)
        titleLabel.frame = NSRect(x: 10, y: 560, width: 380, height: 30)
        leftPanel.addSubview(titleLabel)
        
        // Table view with scroll view
        let scrollView = NSScrollView(frame: NSRect(x: 10, y: 50, width: 380, height: 500))
        scrollView.hasVerticalScroller = true
        scrollView.autohidesScrollers = false
        
        tableView = NSTableView(frame: scrollView.bounds)
        tableView.dataSource = self
        tableView.delegate = self
        
        // Add columns
        let typeColumn = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("type"))
        typeColumn.title = "Type"
        typeColumn.width = 100
        tableView.addTableColumn(typeColumn)
        
        let descColumn = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("description"))
        descColumn.title = "Description"
        descColumn.width = 200
        tableView.addTableColumn(descColumn)
        
        let priorityColumn = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("priority"))
        priorityColumn.title = "Priority"
        priorityColumn.width = 70
        tableView.addTableColumn(priorityColumn)
        
        scrollView.documentView = tableView
        leftPanel.addSubview(scrollView)
        
        // Status label
        statusLabel = NSTextField(labelWithString: "Loading...")
        statusLabel.font = NSFont.systemFont(ofSize: 11)
        statusLabel.textColor = NSColor.secondaryLabelColor
        statusLabel.frame = NSRect(x: 10, y: 10, width: 380, height: 30)
        leftPanel.addSubview(statusLabel)
        
        // Right panel - Details and actions
        let rightPanel = NSView(frame: NSRect(x: 400, y: 0, width: 500, height: 600))
        
        // Details title
        let detailsTitle = NSTextField(labelWithString: "Implementation Details")
        detailsTitle.font = NSFont.boldSystemFont(ofSize: 14)
        detailsTitle.frame = NSRect(x: 10, y: 560, width: 480, height: 30)
        rightPanel.addSubview(detailsTitle)
        
        // Details text view
        let detailsScrollView = NSScrollView(frame: NSRect(x: 10, y: 100, width: 480, height: 450))
        detailsScrollView.hasVerticalScroller = true
        
        detailsTextView = NSTextView(frame: detailsScrollView.bounds)
        detailsTextView.isEditable = false
        detailsTextView.isRichText = true
        detailsTextView.font = NSFont.monospacedSystemFont(ofSize: 12, weight: .regular)
        detailsTextView.string = "Select an implementation to view details..."
        
        detailsScrollView.documentView = detailsTextView
        rightPanel.addSubview(detailsScrollView)
        
        // Action buttons
        let buttonY: CGFloat = 50
        let buttonWidth: CGFloat = 100
        let buttonSpacing: CGFloat = 10
        
        approveButton = NSButton(frame: NSRect(x: 10, y: buttonY, width: buttonWidth, height: 30))
        approveButton.title = "✅ Approve"
        approveButton.bezelStyle = .rounded
        approveButton.target = self
        approveButton.action = #selector(approveImplementation)
        approveButton.isEnabled = false
        rightPanel.addSubview(approveButton)
        
        holdButton = NSButton(frame: NSRect(x: 10 + buttonWidth + buttonSpacing, y: buttonY, width: buttonWidth, height: 30))
        holdButton.title = "⏸ Hold"
        holdButton.bezelStyle = .rounded
        holdButton.target = self
        holdButton.action = #selector(holdImplementation)
        holdButton.isEnabled = false
        rightPanel.addSubview(holdButton)
        
        denyButton = NSButton(frame: NSRect(x: 10 + (buttonWidth + buttonSpacing) * 2, y: buttonY, width: buttonWidth, height: 30))
        denyButton.title = "❌ Deny"
        denyButton.bezelStyle = .rounded
        denyButton.target = self
        denyButton.action = #selector(denyImplementation)
        denyButton.isEnabled = false
        rightPanel.addSubview(denyButton)
        
        executeButton = NSButton(frame: NSRect(x: 10 + (buttonWidth + buttonSpacing) * 3, y: buttonY, width: 150, height: 30))
        executeButton.title = "🚀 Execute Approved"
        executeButton.bezelStyle = .rounded
        executeButton.keyEquivalent = "\r" // Enter key
        executeButton.target = self
        executeButton.action = #selector(executeApproved)
        rightPanel.addSubview(executeButton)
        
        // Refresh button
        let refreshButton = NSButton(frame: NSRect(x: 10, y: 10, width: 100, height: 30))
        refreshButton.title = "🔄 Refresh"
        refreshButton.bezelStyle = .rounded
        refreshButton.target = self
        refreshButton.action = #selector(refreshImplementations)
        rightPanel.addSubview(refreshButton)
        
        // Add panels to split view
        splitView.addSubview(leftPanel)
        splitView.addSubview(rightPanel)
        
        contentView.addSubview(splitView)
        window.contentView = contentView
    }
    
    func show() {
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    
    // MARK: - Data Loading
    
    private func loadPendingImplementations() {
        let url = URL(string: "\(memoryAPIBase)/api/implementations/pending")!
        
        let task = URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let pending = json["implementations"] as? [[String: Any]] {
                    self.implementations = pending
                    self.tableView.reloadData()
                    self.statusLabel.stringValue = "\(pending.count) pending implementations"
                } else {
                    // Fallback to Python queue API
                    self.loadFromPythonQueue()
                }
            }
        }
        task.resume()
    }
    
    private func loadFromPythonQueue() {
        // Call Python implementation queue directly
        let task = Process()
        task.launchPath = "/usr/bin/python3"
        task.arguments = ["-c", """
import sys
sys.path.insert(0, '/usr/local/share/universal-memory-system/src')
from implementation_queue import ImplementationQueue
import json

queue = ImplementationQueue()
pending = queue.get_pending_implementations()
print(json.dumps({"implementations": pending}))
"""]
        
        let pipe = Pipe()
        task.standardOutput = pipe
        
        task.launch()
        task.waitUntilExit()
        
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let pending = json["implementations"] as? [[String: Any]] {
            self.implementations = pending
            self.tableView.reloadData()
            self.statusLabel.stringValue = "\(pending.count) pending implementations"
        } else {
            self.statusLabel.stringValue = "No pending implementations"
        }
    }
    
    // MARK: - NSTableViewDataSource
    
    func numberOfRows(in tableView: NSTableView) -> Int {
        return implementations.count
    }
    
    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let impl = implementations[row]
        
        let cellView = NSTextField(labelWithString: "")
        cellView.font = NSFont.systemFont(ofSize: 12)
        
        switch tableColumn?.identifier.rawValue {
        case "type":
            let type = impl["implementation_type"] as? String ?? "unknown"
            let icon = getIconForType(type)
            cellView.stringValue = "\(icon) \(type)"
        case "description":
            cellView.stringValue = impl["description"] as? String ?? ""
            cellView.lineBreakMode = .byTruncatingTail
        case "priority":
            let priority = impl["priority"] as? String ?? "medium"
            let color = getColorForPriority(priority)
            cellView.stringValue = priority.capitalized
            cellView.textColor = color
        default:
            break
        }
        
        return cellView
    }
    
    func tableViewSelectionDidChange(_ notification: Notification) {
        let selectedRow = tableView.selectedRow
        
        if selectedRow >= 0 && selectedRow < implementations.count {
            selectedImplementation = implementations[selectedRow]
            updateDetailsView()
            enableActionButtons(true)
        } else {
            selectedImplementation = nil
            detailsTextView.string = "Select an implementation to view details..."
            enableActionButtons(false)
        }
    }
    
    // MARK: - Actions
    
    @objc private func approveImplementation() {
        guard let impl = selectedImplementation,
              let implId = impl["id"] as? Int else { return }
        
        updateImplementationStatus(implId, decision: "approve")
    }
    
    @objc private func holdImplementation() {
        guard let impl = selectedImplementation,
              let implId = impl["id"] as? Int else { return }
        
        updateImplementationStatus(implId, decision: "hold")
    }
    
    @objc private func denyImplementation() {
        guard let impl = selectedImplementation,
              let implId = impl["id"] as? Int else { return }
        
        updateImplementationStatus(implId, decision: "deny")
    }
    
    @objc private func executeApproved() {
        // Execute all approved implementations
        let task = Process()
        task.launchPath = "/usr/bin/python3"
        task.arguments = ["-c", """
import sys
sys.path.insert(0, '/usr/local/share/universal-memory-system/src')
from implementation_queue import ImplementationQueue
import json

queue = ImplementationQueue()
results = queue.execute_approved_implementations()
print(json.dumps(results))
"""]
        
        let pipe = Pipe()
        task.standardOutput = pipe
        
        task.launch()
        task.waitUntilExit()
        
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            showExecutionResults(json)
        }
        
        refreshImplementations()
    }
    
    @objc private func refreshImplementations() {
        loadPendingImplementations()
    }
    
    // MARK: - Helper Methods
    
    private func updateDetailsView() {
        guard let impl = selectedImplementation else { return }
        
        let details = impl["details"] as? [String: Any] ?? [:]
        let metadata = impl["metadata"] as? [String: Any] ?? [:]
        
        let detailsText = NSMutableAttributedString()
        
        // Title
        let titleAttr = [NSAttributedString.Key.font: NSFont.boldSystemFont(ofSize: 14)]
        detailsText.append(NSAttributedString(string: "📋 Implementation Details\n\n", attributes: titleAttr))
        
        // Basic info
        let infoAttr = [NSAttributedString.Key.font: NSFont.systemFont(ofSize: 12)]
        detailsText.append(NSAttributedString(string: "Type: \(impl["implementation_type"] as? String ?? "")\n", attributes: infoAttr))
        detailsText.append(NSAttributedString(string: "Priority: \(impl["priority"] as? String ?? "")\n", attributes: infoAttr))
        detailsText.append(NSAttributedString(string: "Article: \(impl["article_title"] as? String ?? "")\n", attributes: infoAttr))
        detailsText.append(NSAttributedString(string: "Description: \(impl["description"] as? String ?? "")\n\n", attributes: infoAttr))
        
        // Details section
        detailsText.append(NSAttributedString(string: "Details:\n", attributes: titleAttr))
        let detailsString = formatJSON(details)
        detailsText.append(NSAttributedString(string: detailsString, attributes: infoAttr))
        
        detailsTextView.textStorage?.setAttributedString(detailsText)
    }
    
    private func formatJSON(_ json: [String: Any]) -> String {
        guard let data = try? JSONSerialization.data(withJSONObject: json, options: .prettyPrinted),
              let string = String(data: data, encoding: .utf8) else {
            return "Unable to format details"
        }
        return string
    }
    
    private func updateImplementationStatus(_ implId: Int, decision: String) {
        // Call Python to update status
        let task = Process()
        task.launchPath = "/usr/bin/python3"
        task.arguments = ["-c", """
import sys
sys.path.insert(0, '/usr/local/share/universal-memory-system/src')
from implementation_queue import ImplementationQueue

queue = ImplementationQueue()
if '\(decision)' == 'approve':
    queue.approve_implementation(\(implId))
elif '\(decision)' == 'hold':
    queue.hold_implementation(\(implId))
elif '\(decision)' == 'deny':
    queue.deny_implementation(\(implId))
print('Success')
"""]
        
        task.launch()
        task.waitUntilExit()
        
        // Refresh list
        refreshImplementations()
    }
    
    private func enableActionButtons(_ enabled: Bool) {
        approveButton.isEnabled = enabled
        holdButton.isEnabled = enabled
        denyButton.isEnabled = enabled
    }
    
    private func getIconForType(_ type: String) -> String {
        switch type {
        case "package_install": return "📦"
        case "code_creation": return "💻"
        case "config_change": return "⚙️"
        default: return "📄"
        }
    }
    
    private func getColorForPriority(_ priority: String) -> NSColor {
        switch priority {
        case "high": return NSColor.systemRed
        case "medium": return NSColor.systemOrange
        case "low": return NSColor.systemGreen
        default: return NSColor.labelColor
        }
    }
    
    private func showExecutionResults(_ results: [String: Any]) {
        let executed = (results["executed"] as? [[String: Any]])?.count ?? 0
        let failed = (results["failed"] as? [[String: Any]])?.count ?? 0
        
        let alert = NSAlert()
        alert.messageText = "Execution Complete"
        alert.informativeText = "Successfully executed: \(executed)\nFailed: \(failed)"
        alert.alertStyle = executed > 0 ? .informational : .warning
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
    
    // MARK: - NSWindowDelegate
    
    func windowWillClose(_ notification: Notification) {
        // Clean up if needed
    }
}