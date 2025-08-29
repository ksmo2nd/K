"""
KSWiFi Connect Routes - VPN-based session access
Replaces eSIM routes with VPN profile generation
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..core.auth import get_current_user_id
from ..core.database import get_supabase_client
from ..services.kswifi_connect_service import KSWiFiConnectService
from datetime import datetime

router = APIRouter(prefix="/api/connect", tags=["kswifi-connect"])
logger = logging.getLogger(__name__)

# Pydantic models
class GenerateConnectRequest(BaseModel):
    session_id: str
    data_limit_mb: int = 1024
    time_limit_hours: int = 24
    profile_name: Optional[str] = "KSWiFi Connect"

class UpdateUsageRequest(BaseModel):
    client_public_key: str
    data_used_mb: float
    last_seen: str

# Initialize service
connect_service = KSWiFiConnectService()

@router.post("/generate-profile")
async def generate_connect_profile(
    request: GenerateConnectRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Generate KSWiFi Connect profile for session access
    Replaces the old eSIM generation endpoint
    """
    try:
        logger.info(f"🔍 CONNECT: Generating profile for session {request.session_id}")
        
        # Generate VPN profile
        result = await connect_service.generate_connect_profile(
            user_id=current_user_id,
            session_id=request.session_id,
            data_limit_mb=request.data_limit_mb,
            time_limit_hours=request.time_limit_hours
        )
        
        logger.info(f"✅ CONNECT: Profile generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ CONNECT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-usage")
async def update_session_usage(request: UpdateUsageRequest) -> Dict[str, Any]:
    """
    Update session usage from VPN server monitoring
    Called by VPS monitoring service
    """
    try:
        logger.info(f"🔍 USAGE UPDATE: Client {request.client_public_key[:8]}... used {request.data_used_mb}MB")
        
        result = await connect_service.update_session_usage(
            client_public_key=request.client_public_key,
            data_used_mb=request.data_used_mb
        )
        
        if result["session_valid"]:
            logger.info(f"✅ USAGE: Session still valid, {result.get('remaining_mb', 0)}MB remaining")
        else:
            logger.info(f"❌ USAGE: Session invalid - {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ USAGE UPDATE ERROR: {str(e)}")
        return {"session_valid": False, "error": str(e)}

@router.get("/my-profiles")
async def get_my_connect_profiles(
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get user's KSWiFi Connect profiles"""
    try:
        profiles = await connect_service.get_user_profiles(current_user_id)
        
        return {
            "profiles": profiles,
            "count": len(profiles)
        }
        
    except Exception as e:
        logger.error(f"❌ GET PROFILES ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/profile/{connect_id}")
async def deactivate_connect_profile(
    connect_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Deactivate a KSWiFi Connect profile"""
    try:
        # Get profile
        response = get_supabase_client().table('kswifi_connect_profiles')\
            .select('*')\
            .eq('id', connect_id)\
            .eq('user_id', current_user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = response.data[0]
        
        # Deactivate profile
        await connect_service._deactivate_profile(
            profile["client_public_key"], 
            "user_requested"
        )
        
        return {
            "success": True,
            "connect_id": connect_id,
            "status": "deactivated",
            "message": "KSWiFi Connect profile deactivated successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ DEACTIVATE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{connect_id}/status")
async def get_connect_profile_status(
    connect_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get real-time status of KSWiFi Connect profile"""
    try:
        response = get_supabase_client().table('kswifi_connect_profiles')\
            .select('*')\
            .eq('id', connect_id)\
            .eq('user_id', current_user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = response.data[0]
        
        # Calculate remaining data and time
        data_used = profile.get('data_used_mb', 0)
        data_limit = profile.get('data_limit_mb', 0)
        remaining_data = max(0, data_limit - data_used)
        
        expires_at = datetime.fromisoformat(profile['expires_at'].replace('Z', '+00:00'))
        time_remaining = max(0, (expires_at - datetime.utcnow().replace(tzinfo=expires_at.tzinfo)).total_seconds())
        
        return {
            "connect_id": connect_id,
            "session_id": profile["session_id"],
            "status": profile["status"],
            "data_used_mb": data_used,
            "data_limit_mb": data_limit,
            "remaining_data_mb": remaining_data,
            "data_usage_percent": (data_used / data_limit * 100) if data_limit > 0 else 0,
            "time_remaining_seconds": time_remaining,
            "bandwidth_limit_mbps": profile.get("bandwidth_limit_mbps", 10),
            "client_ip": profile.get("client_ip"),
            "expires_at": profile["expires_at"],
            "created_at": profile["created_at"],
            "last_used_at": profile.get("last_used_at"),
            "access_method": "kswifi_connect"
        }
        
    except Exception as e:
        logger.error(f"❌ STATUS ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))