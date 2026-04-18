#!/usr/bin/env python3
"""
Cross-User Notification System for Universal Memory System
Handles both user-to-user notifications and system notifications
"""

import os
import json
import time
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import sqlite3
from pathlib import Path
import threading
import queue

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    URGENT = "urgent"

class NotificationType(Enum):
    """Types of notifications"""
    USER_MESSAGE = "user_message"
    SYSTEM_ALERT = "system_alert"
    OPERATION_COMPLETE = "operation_complete"
    ERROR = "error"
    INPUT_NEEDED = "input_needed"
    PROGRESS_UPDATE = "progress_update"

class NotificationService:
    """
    Manages notifications for UMS including:
    - Cross-user messaging through shared database
    - Desktop notifications for long operations
    - System alerts and error notifications
    """
    
    def __init__(self, db_path: str = None, user: str = None):
        """Initialize notification service"""
        # Use shared UMS database location
        self.db_path = db_path or "/usr/local/var/universal-memory-system/databases/memories.db"
        
        # Fall back to user home if shared doesn't exist
        if not os.path.exists(self.db_path):
            self.db_path = os.path.expanduser("~/.ai-memory/memories.db")
        
        self.current_user = user or os.environ.get('USER', 'unknown')
        self.notification_queue = queue.Queue()
        
        # Notification settings
        self.settings = {
            "desktop_notifications": True,
            "notification_threshold_seconds": 30,
            "sound_enabled": True,
            "cross_user_notifications": True,
            "notification_methods": ["desktop", "memory", "log"],
            "priority_sounds": {
                "low": None,
                "normal": "Glass",
                "high": "Ping",
                "urgent": "Basso"
            }
        }
        
        # Initialize notification table
        self._init_notification_table()
        
        # Check for terminal-notifier
        self.has_terminal_notifier = shutil.which("terminal-notifier") is not None
        if not self.has_terminal_notifier:
            print("ℹ️ Install terminal-notifier for better notifications: brew install terminal-notifier")
    
    def _init_notification_table(self):
        """Create notification table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                is_read BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_recipient 
            ON notifications(recipient, is_read)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_created 
            ON notifications(created_at DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def send_desktop_notification(self, title: str, message: str, 
                                 sound: bool = True, 
                                 urgent: bool = False,
                                 priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """
        Send a desktop notification using macOS notification system
        
        Args:
            title: Notification title
            message: Notification message
            sound: Whether to play sound
            urgent: Whether to bring app to front
            priority: Notification priority level
        
        Returns:
            Success status
        """
        if not self.settings["desktop_notifications"]:
            return False
        
        try:
            # Escape quotes in message and title
            title = title.replace('"', '\\"')
            message = message.replace('"', '\\"')
            
            if self.has_terminal_notifier:
                # Use terminal-notifier for rich notifications
                cmd = ["terminal-notifier", 
                       "-title", title, 
                       "-message", message,
                       "-group", "ums-notifications"]
                
                if sound and self.settings["sound_enabled"]:
                    sound_name = self.settings["priority_sounds"].get(priority.value, "Glass")
                    if sound_name:
                        cmd.extend(["-sound", sound_name])
                
                if urgent:
                    cmd.extend(["-activate", "com.apple.Terminal"])
                
                # Add app icon if available
                icon_path = "/usr/local/share/universal-memory-system/static/icon.png"
                if os.path.exists(icon_path):
                    cmd.extend(["-appIcon", icon_path])
                
                subprocess.run(cmd, check=False)
            else:
                # Fall back to osascript
                script = f'display notification "{message}" with title "{title}"'
                
                if sound and self.settings["sound_enabled"]:
                    sound_name = self.settings["priority_sounds"].get(priority.value)
                    if sound_name:
                        script += f' sound name "{sound_name}"'
                
                subprocess.run(["osascript", "-e", script], check=False)
            
            return True
            
        except Exception as e:
            print(f"Error sending desktop notification: {e}")
            return False
    
    def send_notification(self, recipient: str, title: str, message: str,
                         notification_type: NotificationType = NotificationType.USER_MESSAGE,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         metadata: Dict = None) -> str:
        """
        Send a notification to another user through the shared database
        
        Args:
            recipient: Username to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            metadata: Additional metadata
        
        Returns:
            Notification ID
        """
        import random
        notification_id = f"notif_{int(time.time() * 1000)}_{random.randint(1000,9999)}_{self.current_user}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications 
            (id, sender, recipient, type, priority, title, message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            notification_id,
            self.current_user,
            recipient,
            notification_type.value,
            priority.value,
            title,
            message,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
        
        # Also store in memory system with notification tags
        self._store_notification_memory(notification_id, recipient, title, message, priority)
        
        return notification_id
    
    def _store_notification_memory(self, notification_id: str, recipient: str, 
                                  title: str, message: str, 
                                  priority: NotificationPriority):
        """Store notification in memory system for searchability"""
        try:
            # Import relative to UMS location
            import sys
            sys.path.insert(0, '/usr/local/share/universal-memory-system/src')
            from memory_service import MemoryService
            
            memory = MemoryService()
            memory.store_memory({
                "content": f"Notification to {recipient}: {title}\n{message}",
                "category": "notification",
                "tags": [
                    "notification",
                    f"to:{recipient}",
                    f"from:{self.current_user}",
                    f"priority:{priority.value}",
                    "unread"
                ],
                "metadata": {
                    "notification_id": notification_id,
                    "sender": self.current_user,
                    "recipient": recipient
                },
                "importance": 6 if priority == NotificationPriority.HIGH else 5
            })
        except Exception as e:
            print(f"Could not store notification in memory: {e}")
    
    def check_notifications(self, username: str = None, unread_only: bool = True) -> List[Dict]:
        """
        Check notifications for a user
        
        Args:
            username: User to check notifications for (default: current user)
            unread_only: Only return unread notifications
        
        Returns:
            List of notifications
        """
        username = username or self.current_user
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, sender, type, priority, title, message, metadata, 
                   created_at, read_at, is_read
            FROM notifications
            WHERE recipient = ?
        '''
        
        if unread_only:
            query += ' AND is_read = 0'
        
        query += ' ORDER BY created_at DESC LIMIT 50'
        
        cursor.execute(query, (username,))
        
        notifications = []
        for row in cursor.fetchall():
            notif = {
                "id": row[0],
                "sender": row[1],
                "type": row[2],
                "priority": row[3],
                "title": row[4],
                "message": row[5],
                "metadata": json.loads(row[6]) if row[6] else None,
                "created_at": row[7],
                "read_at": row[8],
                "is_read": bool(row[9])
            }
            notifications.append(notif)
        
        conn.close()
        
        # Show desktop notification for unread high-priority messages
        if unread_only:
            for notif in notifications:
                if notif["priority"] in ["high", "urgent"]:
                    self.send_desktop_notification(
                        f"Message from {notif['sender']}",
                        notif["title"],
                        priority=NotificationPriority(notif["priority"])
                    )
        
        return notifications
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: ID of notification to mark as read
        
        Returns:
            Success status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications 
            SET is_read = 1, read_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (notification_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def mark_all_as_read(self, username: str = None) -> int:
        """
        Mark all notifications as read for a user
        
        Args:
            username: User to mark notifications for
        
        Returns:
            Number of notifications marked
        """
        username = username or self.current_user
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications 
            SET is_read = 1, read_at = CURRENT_TIMESTAMP
            WHERE recipient = ? AND is_read = 0
        ''', (username,))
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    def get_notification_history(self, username: str = None, 
                                days: int = 7,
                                limit: int = 100) -> List[Dict]:
        """
        Get notification history for a user
        
        Args:
            username: User to get history for
            days: Number of days to look back
            limit: Maximum number of notifications
        
        Returns:
            List of notifications
        """
        username = username or self.current_user
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT id, sender, type, priority, title, message, metadata,
                   created_at, read_at, is_read
            FROM notifications
            WHERE recipient = ? AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (username, cutoff_date.isoformat(), limit))
        
        notifications = []
        for row in cursor.fetchall():
            notif = {
                "id": row[0],
                "sender": row[1],
                "type": row[2],
                "priority": row[3],
                "title": row[4],
                "message": row[5],
                "metadata": json.loads(row[6]) if row[6] else None,
                "created_at": row[7],
                "read_at": row[8],
                "is_read": bool(row[9])
            }
            notifications.append(notif)
        
        conn.close()
        return notifications


class ProgressNotifier:
    """
    Tracks long-running operations and sends notifications
    """
    
    def __init__(self, operation_name: str, total_items: int = None,
                 notification_service: NotificationService = None):
        """
        Initialize progress notifier
        
        Args:
            operation_name: Name of the operation
            total_items: Total number of items (optional)
            notification_service: Notification service instance
        """
        self.operation = operation_name
        self.start_time = time.time()
        self.total = total_items
        self.current = 0
        self.notified_slow = False
        
        self.notifier = notification_service or NotificationService()
        
        # Send start notification for operations with known totals
        if self.total and self.total > 100:
            self.notifier.send_desktop_notification(
                "UMS Operation Started",
                f"{self.operation}: Processing {self.total} items",
                priority=NotificationPriority.LOW
            )
    
    def update(self, current: int, message: str = None):
        """
        Update progress and send notification if taking too long
        
        Args:
            current: Current item number
            message: Optional status message
        """
        self.current = current
        elapsed = time.time() - self.start_time
        
        # Send notification if taking longer than expected
        if elapsed > 30 and not self.notified_slow:
            self.notified_slow = True
            
            if self.total:
                percent = (self.current / self.total) * 100
                remaining = (elapsed / self.current) * (self.total - self.current)
                msg = f"{self.operation}: {percent:.1f}% complete, ~{remaining:.0f}s remaining"
            else:
                msg = f"{self.operation} is taking longer than expected..."
            
            if message:
                msg += f"\n{message}"
            
            self.notifier.send_desktop_notification(
                "UMS Operation Running",
                msg,
                priority=NotificationPriority.LOW
            )
    
    def complete(self, success: bool = True, message: str = None):
        """
        Mark operation as complete and send notification
        
        Args:
            success: Whether operation succeeded
            message: Optional completion message
        """
        elapsed = time.time() - self.start_time
        
        # Only notify for operations over 10 seconds
        if elapsed > 10:
            if success:
                title = "UMS Operation Complete"
                default_msg = f"{self.operation} finished in {elapsed:.1f} seconds"
                priority = NotificationPriority.NORMAL
            else:
                title = "UMS Operation Failed"
                default_msg = f"{self.operation} failed after {elapsed:.1f} seconds"
                priority = NotificationPriority.HIGH
            
            self.notifier.send_desktop_notification(
                title,
                message or default_msg,
                priority=priority
            )
    
    def error(self, error_message: str):
        """
        Send error notification
        
        Args:
            error_message: Error description
        """
        self.notifier.send_desktop_notification(
            f"UMS Error: {self.operation}",
            error_message,
            priority=NotificationPriority.URGENT,
            urgent=True
        )


def prompt_with_notification(prompt_text: str, 
                            title: str = "UMS Input Needed",
                            urgent: bool = True) -> str:
    """
    Show notification before prompting for input
    
    Args:
        prompt_text: Text to prompt user with
        title: Notification title
        urgent: Whether to bring Terminal to front
    
    Returns:
        User input
    """
    notifier = NotificationService()
    notifier.send_desktop_notification(
        title,
        prompt_text,
        priority=NotificationPriority.HIGH,
        urgent=urgent
    )
    
    # Small delay to ensure notification appears first
    time.sleep(0.5)
    
    return input(prompt_text)


# Test functions
def test_notifications():
    """Test notification system functionality"""
    print("🧪 Testing UMS Notification System")
    print("-" * 40)
    
    service = NotificationService()
    
    # Test 1: Desktop notification
    print("Test 1: Sending desktop notification...")
    service.send_desktop_notification(
        "UMS Test",
        "This is a test notification",
        priority=NotificationPriority.NORMAL
    )
    time.sleep(2)
    
    # Test 2: Cross-user notification
    print("Test 2: Sending cross-user notification...")
    notif_id = service.send_notification(
        recipient="equillabs",
        title="Test Message",
        message="This is a test message from the notification system",
        priority=NotificationPriority.HIGH
    )
    print(f"  Sent notification: {notif_id}")
    
    # Test 3: Check notifications
    print("Test 3: Checking notifications...")
    notifications = service.check_notifications()
    print(f"  Found {len(notifications)} unread notifications")
    
    # Test 4: Progress notification
    print("Test 4: Testing progress notifications...")
    progress = ProgressNotifier("Test Operation", total_items=100)
    
    for i in range(1, 101, 20):
        progress.update(i)
        time.sleep(0.5)
    
    progress.complete(success=True, message="Test completed successfully")
    
    print("\n✅ All tests complete!")


if __name__ == "__main__":
    test_notifications()