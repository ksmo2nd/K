"""
WiFi QR System API Routes
Clean, focused WiFi QR code generation and session management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..services.wifi_captive_service import WiFiCaptiveService
from ..core.auth import get_current_user_id
from ..core.database import get_supabase_client

router = APIRouter()
wifi_service = WiFiCaptiveService()


class GenerateWiFiQRRequest(BaseModel):
    session_id: str
    data_limit_mb: int


class WiFiConnectionRequest(BaseModel):
    network_name: str
    device_mac: str


class TrackUsageRequest(BaseModel):
    session_token: str
    data_used_mb: int
    duration_minutes: Optional[int] = 0


@router.post("/generate-qr")
async def generate_wifi_qr(
    request: GenerateWiFiQRRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate WiFi QR code with encrypted password for automatic connection"""
    try:
        result = await wifi_service.create_wifi_access_token(
            user_id=user_id,
            session_id=request.session_id,
            data_limit_mb=request.data_limit_mb
        )
        
        if result["success"]:
            # Generate the actual QR code image
            qr_image = wifi_service.generate_wifi_qr_code(result["wifi_qr_data"])
            
            return {
                "success": True,
                "data": {
                    "qr_code_image": qr_image,
                    "qr_code_data": result["wifi_qr_data"],
                    "network_name": result["network_name"],
                    "wifi_security": result["wifi_security"],
                    "data_limit_mb": result["data_limit_mb"],
                    "session_duration": result["session_duration"],
                    "access_type": result["access_type"],
                    "token_id": result["token_id"],
                    "expires_at": "30 days from now"
                },
                "message": "WiFi QR code generated successfully - scan to connect instantly"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate WiFi QR code")
        
    except Exception as e:
        print(f"❌ WIFI QR ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-connection")
async def validate_wifi_connection(request: WiFiConnectionRequest):
    """Validate WiFi connection when device connects to network"""
    try:
        validation = await wifi_service.validate_wifi_session_connection(
            request.network_name, 
            request.device_mac
        )
        
        return {
            "success": validation["success"],
            "data": validation
        }
        
    except Exception as e:
        print(f"❌ WIFI CONNECTION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-info/{network_name}")
async def get_wifi_session_info(network_name: str):
    """Get WiFi session information by network name"""
    try:
        response = get_supabase_client().table('wifi_access_tokens')\
            .select('*')\
            .eq('network_name', network_name)\
            .eq('status', 'active')\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="WiFi session not found")
        
        session_data = response.data[0]
        
        return {
            "success": True,
            "data": {
                "session_id": session_data["session_id"],
                "network_name": session_data["network_name"],
                "data_limit_mb": session_data["data_limit_mb"],
                "bandwidth_limit_mbps": session_data["bandwidth_limit_mbps"],
                "expires_at": session_data["expires_at"],
                "status": session_data["status"],
                "wifi_security": session_data.get("wifi_security", "WPA2")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ WIFI SESSION INFO ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-usage")
async def track_wifi_usage(request: TrackUsageRequest):
    """Track data usage for WiFi session"""
    try:
        result = await wifi_service.track_session_usage(
            request.session_token,
            request.data_used_mb,
            request.duration_minutes
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"❌ WIFI USAGE TRACKING ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-sessions/{user_id}")
async def get_user_wifi_sessions(user_id: str):
    """Get all WiFi sessions for a user"""
    try:
        sessions = await wifi_service.get_user_sessions(user_id)
        
        return {
            "success": True,
            "data": sessions
        }
        
    except Exception as e:
        print(f"❌ USER SESSIONS ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{token_id}")
async def delete_wifi_session(
    token_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete/revoke a WiFi session"""
    try:
        # Verify ownership
        response = get_supabase_client().table('wifi_access_tokens')\
            .select('*')\
            .eq('id', token_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="WiFi session not found")
        
        # Revoke the session
        get_supabase_client().table('wifi_access_tokens')\
            .update({'status': 'revoked'})\
            .eq('id', token_id)\
            .execute()
        
        return {
            "success": True,
            "message": "WiFi session revoked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ DELETE SESSION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))