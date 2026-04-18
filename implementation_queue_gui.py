#!/usr/bin/env python3
"""
Implementation Queue GUI - Standalone window for approving implementations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from implementation_queue import ImplementationQueue
import threading

class ImplementationQueueGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Implementation Queue - Pending Approvals")
        self.root.geometry("900x600")
        
        self.queue = ImplementationQueue()
        self.current_implementations = []
        self.selected_impl = None
        
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="Implementation Queue", font=("Helvetica", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Left panel - List
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        list_label = ttk.Label(left_frame, text="Pending Implementations:", font=("Helvetica", 12))
        list_label.pack(anchor="w")
        
        # Listbox with scrollbar
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill="both", expand=True, pady=(5, 0))
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set, width=40)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        # Right panel - Details
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky="nsew")
        
        details_label = ttk.Label(right_frame, text="Implementation Details:", font=("Helvetica", 12))
        details_label.pack(anchor="w")
        
        # Details text area
        self.details_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20)
        self.details_text.pack(fill="both", expand=True, pady=(5, 10))
        
        # Action buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill="x")
        
        self.approve_btn = ttk.Button(button_frame, text="✅ Approve", command=self.approve_impl, state="disabled")
        self.approve_btn.pack(side="left", padx=(0, 5))
        
        self.hold_btn = ttk.Button(button_frame, text="⏸️  Hold", command=self.hold_impl, state="disabled")
        self.hold_btn.pack(side="left", padx=(0, 5))
        
        self.deny_btn = ttk.Button(button_frame, text="❌ Deny", command=self.deny_impl, state="disabled")
        self.deny_btn.pack(side="left", padx=(0, 5))
        
        ttk.Separator(button_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        self.execute_btn = ttk.Button(button_frame, text="🚀 Execute Approved", command=self.execute_approved)
        self.execute_btn.pack(side="left")
        
        self.refresh_btn = ttk.Button(button_frame, text="🔄 Refresh", command=self.refresh_list)
        self.refresh_btn.pack(side="left", padx=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken")
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
    def refresh_list(self):
        """Refresh the list of pending implementations"""
        self.current_implementations = self.queue.get_pending_implementations()
        
        self.listbox.delete(0, tk.END)
        for impl in self.current_implementations:
            priority_symbol = {"high": "🔴", "medium": "🟠", "low": "🟢"}.get(impl["priority"], "⚪")
            type_symbol = {
                "package_install": "📦",
                "code_creation": "💻",
                "config_change": "⚙️"
            }.get(impl["implementation_type"], "📄")
            
            display_text = f"{priority_symbol} {type_symbol} {impl['description'][:40]}..."
            self.listbox.insert(tk.END, display_text)
        
        # Update status
        stats = self.queue.get_statistics()
        self.status_var.set(
            f"Pending: {stats['total_pending']} | "
            f"Approved: {stats['total_approved']} | "
            f"On Hold: {stats['total_on_hold']} | "
            f"Denied: {stats['total_denied']}"
        )
        
        # Clear details
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, "Select an implementation to view details...")
        self.selected_impl = None
        self.update_buttons()
    
    def on_select(self, event):
        """Handle selection in the list"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.current_implementations):
            self.selected_impl = self.current_implementations[index]
            self.show_details(self.selected_impl)
            self.update_buttons()
    
    def show_details(self, impl):
        """Show details of selected implementation"""
        self.details_text.delete(1.0, tk.END)
        
        details = f"""📋 IMPLEMENTATION DETAILS
{'='*50}

Type: {impl['implementation_type']}
Priority: {impl['priority'].upper()}
Status: {impl['status']}
Created: {impl['created_at']}

📰 Source Article:
{impl['article_title']}

📝 Description:
{impl['description']}

🔧 Implementation Details:
{json.dumps(impl['details'], indent=2)}

📊 Metadata:
{json.dumps(impl.get('metadata', {}), indent=2)}
"""
        self.details_text.insert(1.0, details)
    
    def update_buttons(self):
        """Update button states based on selection"""
        state = "normal" if self.selected_impl else "disabled"
        self.approve_btn["state"] = state
        self.hold_btn["state"] = state
        self.deny_btn["state"] = state
    
    def approve_impl(self):
        """Approve selected implementation"""
        if not self.selected_impl:
            return
        
        self.queue.approve_implementation(self.selected_impl["id"])
        messagebox.showinfo("Success", f"Implementation approved: {self.selected_impl['description']}")
        self.refresh_list()
    
    def hold_impl(self):
        """Put selected implementation on hold"""
        if not self.selected_impl:
            return
        
        self.queue.hold_implementation(self.selected_impl["id"])
        messagebox.showinfo("Success", f"Implementation put on hold: {self.selected_impl['description']}")
        self.refresh_list()
    
    def deny_impl(self):
        """Deny selected implementation"""
        if not self.selected_impl:
            return
        
        if messagebox.askyesno("Confirm", f"Deny implementation: {self.selected_impl['description']}?"):
            self.queue.deny_implementation(self.selected_impl["id"])
            messagebox.showinfo("Success", "Implementation denied")
            self.refresh_list()
    
    def execute_approved(self):
        """Execute all approved implementations"""
        if messagebox.askyesno("Execute Implementations", "Execute all approved implementations?"):
            def execute():
                results = self.queue.execute_approved_implementations()
                executed = len(results.get("executed", []))
                failed = len(results.get("failed", []))
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Execution Complete",
                    f"Successfully executed: {executed}\nFailed: {failed}"
                ))
                self.root.after(0, self.refresh_list)
            
            thread = threading.Thread(target=execute)
            thread.start()

def main():
    root = tk.Tk()
    app = ImplementationQueueGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()