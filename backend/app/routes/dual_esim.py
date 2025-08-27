"""
Dual eSIM API routes - osmo-smdpp + WiFi captive portal
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ..services.dual_esim_service import DualESIMService
from ..services.wifi_captive_service import WiFiCaptiveService
from ..core.auth import get_current_user_id

router = APIRouter()
dual_esim_service = DualESIMService()
wifi_service = WiFiCaptiveService()


class GenerateESIMOptionsRequest(BaseModel):
    session_id: str
    bundle_size_mb: int
    access_password: Optional[str] = None


class ValidatePrivateAccessRequest(BaseModel):
    password: str


class ActivateESIMRequest(BaseModel):
    esim_type: str  # "private_osmo" or "public_wifi"
    esim_id: str


class CaptivePortalConnectRequest(BaseModel):
    access_token: str
    mac_address: str
    device_info: Optional[Dict[str, Any]] = None


class TrackUsageRequest(BaseModel):
    session_token: str
    data_used_mb: int
    duration_minutes: Optional[int] = 0


@router.post("/generate-options")
async def generate_esim_options(
    request: GenerateESIMOptionsRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate eSIM options (public WiFi + private osmo if password provided)"""
    try:
        print(f"🔄 API: Generating eSIM options for user {user_id}")
        
        options = await dual_esim_service.generate_esim_options(
            user_id=user_id,
            session_id=request.session_id,
            bundle_size_mb=request.bundle_size_mb,
            access_password=request.access_password
        )
        
        return {
            "success": True,
            "data": options,
            "message": f"Generated {options['summary']['total_options']} eSIM options"
        }
        
    except Exception as e:
        print(f"❌ API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-private-access")
async def validate_private_access(request: ValidatePrivateAccessRequest):
    """Validate private access password"""
    try:
        is_valid = dual_esim_service.validate_private_access(request.password)
        
        return {
            "valid": is_valid,
            "message": "Private access granted" if is_valid else "Invalid password"
        }
        
    except Exception as e:
        print(f"❌ API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_esim_history(user_id: str = Depends(get_current_user_id)):
    """Get user's eSIM history from both systems"""
    try:
        history = await dual_esim_service.get_user_esim_history(user_id)
        
        return {
            "success": True,
            "data": history
        }
        
    except Exception as e:
        print(f"❌ API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activate")
async def activate_esim(
    request: ActivateESIMRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Activate eSIM by type"""
    try:
        result = await dual_esim_service.activate_esim_by_type(
            esim_type=request.esim_type,
            esim_id=request.esim_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"❌ API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/options")
async def get_session_esim_options(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get eSIM options for a specific session"""
    try:
        options = await dual_esim_service.get_session_esim_options(session_id)
        
        return {
            "success": True,
            "data": options
        }
        
    except Exception as e:
        print(f"❌ API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 🌐 CAPTIVE PORTAL ENDPOINTS
# =====================================================

@router.get("/captive/portal")
async def captive_portal_landing(request: Request):
    """Captive portal landing page"""
    token = request.query_params.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Access token required")
    
    # Return HTML for captive portal
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KSWiFi Public Access</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; margin: 0; }}
            .container {{ max-width: 400px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }}
            .logo {{ font-size: 2.5em; margin-bottom: 20px; }}
            .title {{ font-size: 1.5em; margin-bottom: 10px; }}
            .subtitle {{ opacity: 0.8; margin-bottom: 30px; }}
            .connect-btn {{ background: #4CAF50; color: white; border: none; padding: 15px 30px; font-size: 1.1em; border-radius: 8px; cursor: pointer; width: 100%; }}
            .connect-btn:hover {{ background: #45a049; }}
            .info {{ margin-top: 20px; font-size: 0.9em; opacity: 0.7; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🌐</div>
            <div class="title">Welcome to KSWiFi</div>
            <div class="subtitle">Free Public Internet Access</div>
            <button class="connect-btn" onclick="connectToInternet()">Connect to Internet</button>
            <div class="info">
                <p>✅ Secure connection</p>
                <p>⚡ High-speed internet</p>
                <p>🔒 Privacy protected</p>
            </div>
        </div>
        
        <script>
            async function connectToInternet() {{
                const btn = document.querySelector('.connect-btn');
                btn.textContent = 'Connecting...';
                btn.disabled = true;
                
                try {{
                    const response = await fetch('/api/dual-esim/captive/connect', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            access_token: '{token}',
                            mac_address: 'auto-detect',
                            device_info: {{
                                user_agent: navigator.userAgent,
                                device_type: /Mobile|Android|iPhone|iPad/.test(navigator.userAgent) ? 'mobile' : 'desktop'
                            }}
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        btn.textContent = '✅ Connected!';
                        btn.style.background = '#4CAF50';
                        setTimeout(() => {{
                            window.location.href = result.data.redirect_url || 'https://google.com';
                        }}, 1000);
                    }} else {{
                        btn.textContent = '❌ Connection Failed';
                        btn.style.background = '#f44336';
                        setTimeout(() => {{
                            btn.textContent = 'Try Again';
                            btn.disabled = false;
                            btn.style.background = '#4CAF50';
                        }}, 3000);
                    }}
                }} catch (error) {{
                    btn.textContent = '❌ Error';
                    btn.style.background = '#f44336';
                    setTimeout(() => {{
                        btn.textContent = 'Try Again';
                        btn.disabled = false;
                        btn.style.background = '#4CAF50';
                    }}, 3000);
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


@router.post("/captive/connect")
async def captive_portal_connect(request: CaptivePortalConnectRequest):
    """Connect to internet through captive portal"""
    try:
        # Get client IP
        client_ip = "192.168.1.100"  # In production, get from request headers
        
        session = await wifi_service.create_captive_session(
            access_token=request.access_token,
            mac_address=request.mac_address,
            ip_address=client_ip,
            device_info=request.device_info
        )
        
        return {
            "success": True,
            "data": session,
            "message": "Internet access granted successfully"
        }
        
    except Exception as e:
        print(f"❌ CAPTIVE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/captive/track-usage")
async def track_captive_usage(request: TrackUsageRequest):
    """Track captive portal usage"""
    try:
        result = await wifi_service.track_session_usage(
            session_token=request.session_token,
            data_used_mb=request.data_used_mb,
            duration_minutes=request.duration_minutes
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"❌ CAPTIVE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/captive/status/{access_token}")
async def get_captive_status(access_token: str):
    """Get captive portal access status"""
    try:
        validation = await wifi_service.validate_access_token(access_token, "unknown", "0.0.0.0")
        
        return {
            "success": True,
            "data": validation
        }
        
    except Exception as e:
        print(f"❌ CAPTIVE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class WiFiConnectionRequest(BaseModel):
    network_name: str
    device_mac: str


@router.post("/wifi/validate-connection")
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


@router.get("/wifi/session-info/{network_name}")
async def get_wifi_session_info(network_name: str):
    """Get WiFi session information by network name"""
    try:
        from ..core.database import get_supabase_client
        
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
                "status": session_data["status"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ WIFI SESSION INFO ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))