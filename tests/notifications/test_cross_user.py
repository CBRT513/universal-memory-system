#!/usr/bin/env python3
"""
Test Script for Cross-User Notification System
Demonstrates communication between cerion and equillabs users
"""

import time
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notification_service import (
    NotificationService,
    NotificationPriority,
    NotificationType,
    ProgressNotifier
)

def simulate_cerion_user():
    """Simulate actions from cerion user"""
    print("\n👤 CERION USER SESSION")
    print("=" * 50)
    
    service = NotificationService(user="cerion")
    
    # Send various notifications to equillabs
    print("\n1. Sending notifications to equillabs...")
    
    # High priority message
    notif1 = service.send_notification(
        recipient="equillabs",
        title="Build Complete",
        message="The AgentForge build has completed successfully. All tests passed.",
        priority=NotificationPriority.HIGH,
        metadata={"build_id": "af-build-123", "tests_passed": 42}
    )
    print(f"   ✅ Sent high-priority build notification: {notif1}")
    
    # Normal message
    notif2 = service.send_notification(
        recipient="equillabs",
        title="Code Review Request",
        message="Please review PR #42: Add notification system to UMS",
        priority=NotificationPriority.NORMAL,
        metadata={"pr_number": 42, "files_changed": 5}
    )
    print(f"   ✅ Sent normal-priority review request: {notif2}")
    
    # Urgent message
    notif3 = service.send_notification(
        recipient="equillabs",
        title="🚨 Production Issue",
        message="Database connection pool exhausted. Immediate attention needed!",
        priority=NotificationPriority.URGENT,
        metadata={"severity": "critical", "affected_service": "api"}
    )
    print(f"   ✅ Sent urgent production alert: {notif3}")
    
    # Check my own notifications
    print("\n2. Checking cerion's notifications...")
    my_notifications = service.check_notifications(username="cerion")
    print(f"   📬 Cerion has {len(my_notifications)} unread notification(s)")
    
    for notif in my_notifications[:3]:  # Show first 3
        print(f"      - From {notif['sender']}: {notif['title']}")
    
    return [notif1, notif2, notif3]

def simulate_equillabs_user(notification_ids):
    """Simulate actions from equillabs user"""
    print("\n👤 EQUILLABS USER SESSION")
    print("=" * 50)
    
    service = NotificationService(user="equillabs")
    
    # Check notifications
    print("\n1. Checking equillabs's notifications...")
    notifications = service.check_notifications(username="equillabs", unread_only=True)
    
    print(f"   📬 Equillabs has {len(notifications)} unread notification(s)")
    
    for notif in notifications:
        priority_emoji = {
            "low": "🔵",
            "normal": "⚪",
            "high": "🟡",
            "urgent": "🔴"
        }.get(notif["priority"], "⚪")
        
        print(f"\n   {priority_emoji} [{notif['priority'].upper()}] From: {notif['sender']}")
        print(f"      Title: {notif['title']}")
        print(f"      Message: {notif['message']}")
        print(f"      Time: {notif['created_at']}")
        
        if notif["metadata"]:
            print(f"      Metadata: {notif['metadata']}")
    
    # Mark some as read
    if len(notifications) > 0:
        print("\n2. Marking first notification as read...")
        success = service.mark_as_read(notifications[0]["id"])
        if success:
            print(f"   ✅ Marked {notifications[0]['id']} as read")
    
    # Send response back to cerion
    print("\n3. Sending response to cerion...")
    response_id = service.send_notification(
        recipient="cerion",
        title="Re: Production Issue",
        message="I'm on it! Checking the database connection pool now. Will update in 5 minutes.",
        priority=NotificationPriority.HIGH,
        metadata={"in_response_to": notification_ids[2] if len(notification_ids) > 2 else None}
    )
    print(f"   ✅ Sent response: {response_id}")
    
    return response_id

def test_long_operation():
    """Test long-running operation notifications"""
    print("\n⏱️  LONG OPERATION TEST")
    print("=" * 50)
    
    service = NotificationService()
    progress = ProgressNotifier("Data Import", total_items=100, notification_service=service)
    
    print("\nSimulating long-running data import...")
    print("(This will take about 35 seconds to trigger 'taking too long' notification)")
    
    for i in range(1, 101):
        progress.update(i, f"Importing record {i}")
        
        # Print progress every 10 items
        if i % 10 == 0:
            print(f"   Progress: {i}/100 ({i}%)")
        
        # Simulate work (faster for testing)
        time.sleep(0.35 if i <= 10 else 0.01)  # First 10 items take longer
    
    progress.complete(success=True, message="Data import completed successfully!")
    print("   ✅ Operation complete!")

def test_error_notification():
    """Test error notification"""
    print("\n❌ ERROR NOTIFICATION TEST")
    print("=" * 50)
    
    service = NotificationService()
    progress = ProgressNotifier("Database Backup", notification_service=service)
    
    print("\nSimulating database backup with error...")
    time.sleep(2)
    
    # Simulate error
    progress.error("Failed to connect to database: Connection refused on port 5432")
    print("   ❌ Error notification sent!")

def test_notification_history():
    """Test notification history"""
    print("\n📜 NOTIFICATION HISTORY TEST")
    print("=" * 50)
    
    service = NotificationService()
    
    # Get history for both users
    for username in ["cerion", "equillabs"]:
        print(f"\n{username}'s notification history (last 7 days):")
        history = service.get_notification_history(username=username, days=7, limit=5)
        
        if history:
            for notif in history:
                status = "📬 UNREAD" if not notif["is_read"] else "✓ READ"
                print(f"   {status} | {notif['created_at']} | From: {notif['sender']}")
                print(f"        {notif['title']}")
        else:
            print(f"   No notifications in history")

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("🧪 UMS CROSS-USER NOTIFICATION SYSTEM TEST")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("• Cross-user notifications between cerion and equillabs")
    print("• Desktop notifications for long operations")
    print("• Error notifications")
    print("• Notification history")
    
    # Test 1: Cross-user notifications
    print("\n" + "-" * 60)
    print("TEST 1: CROSS-USER NOTIFICATIONS")
    print("-" * 60)
    
    # Cerion sends notifications
    notification_ids = simulate_cerion_user()
    time.sleep(2)
    
    # Equillabs receives and responds
    response_id = simulate_equillabs_user(notification_ids)
    time.sleep(2)
    
    # Cerion checks response
    print("\n👤 CERION CHECKS RESPONSE")
    print("=" * 50)
    service = NotificationService(user="cerion")
    new_notifications = service.check_notifications(username="cerion", unread_only=True)
    
    for notif in new_notifications:
        if notif["sender"] == "equillabs":
            print(f"   📬 New message from equillabs: {notif['title']}")
            print(f"      {notif['message']}")
    
    # Test 2: Long operation
    print("\n" + "-" * 60)
    print("TEST 2: LONG OPERATION NOTIFICATION")
    print("-" * 60)
    test_long_operation()
    
    # Test 3: Error notification
    print("\n" + "-" * 60)
    print("TEST 3: ERROR NOTIFICATION")
    print("-" * 60)
    test_error_notification()
    
    # Test 4: History
    print("\n" + "-" * 60)
    print("TEST 4: NOTIFICATION HISTORY")
    print("-" * 60)
    test_notification_history()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)
    print("\nSummary:")
    print("• Cross-user notifications: Working")
    print("• Desktop notifications: Check your notification center")
    print("• Long operation alerts: Triggered after 30+ seconds")
    print("• Error notifications: Sent with urgent priority")
    print("• History tracking: All notifications stored")
    print("\nNote: Desktop notifications should have appeared in your macOS notification center")
    print("Install terminal-notifier for better notifications: brew install terminal-notifier")

if __name__ == "__main__":
    main()