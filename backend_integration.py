# Backend Integration for Transparent WiFi Authentication
# Add these endpoints to your FastAPI backend

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import jwt
import subprocess
import re
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/api/wifi", tags=["wifi"])

# Pydantic models
class DeviceConnectionRequest(BaseModel):
    device_mac: str
    device_ip: str
    session_token: str

class QRTokenRequest(BaseModel):
    session_id: str
    user_id: str
    data_limit_mb: int = 1024
    time_limit_hours: int = 24

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/device-connect")
async def handle_device_connection(
    request: DeviceConnectionRequest
) -> Dict[str, Any]:
    """Handle device connection with transparent authentication"""
    try:
        logger.info(f"🔍 DEVICE CONNECT: MAC={request.device_mac}, IP={request.device_ip}")
        
        # Validate session token (JWT)
        try:
            payload = jwt.decode(
                request.session_token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            
            logger.info(f"🔍 TOKEN VALID: user={user_id}, session={session_id}")
            
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ INVALID TOKEN: {request.session_token} - {str(e)}")
            return {"authenticated": False, "error": "Invalid token"}
        
        # Check session in database
        session_response = get_supabase_client().table('wifi_access_tokens')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('status', 'active')\
            .execute()
        
        if not session_response.data:
            logger.error(f"❌ SESSION NOT FOUND: {session_id}")
            return {"authenticated": False, "error": "Session not found"}
        
        session_data = session_response.data[0]
        
        # Check session limits (data, time, bandwidth)
        limits_check = await _check_session_limits(session_data, request.device_mac)
        
        if limits_check["valid"]:
            # Log successful authentication
            await _log_device_connection(
                session_id, 
                request.device_mac, 
                request.device_ip, 
                "authenticated"
            )
            
            logger.info(f"✅ DEVICE AUTHENTICATED: {request.device_mac}")
            return {
                "authenticated": True,
                "session_id": session_id,
                "user_id": user_id,
                "data_limit_mb": session_data.get('data_limit_mb'),
                "data_used_mb": session_data.get('data_used_mb', 0),
                "expires_at": session_data.get('expires_at'),
                "bandwidth_limit_mbps": session_data.get('bandwidth_limit_mbps', 10)
            }
        else:
            logger.warning(f"❌ SESSION LIMITS EXCEEDED: {session_id} - {limits_check['reason']}")
            return {"authenticated": False, "error": f"Session limits exceeded: {limits_check['reason']}"}
            
    except Exception as e:
        logger.error(f"❌ DEVICE AUTH ERROR: {str(e)}")
        return {"authenticated": False, "error": str(e)}

@router.post("/generate-qr-token")
async def generate_qr_with_token(
    request: QRTokenRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Generate WiFi QR code with embedded session token"""
    try:
        logger.info(f"🔍 QR TOKEN: Generating for session {request.session_id}")
        
        # Verify user owns the session
        session_response = get_supabase_client().table('internet_sessions')\
            .select('*')\
            .eq('id', request.session_id)\
            .eq('user_id', current_user_id)\
            .execute()
        
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_response.data[0]
        
        # Generate unique access token
        access_token = f"wifi_{secrets.token_hex(24)}"
        
        # Create JWT token for device authentication
        token_payload = {
            "user_id": current_user_id,
            "session_id": request.session_id,
            "access_token": access_token,
            "data_limit_mb": request.data_limit_mb,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=request.time_limit_hours)
        }
        
        session_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")
        
        # Generate session-specific WiFi password (first 12 chars of token)
        wifi_password = access_token[:12].upper()
        
        # Create WiFi access token record
        wifi_token_record = {
            "user_id": current_user_id,
            "session_id": request.session_id,
            "access_token": access_token,
            "network_name": "KSWIFI",
            "wifi_password": wifi_password,
            "wifi_security": "WPA2",
            "data_limit_mb": request.data_limit_mb,
            "bandwidth_limit_mbps": 10,  # Default bandwidth limit
            "status": "active",
            "expires_at": (datetime.utcnow() + timedelta(hours=request.time_limit_hours)).isoformat(),
            "session_token": session_token  # Store for reference
        }
        
        # Store in database
        response = get_supabase_client().table('wifi_access_tokens').insert(wifi_token_record).execute()
        
        if not response.data:
            raise Exception("Failed to create WiFi access token")
        
        stored_token = response.data[0]
        
        # Generate WiFi QR code with embedded token
        # Format: WIFI:T:WPA;S:KSWIFI;P:password_token;H:false;;
        # The token is embedded in the password field and will be extracted by VPS
        wifi_qr_data = f"WIFI:T:WPA;S:KSWIFI;P:{wifi_password}#{session_token};H:false;;"
        
        # Generate QR code image
        qr_image = _generate_qr_image(wifi_qr_data)
        
        logger.info(f"✅ QR TOKEN GENERATED: {access_token}")
        
        return {
            "success": True,
            "token_id": stored_token["id"],
            "access_token": access_token,
            "qr_code_image": qr_image,
            "qr_data": wifi_qr_data,
            "network_name": "KSWIFI",
            "wifi_password": wifi_password,  # For debugging only
            "session_token": session_token,  # For debugging only
            "data_limit_mb": request.data_limit_mb,
            "expires_at": stored_token["expires_at"],
            "instructions": [
                "1. Scan this QR code with your device camera",
                "2. Your device will automatically connect to KSWIFI",
                "3. Internet access will be granted automatically",
                "4. No manual configuration required"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ QR TOKEN ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-status/{session_id}")
async def get_session_status(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get current session status and usage"""
    try:
        # Get session data
        session_response = get_supabase_client().table('wifi_access_tokens')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('user_id', current_user_id)\
            .execute()
        
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_response.data[0]
        
        # Get connected devices
        devices_response = get_supabase_client().table('wifi_device_connections')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('status', 'connected')\
            .execute()
        
        connected_devices = devices_response.data if devices_response.data else []
        
        # Calculate usage statistics
        total_data_used = session_data.get('data_used_mb', 0)
        data_limit = session_data.get('data_limit_mb', 0)
        remaining_data = max(0, data_limit - total_data_used)
        
        return {
            "session_id": session_id,
            "status": session_data.get('status'),
            "network_name": "KSWIFI",
            "connected_devices": len(connected_devices),
            "data_used_mb": total_data_used,
            "data_limit_mb": data_limit,
            "remaining_data_mb": remaining_data,
            "bandwidth_limit_mbps": session_data.get('bandwidth_limit_mbps'),
            "expires_at": session_data.get('expires_at'),
            "created_at": session_data.get('created_at'),
            "devices": [
                {
                    "mac": device.get('device_mac'),
                    "ip": device.get('device_ip'),
                    "connected_at": device.get('connected_at')
                }
                for device in connected_devices
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ SESSION STATUS ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/revoke-session/{session_id}")
async def revoke_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Revoke a WiFi session and disconnect all devices"""
    try:
        # Update session status
        update_response = get_supabase_client().table('wifi_access_tokens')\
            .update({"status": "revoked", "updated_at": datetime.utcnow().isoformat()})\
            .eq('session_id', session_id)\
            .eq('user_id', current_user_id)\
            .execute()
        
        if not update_response.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get connected devices to disconnect them
        devices_response = get_supabase_client().table('wifi_device_connections')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('status', 'connected')\
            .execute()
        
        disconnected_count = 0
        if devices_response.data:
            for device in devices_response.data:
                # This would trigger VPS to disconnect the device
                # In practice, the VPS monitoring service would handle this
                disconnected_count += 1
        
        # Update device connection status
        get_supabase_client().table('wifi_device_connections')\
            .update({
                "status": "disconnected",
                "disconnected_at": datetime.utcnow().isoformat()
            })\
            .eq('session_id', session_id)\
            .execute()
        
        logger.info(f"✅ SESSION REVOKED: {session_id}, devices disconnected: {disconnected_count}")
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "revoked",
            "devices_disconnected": disconnected_count,
            "message": "Session revoked and all devices disconnected"
        }
        
    except Exception as e:
        logger.error(f"❌ SESSION REVOKE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def _check_session_limits(session_data: Dict, device_mac: str) -> Dict[str, Any]:
    """Check if session is within data/time/bandwidth limits"""
    
    try:
        # Check expiry
        expires_at = datetime.fromisoformat(session_data['expires_at'].replace('Z', '+00:00'))
        if expires_at <= datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
            return {"valid": False, "reason": "Session expired"}
        
        # Check data usage
        data_used = session_data.get('data_used_mb', 0)
        data_limit = session_data.get('data_limit_mb', 0)
        if data_used >= data_limit:
            return {"valid": False, "reason": "Data limit exceeded"}
        
        # Check if session is active
        if session_data.get('status') != 'active':
            return {"valid": False, "reason": f"Session status: {session_data.get('status')}"}
        
        # Additional checks can be added here (bandwidth, concurrent devices, etc.)
        
        return {"valid": True, "reason": "All limits OK"}
        
    except Exception as e:
        logger.error(f"❌ LIMITS CHECK ERROR: {str(e)}")
        return {"valid": False, "reason": f"Error checking limits: {str(e)}"}

async def _log_device_connection(session_id: str, device_mac: str, device_ip: str, status: str):
    """Log device connection to database"""
    
    try:
        connection_record = {
            "session_id": session_id,
            "device_mac": device_mac,
            "device_ip": device_ip,
            "status": status,
            "connected_at": datetime.utcnow().isoformat(),
            "user_agent": "WiFi-Device"
        }
        
        get_supabase_client().table('wifi_device_connections').insert(connection_record).execute()
        logger.info(f"✅ LOGGED CONNECTION: {device_mac} -> {status}")
        
    except Exception as e:
        logger.error(f"❌ LOG CONNECTION ERROR: {str(e)}")

def _generate_qr_image(qr_data: str) -> str:
    """Generate QR code image from data"""
    
    import qrcode
    import qrcode.image.pil
    import io
    import base64
    
    # Create QR code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=6,
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(
        fill_color="#000000",
        back_color="#FFFFFF",
        image_factory=qrcode.image.pil.PilImage
    )
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# Update existing WiFi service to use new token-based system
def update_existing_wifi_service():
    """
    Instructions to update your existing WiFi service:
    
    1. Replace the QR generation in wifi_captive_service.py:
       - Use the new generate_qr_with_token endpoint
       - Embed session tokens in QR codes
       - Use session-specific WiFi passwords
    
    2. Update the generate-esim endpoint in routes/esim.py:
       - Call the new generate-qr-token endpoint instead
       - Return the token-embedded QR code
    
    3. Add database migration for new columns:
       - wifi_access_tokens.session_token (TEXT)
       - wifi_device_connections.session_id (UUID)
    """
    pass