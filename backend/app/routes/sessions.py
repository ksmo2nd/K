"""
Internet Session Download API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.auth import verify_jwt_token
from ..services.session_service import SessionService


router = APIRouter()
session_service = SessionService()


# Request/Response Models
class SessionDownloadRequest(BaseModel):
    session_id: str
    esim_id: Optional[str] = None


class SessionActivationRequest(BaseModel):
    session_id: str


class SessionUsageRequest(BaseModel):
    session_id: str
    data_used_mb: int


# Session Information Response
class SessionInfo(BaseModel):
    id: str
    name: str
    size: str
    data_mb: int
    price_ngn: int
    price_usd: float
    validity_days: Optional[int]  # None for sessions that don't expire
    plan_type: str
    is_unlimited: bool
    is_free: bool
    description: str
    features: List[str]
    source_network: Optional[str] = None
    network_quality: Optional[str] = None


# User Session Response
class UserSession(BaseModel):
    id: str
    name: str
    size: str
    status: str
    progress_percent: int
    download_started_at: str
    expires_at: Optional[str]
    is_active: bool
    can_activate: bool
    data_remaining_mb: int


@router.get("/sessions/available", response_model=List[SessionInfo])
async def get_available_sessions(wifi_network: Optional[str] = None, user_id: Optional[str] = None):
    """Get all available internet session options from connected WiFi network"""
    try:
        sessions = await session_service.get_available_sessions(wifi_network=wifi_network, user_id=user_id)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/download")
async def start_session_download(
    request: SessionDownloadRequest,
    user_data: dict = Depends(verify_jwt_token)
):
    """Start downloading an internet session"""
    try:
        user_id = user_data["sub"]
        
        result = await session_service.start_session_download(
            user_id=user_id,
            session_id=request.session_id,
            esim_id=request.esim_id
        )
        
        return {
            "success": True,
            "message": "Session download started successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/activate")
async def activate_session(
    request: SessionActivationRequest,
    user_data: dict = Depends(verify_jwt_token)
):
    """Activate a downloaded session for use"""
    try:
        user_id = user_data["sub"]
        
        result = await session_service.activate_session(
            session_id=request.session_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": "Session activated successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/my-sessions", response_model=List[UserSession])
async def get_my_sessions(user_data: dict = Depends(verify_jwt_token)):
    """Get all sessions for the current user"""
    try:
        user_id = user_data["sub"]
        print(f"🔍 MY SESSIONS ROUTE: JWT user_id = {user_id}")
        print(f"🔍 MY SESSIONS ROUTE: Full user_data = {user_data}")
        sessions = await session_service.get_user_sessions(user_id)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/track-usage")
async def track_session_usage(
    request: SessionUsageRequest,
    user_data: dict = Depends(verify_jwt_token)
):
    """Track data usage for an active session"""
    try:
        result = await session_service.track_session_usage(
            session_id=request.session_id,
            data_used_mb=request.data_used_mb
        )
        
        return {
            "success": True,
            "message": "Usage tracked successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str,
    user_data: dict = Depends(verify_jwt_token)
):
    """Get real-time status of a session download or usage"""
    try:
        user_id = user_data["sub"]
        
        # Get session from database
        from ..core.database import get_supabase_client
        
        response = get_supabase_client().table('internet_sessions')\
            .select('*')\
            .eq('id', session_id)\
            .eq('user_id', user_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = response.data
        
        return {
            "success": True,
            "data": {
                "session_id": session["id"],
                "status": session["status"],
                "progress_percent": session.get("progress_percent", 0),
                "data_used_mb": session.get("used_data_mb", 0),
                "data_remaining_mb": (
                    session["data_mb"] - session.get("used_data_mb", 0)
                    if session["data_mb"] > 0 else 999999
                ),
                "expires_at": session.get("expires_at"),
                "error_message": session.get("error_message")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/quota/free")
async def get_unlimited_access_status(user_data: dict = Depends(verify_jwt_token)):
    """Get unlimited access status - no quota limitations"""
    try:
        user_id = user_data.get('user_id') or user_data.get('sub')
        
        # Get user's total data usage for informational purposes only
        from ..core.database import get_supabase_client
        
        # Get total data from all sessions (for statistics only)
        sessions_response = get_supabase_client().table('internet_sessions')\
            .select('data_mb')\
            .eq('user_id', user_id)\
            .execute()
        
        total_used_mb = sum(session.get('data_mb', 0) for session in sessions_response.data)
        
        return {
            "success": True,
            "data": {
                "unlimited_access": True,
                "total_used_mb": total_used_mb,
                "quota_exhausted": False,  # Never exhausted - unlimited
                "message": "Unlimited data access - no restrictions",
                "can_create_session": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))