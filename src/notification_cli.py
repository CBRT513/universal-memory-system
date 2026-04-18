#!/usr/bin/env python3
"""
CLI Commands for UMS Notification System
Provides command-line interface for notifications
"""

import click
import json
import sys
import time
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# Add UMS src to path
sys.path.insert(0, '/usr/local/share/universal-memory-system/src')

from notification_service import (
    NotificationService,
    NotificationPriority,
    NotificationType,
    ProgressNotifier,
    prompt_with_notification
)

# Rich formatting if available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False

@click.group(name="notify")
def notification_group():
    """Notification commands for cross-user messaging and alerts"""
    pass

@notification_group.command(name="send")
@click.argument("recipient")
@click.argument("message")
@click.option("--title", "-t", default="Message", help="Notification title")
@click.option("--priority", "-p", 
              type=click.Choice(["low", "normal", "high", "urgent"]),
              default="normal", help="Message priority")
@click.option("--metadata", "-m", help="Additional metadata as JSON")
def send_notification_cmd(recipient: str, message: str, title: str, 
                         priority: str, metadata: Optional[str]):
    """
    Send a notification to another user
    
    Examples:
        umscli notify send equillabs "Build complete, ready for review"
        umscli notify send cerion "Database backup finished" --priority high
        umscli notify send equillabs "Please check PR #42" --title "Code Review" --priority urgent
    """
    service = NotificationService()
    
    # Parse metadata if provided
    meta_dict = None
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON metadata", err=True)
            sys.exit(1)
    
    # Send notification
    try:
        notif_id = service.send_notification(
            recipient=recipient,
            title=title,
            message=message,
            priority=NotificationPriority(priority),
            metadata=meta_dict
        )
        
        if HAS_RICH:
            console.print(f"[green]✅ Notification sent to {recipient}[/green]")
            console.print(f"[dim]ID: {notif_id}[/dim]")
        else:
            click.echo(f"✅ Notification sent to {recipient}")
            click.echo(f"ID: {notif_id}")
            
    except Exception as e:
        click.echo(f"❌ Failed to send notification: {e}", err=True)
        sys.exit(1)

@notification_group.command(name="check")
@click.option("--user", "-u", help="Username to check (default: current user)")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all notifications, not just unread")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def check_notifications_cmd(user: Optional[str], show_all: bool, as_json: bool):
    """
    Check your notifications
    
    Examples:
        umscli notify check                # Check your unread notifications
        umscli notify check --all          # Show all notifications
        umscli notify check --user equillabs  # Check another user's notifications
    """
    service = NotificationService()
    
    notifications = service.check_notifications(
        username=user,
        unread_only=not show_all
    )
    
    if as_json:
        click.echo(json.dumps(notifications, indent=2))
        return
    
    if not notifications:
        if HAS_RICH:
            console.print("[yellow]📭 No notifications[/yellow]")
        else:
            click.echo("📭 No notifications")
        return
    
    # Display notifications
    if HAS_RICH:
        table = Table(title=f"Notifications for {user or service.current_user}")
        table.add_column("From", style="cyan")
        table.add_column("Priority", style="yellow")
        table.add_column("Title", style="green")
        table.add_column("Message", style="white")
        table.add_column("Time", style="dim")
        table.add_column("Status", style="magenta")
        
        for notif in notifications:
            priority_emoji = {
                "low": "🔵",
                "normal": "⚪",
                "high": "🟡",
                "urgent": "🔴"
            }.get(notif["priority"], "⚪")
            
            status = "📬 Unread" if not notif["is_read"] else "✓ Read"
            
            # Format time
            created = datetime.fromisoformat(notif["created_at"])
            time_str = created.strftime("%m/%d %H:%M")
            
            table.add_row(
                notif["sender"],
                f"{priority_emoji} {notif['priority']}",
                notif["title"],
                notif["message"][:50] + "..." if len(notif["message"]) > 50 else notif["message"],
                time_str,
                status
            )
        
        console.print(table)
        
        # Summary
        unread = sum(1 for n in notifications if not n["is_read"])
        if unread > 0:
            console.print(f"\n[yellow]📬 You have {unread} unread notification(s)[/yellow]")
    else:
        # Plain text output
        click.echo(f"\nNotifications for {user or service.current_user}")
        click.echo("-" * 60)
        
        for notif in notifications:
            status = "UNREAD" if not notif["is_read"] else "READ"
            click.echo(f"\n[{status}] From: {notif['sender']} | Priority: {notif['priority']}")
            click.echo(f"Title: {notif['title']}")
            click.echo(f"Message: {notif['message']}")
            click.echo(f"Time: {notif['created_at']}")
            click.echo("-" * 40)
        
        unread = sum(1 for n in notifications if not n["is_read"])
        if unread > 0:
            click.echo(f"\n📬 You have {unread} unread notification(s)")

@notification_group.command(name="mark-read")
@click.argument("notification_id", required=False)
@click.option("--all", "-a", "mark_all", is_flag=True, help="Mark all as read")
def mark_read_cmd(notification_id: Optional[str], mark_all: bool):
    """
    Mark notifications as read
    
    Examples:
        umscli notify mark-read notif_123456_cerion  # Mark specific notification
        umscli notify mark-read --all                # Mark all as read
    """
    service = NotificationService()
    
    if mark_all:
        count = service.mark_all_as_read()
        if HAS_RICH:
            console.print(f"[green]✅ Marked {count} notifications as read[/green]")
        else:
            click.echo(f"✅ Marked {count} notifications as read")
    elif notification_id:
        success = service.mark_as_read(notification_id)
        if success:
            if HAS_RICH:
                console.print(f"[green]✅ Marked {notification_id} as read[/green]")
            else:
                click.echo(f"✅ Marked {notification_id} as read")
        else:
            click.echo(f"❌ Notification {notification_id} not found", err=True)
            sys.exit(1)
    else:
        click.echo("❌ Provide notification ID or use --all flag", err=True)
        sys.exit(1)

@notification_group.command(name="history")
@click.option("--user", "-u", help="Username (default: current user)")
@click.option("--days", "-d", default=7, help="Days to look back")
@click.option("--limit", "-l", default=50, help="Maximum notifications to show")
def history_cmd(user: Optional[str], days: int, limit: int):
    """
    View notification history
    
    Examples:
        umscli notify history              # Last 7 days
        umscli notify history --days 30    # Last month
        umscli notify history --user equillabs --days 14
    """
    service = NotificationService()
    
    notifications = service.get_notification_history(
        username=user,
        days=days,
        limit=limit
    )
    
    if not notifications:
        click.echo(f"No notifications in the last {days} days")
        return
    
    if HAS_RICH:
        console.print(f"\n[bold]Notification History - Last {days} Days[/bold]")
        
        for notif in notifications:
            # Color based on read status and priority
            if not notif["is_read"]:
                style = "bold yellow" if notif["priority"] in ["high", "urgent"] else "bold"
            else:
                style = "dim"
            
            created = datetime.fromisoformat(notif["created_at"])
            
            panel = Panel(
                f"[{style}]{notif['message']}[/{style}]",
                title=f"{notif['title']} - From: {notif['sender']}",
                subtitle=f"{created.strftime('%Y-%m-%d %H:%M')} | {notif['priority']}",
                border_style=style
            )
            console.print(panel)
    else:
        click.echo(f"\nNotification History - Last {days} Days")
        click.echo("=" * 60)
        
        for notif in notifications:
            status = "UNREAD" if not notif["is_read"] else "READ"
            click.echo(f"\n[{status}] {notif['created_at']}")
            click.echo(f"From: {notif['sender']} | Priority: {notif['priority']}")
            click.echo(f"Title: {notif['title']}")
            click.echo(f"Message: {notif['message']}")
            click.echo("-" * 40)

@notification_group.command(name="desktop")
@click.argument("message")
@click.option("--title", "-t", default="UMS Notification", help="Notification title")
@click.option("--priority", "-p",
              type=click.Choice(["low", "normal", "high", "urgent"]),
              default="normal", help="Priority level")
@click.option("--sound/--no-sound", default=True, help="Play sound")
def desktop_notification_cmd(message: str, title: str, priority: str, sound: bool):
    """
    Send a desktop notification
    
    Examples:
        umscli notify desktop "Task complete"
        umscli notify desktop "Error occurred" --priority urgent
        umscli notify desktop "Silent notification" --no-sound
    """
    service = NotificationService()
    
    success = service.send_desktop_notification(
        title=title,
        message=message,
        sound=sound,
        priority=NotificationPriority(priority),
        urgent=(priority == "urgent")
    )
    
    if success:
        if HAS_RICH:
            console.print("[green]✅ Desktop notification sent[/green]")
        else:
            click.echo("✅ Desktop notification sent")
    else:
        click.echo("❌ Failed to send desktop notification", err=True)
        sys.exit(1)

@notification_group.command(name="watch")
@click.argument("command")
@click.option("--notify-on", "-n",
              type=click.Choice(["complete", "error", "both"]),
              default="both", help="When to notify")
def watch_command(command: str, notify_on: str):
    """
    Run a command and notify when complete
    
    Examples:
        umscli notify watch "python long_script.py"
        umscli notify watch "npm run build" --notify-on complete
        umscli notify watch "./backup.sh" --notify-on error
    """
    import subprocess
    
    service = NotificationService()
    progress = ProgressNotifier(f"Command: {command}", notification_service=service)
    
    click.echo(f"🚀 Running: {command}")
    start_time = time.time()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # Success
            if notify_on in ["complete", "both"]:
                progress.complete(
                    success=True,
                    message=f"Command completed successfully in {elapsed:.1f}s"
                )
            click.echo(f"✅ Command completed successfully")
            if result.stdout:
                click.echo(f"Output:\n{result.stdout}")
        else:
            # Error
            if notify_on in ["error", "both"]:
                progress.error(f"Command failed with exit code {result.returncode}")
            click.echo(f"❌ Command failed with exit code {result.returncode}", err=True)
            if result.stderr:
                click.echo(f"Error:\n{result.stderr}", err=True)
            sys.exit(result.returncode)
            
    except Exception as e:
        if notify_on in ["error", "both"]:
            progress.error(f"Command failed: {str(e)}")
        click.echo(f"❌ Failed to run command: {e}", err=True)
        sys.exit(1)

@notification_group.command(name="test")
def test_notifications_cmd():
    """
    Test the notification system
    
    Run various notification tests to ensure everything is working
    """
    click.echo("🧪 Testing UMS Notification System")
    click.echo("-" * 40)
    
    service = NotificationService()
    
    # Test 1: Desktop notification
    click.echo("\n1. Testing desktop notification...")
    success = service.send_desktop_notification(
        "UMS Test",
        "Testing notification system",
        priority=NotificationPriority.NORMAL
    )
    if success:
        click.echo("   ✅ Desktop notification sent")
    else:
        click.echo("   ❌ Desktop notification failed")
    
    time.sleep(2)
    
    # Test 2: Different priority levels
    click.echo("\n2. Testing priority levels...")
    for priority in ["low", "normal", "high", "urgent"]:
        service.send_desktop_notification(
            f"Priority: {priority}",
            f"This is a {priority} priority notification",
            priority=NotificationPriority(priority)
        )
        click.echo(f"   Sent {priority} priority notification")
        time.sleep(1)
    
    # Test 3: Progress notification
    click.echo("\n3. Testing progress notification...")
    progress = ProgressNotifier("Test Operation", total_items=5)
    for i in range(1, 6):
        progress.update(i, f"Processing item {i}")
        click.echo(f"   Processing item {i}/5")
        time.sleep(1)
    progress.complete(success=True)
    
    # Test 4: Prompt with notification
    click.echo("\n4. Testing prompt with notification...")
    response = prompt_with_notification(
        "Please enter 'test' to continue: ",
        title="UMS Test Input"
    )
    if response == "test":
        click.echo("   ✅ Prompt notification worked")
    
    click.echo("\n✅ All tests complete!")
    click.echo("\nNote: Check your notification center for desktop notifications")

# Export commands for integration
__all__ = ['notification_group']

if __name__ == "__main__":
    notification_group()