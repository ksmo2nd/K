"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..core.database import get_supabase_client
from ..services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()


class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/webhook/signup")
async def signup_webhook(user_data: dict):
    """
    Webhook endpoint called by Supabase when a new user signs up
    This handles post-signup actions like sending welcome notifications
    """
    try:
        user_id = user_data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")
        
        # Send welcome notification
        await notification_service.send_welcome_notification(user_id)
        
        return {"status": "success", "message": "Post-signup actions completed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup webhook error: {str(e)}")


@router.post("/webhook/login")
async def login_webhook(login_data: dict):
    """
    Webhook endpoint called by Supabase when a user logs in
    This handles post-login actions like updating last login time
    """
    try:
        user_id = login_data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")
        
        # Update last login time
        await supabase_client.update_user_last_login(user_id)
        
        return {"status": "success", "message": "Post-login actions completed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login webhook error: {str(e)}")


@router.get("/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get user profile information"""
    try:
        user = await supabase_client.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")


@router.post("/device/register")
async def register_device(device_data: dict):
    """Register a device for push notifications"""
    try:
        user_id = device_data.get('user_id')
        push_token = device_data.get('push_token')
        device_type = device_data.get('device_type')  # ios, android, web
        
        if not all([user_id, push_token, device_type]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Store device information
        device_record = {
            'user_id': user_id,
            'push_token': push_token,
            'device_type': device_type,
            'active': True
        }
        
        # Check if device already exists
        existing_response = get_supabase_client().table('user_devices').select('id').eq('push_token', push_token).execute()
        
        if existing_response.data:
            # Update existing device
            get_supabase_client().table('user_devices').update(device_record).eq('push_token', push_token).execute()
        else:
            # Insert new device
            get_supabase_client().table('user_devices').insert(device_record).execute()
        
        return {"status": "success", "message": "Device registered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering device: {str(e)}")


@router.delete("/device/unregister")
async def unregister_device(device_data: dict):
    """Unregister a device from push notifications"""
    try:
        push_token = device_data.get('push_token')
        
        if not push_token:
            raise HTTPException(status_code=400, detail="Missing push_token")
        
        # Mark device as inactive
        get_supabase_client().table('user_devices').update({'active': False}).eq('push_token', push_token).execute()
        
        return {"status": "success", "message": "Device unregistered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unregistering device: {str(e)}")