#!/usr/bin/env python3
"""
Direct launcher for Implementation Queue GUI
Alternative way to access the queue without menu bar
"""

import sys
import os
sys.path.insert(0, '/usr/local/share/universal-memory-system/src')

from implementation_queue import ImplementationQueue
import subprocess
import json

def main():
    queue = ImplementationQueue()
    stats = queue.get_statistics()
    
    print("🚀 Implementation Queue Status")
    print("="*50)
    print(f"📋 Pending: {stats['total_pending']}")
    print(f"✅ Approved: {stats['total_approved']}")
    print(f"⏸️  On Hold: {stats['total_on_hold']}")
    print(f"❌ Denied: {stats['total_denied']}")
    
    if stats['total_pending'] > 0:
        print("\n📝 Pending Implementations:")
        pending = queue.get_pending_implementations()
        for impl in pending:
            print(f"  [{impl['priority']}] {impl['description']}")
        
        print("\n🎯 Actions:")
        print("1. View details")
        print("2. Approve all")
        print("3. Open web interface")
        print("0. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            for impl in pending:
                print(f"\n{'='*50}")
                print(f"📦 {impl['description']}")
                print(f"Type: {impl['implementation_type']}")
                print(f"Priority: {impl['priority']}")
                print(f"Article: {impl['article_title']}")
                print(f"Details: {json.dumps(impl['details'], indent=2)}")
                
                action = input("\n[A]pprove, [H]old, [D]eny, [S]kip: ").strip().lower()
                if action == 'a':
                    queue.approve_implementation(impl['id'])
                    print("✅ Approved!")
                elif action == 'h':
                    queue.hold_implementation(impl['id'])
                    print("⏸️  On hold!")
                elif action == 'd':
                    queue.deny_implementation(impl['id'])
                    print("❌ Denied!")
        
        elif choice == "2":
            for impl in pending:
                queue.approve_implementation(impl['id'])
            print(f"✅ Approved {len(pending)} implementations!")
            
            execute = input("\nExecute now? [y/n]: ").strip().lower()
            if execute == 'y':
                results = queue.execute_approved_implementations()
                print(f"🚀 Executed: {len(results['executed'])}")
                print(f"❌ Failed: {len(results['failed'])}")
    else:
        print("\n✨ No pending implementations!")

if __name__ == "__main__":
    main()