"""
Notification management routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()


class MarkReadRequest(BaseModel):
    notification_id: str
    user_id: str


@router.get("/user/{user_id}")
async def get_user_notifications(
    user_id: str, 
    limit: int = 50, 
    unread_only: bool = False
):
    """Get notifications for a user"""
    try:
        result = await notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            unread_only=unread_only
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notifications: {str(e)}")


@router.post("/mark-read")
async def mark_notification_read(request: MarkReadRequest):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_notification_read(
            notification_id=request.notification_id,
            user_id=request.user_id
        )
        
        if success:
            return {"status": "success", "message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark notification as read")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")


@router.post("/user/{user_id}/mark-all-read")
async def mark_all_notifications_read(user_id: str):
    """Mark all notifications as read for a user"""
    try:
        success = await notification_service.mark_all_notifications_read(user_id)
        
        if success:
            return {"status": "success", "message": "All notifications marked as read"}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark notifications as read")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking all notifications as read: {str(e)}")


@router.get("/user/{user_id}/unread-count")
async def get_unread_count(user_id: str):
    """Get unread notification count for a user"""
    try:
        from ..core.database import supabase_client
        
        response = supabase_client.client.table('notifications').select('id', count='exact').eq('user_id', user_id).eq('read', False).execute()
        unread_count = response.count
        
        return {"unread_count": unread_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting unread count: {str(e)}")


@router.post("/test/low-data-alert")
async def test_low_data_alert(user_id: str, pack_id: str, remaining_mb: float = 50.0, total_mb: float = 1024.0):
    """Test endpoint to send a low data alert"""
    try:
        await notification_service.send_low_data_alert(user_id, pack_id, remaining_mb, total_mb)
        return {"status": "success", "message": "Low data alert sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending test alert: {str(e)}")


@router.post("/test/welcome")
async def test_welcome_notification(user_id: str):
    """Test endpoint to send a welcome notification"""
    try:
        await notification_service.send_welcome_notification(user_id)
        return {"status": "success", "message": "Welcome notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending welcome notification: {str(e)}")


@router.post("/test/esim-activation")
async def test_esim_activation_notification(user_id: str, esim_id: str):
    """Test endpoint to send eSIM activation notification"""
    try:
        await notification_service.send_esim_activation_success(user_id, esim_id)
        return {"status": "success", "message": "eSIM activation notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending eSIM activation notification: {str(e)}")