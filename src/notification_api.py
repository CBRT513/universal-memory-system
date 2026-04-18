#!/usr/bin/env python3
"""
API Endpoints for UMS Notification System
Provides REST API for cross-user notifications and system alerts
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

# Import notification service
from notification_service import (
    NotificationService, 
    NotificationPriority, 
    NotificationType,
    ProgressNotifier
)

# Create router
router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Pydantic models
class NotificationRequest(BaseModel):
    """Request model for sending notifications"""
    recipient: str
    title: str
    message: str
    priority: Optional[str] = "normal"
    type: Optional[str] = "user_message"
    metadata: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    """Response model for notification operations"""
    success: bool
    notification_id: Optional[str] = None
    message: Optional[str] = None

class NotificationItem(BaseModel):
    """Model for a notification item"""
    id: str
    sender: str
    type: str
    priority: str
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    read_at: Optional[str] = None
    is_read: bool

class NotificationList(BaseModel):
    """Model for list of notifications"""
    notifications: List[NotificationItem]
    unread_count: int
    total_count: int

class MarkReadRequest(BaseModel):
    """Request to mark notifications as read"""
    notification_ids: Optional[List[str]] = None
    mark_all: Optional[bool] = False

# Initialize service
notification_service = NotificationService()

@router.post("/send", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """
    Send a notification to another user
    
    Example:
    ```
    POST /api/notifications/send
    {
        "recipient": "equillabs",
        "title": "Build Complete",
        "message": "The project build has finished successfully",
        "priority": "high"
    }
    ```
    """
    try:
        # Convert string enums to actual enums
        priority = NotificationPriority(request.priority)
        notif_type = NotificationType(request.type)
        
        # Send notification
        notification_id = notification_service.send_notification(
            recipient=request.recipient,
            title=request.title,
            message=request.message,
            notification_type=notif_type,
            priority=priority,
            metadata=request.metadata
        )
        
        return NotificationResponse(
            success=True,
            notification_id=notification_id,
            message=f"Notification sent to {request.recipient}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check/{username}", response_model=NotificationList)
async def check_notifications(
    username: str,
    unread_only: bool = Query(True, description="Only return unread notifications")
):
    """
    Check notifications for a specific user
    
    Example:
    ```
    GET /api/notifications/check/cerion?unread_only=true
    ```
    """
    try:
        notifications = notification_service.check_notifications(
            username=username,
            unread_only=unread_only
        )
        
        # Convert to response model
        notif_items = [
            NotificationItem(**notif) for notif in notifications
        ]
        
        unread_count = sum(1 for n in notif_items if not n.is_read)
        
        return NotificationList(
            notifications=notif_items,
            unread_count=unread_count,
            total_count=len(notif_items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mark-read/{notification_id}", response_model=NotificationResponse)
async def mark_notification_read(notification_id: str):
    """
    Mark a specific notification as read
    
    Example:
    ```
    PUT /api/notifications/mark-read/notif_1234567890_cerion
    ```
    """
    try:
        success = notification_service.mark_as_read(notification_id)
        
        if success:
            return NotificationResponse(
                success=True,
                message=f"Notification {notification_id} marked as read"
            )
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mark-read", response_model=NotificationResponse)
async def mark_multiple_read(request: MarkReadRequest):
    """
    Mark multiple notifications as read or mark all as read
    
    Example:
    ```
    PUT /api/notifications/mark-read
    {
        "notification_ids": ["notif_1", "notif_2"],
        "mark_all": false
    }
    ```
    
    Or mark all:
    ```
    PUT /api/notifications/mark-read
    {
        "mark_all": true
    }
    ```
    """
    try:
        if request.mark_all:
            count = notification_service.mark_all_as_read()
            return NotificationResponse(
                success=True,
                message=f"Marked {count} notifications as read"
            )
        elif request.notification_ids:
            success_count = 0
            for notif_id in request.notification_ids:
                if notification_service.mark_as_read(notif_id):
                    success_count += 1
            
            return NotificationResponse(
                success=True,
                message=f"Marked {success_count} of {len(request.notification_ids)} notifications as read"
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either notification_ids or mark_all must be provided"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{username}", response_model=NotificationList)
async def get_notification_history(
    username: str,
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of notifications")
):
    """
    Get notification history for a user
    
    Example:
    ```
    GET /api/notifications/history/cerion?days=30&limit=50
    ```
    """
    try:
        notifications = notification_service.get_notification_history(
            username=username,
            days=days,
            limit=limit
        )
        
        # Convert to response model
        notif_items = [
            NotificationItem(**notif) for notif in notifications
        ]
        
        unread_count = sum(1 for n in notif_items if not n.is_read)
        
        return NotificationList(
            notifications=notif_items,
            unread_count=unread_count,
            total_count=len(notif_items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/desktop", response_model=NotificationResponse)
async def send_desktop_notification(
    title: str = Body(...),
    message: str = Body(...),
    priority: str = Body("normal"),
    sound: bool = Body(True),
    urgent: bool = Body(False)
):
    """
    Send a desktop notification to the current user
    
    Example:
    ```
    POST /api/notifications/desktop
    {
        "title": "Operation Complete",
        "message": "Your data export has finished",
        "priority": "normal",
        "sound": true
    }
    ```
    """
    try:
        priority_enum = NotificationPriority(priority)
        
        success = notification_service.send_desktop_notification(
            title=title,
            message=message,
            sound=sound,
            urgent=urgent,
            priority=priority_enum
        )
        
        return NotificationResponse(
            success=success,
            message="Desktop notification sent" if success else "Failed to send desktop notification"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count/{username}")
async def get_unread_count(username: str):
    """
    Get count of unread notifications for a user
    
    Example:
    ```
    GET /api/notifications/unread-count/cerion
    ```
    """
    try:
        notifications = notification_service.check_notifications(
            username=username,
            unread_only=True
        )
        
        return {
            "username": username,
            "unread_count": len(notifications),
            "has_urgent": any(n["priority"] == "urgent" for n in notifications),
            "has_high_priority": any(n["priority"] in ["high", "urgent"] for n in notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear/{username}")
async def clear_old_notifications(
    username: str,
    days_old: int = Query(30, description="Delete notifications older than this many days")
):
    """
    Clear old notifications for a user
    
    Example:
    ```
    DELETE /api/notifications/clear/cerion?days_old=30
    ```
    """
    try:
        # This would need implementation in NotificationService
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Cleared notifications older than {days_old} days for {username}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time notifications (optional enhancement)
@router.websocket("/ws/{username}")
async def notification_websocket(websocket, username: str):
    """
    WebSocket endpoint for real-time notifications
    
    Connect via: ws://localhost:8091/api/notifications/ws/cerion
    """
    await websocket.accept()
    
    try:
        # This would implement real-time notification streaming
        # For now, just echo messages
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Export router
__all__ = ['router']