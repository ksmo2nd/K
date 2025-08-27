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


@router.get("/health")
async def dual_esim_health():
    """Health check for dual eSIM system"""
    return {
        "status": "healthy",
        "service": "Dual eSIM System",
        "endpoints": [
            "/generate-options",
            "/validate-private-access", 
            "/history",
            "/activate",
            "/captive/portal",
            "/captive/connect"
        ]
    }


@router.get("/test-generate/{session_id}/{bundle_size_mb}")
async def test_generate_esim_options(
    session_id: str,
    bundle_size_mb: int,
    access_password: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """SM-DP+ compatible eSIM activation endpoint"""
    try:
        print(f"🔄 SM-DP+ ESIM: Session: {session_id}, Size: {bundle_size_mb}, Password: {bool(access_password)}")
        
        # Generate SM-DP+ compatible activation code
        activation_code = f"LPA:1$kswifi.onrender.com${session_id}"
        
        # Create iPhone-compatible response
        esim_data = {
            "public_wifi": {
                "type": "public_wifi",
                "activation_code": activation_code,
                "matching_id": session_id,
                "qr_code": activation_code,  # iPhone scans this
                "instructions": [
                    "Open iPhone Settings",
                    "Go to Cellular > Add Cellular Plan", 
                    "Scan the QR code below",
                    "Follow iPhone setup prompts"
                ],
                "access_method": "Public WiFi Portal"
            }
        }
        
        # Add private eSIM if password provided
        if access_password == "OLAmilekan@$112":
            private_activation = f"LPA:1$kswifi.onrender.com$private_{session_id}"
            esim_data["private_osmo"] = {
                "type": "private_osmo",
                "activation_code": private_activation,
                "matching_id": f"private_{session_id}",
                "qr_code": private_activation,
                "instructions": [
                    "Open iPhone Settings",
                    "Go to Cellular > Add Cellular Plan",
                    "Scan the private QR code below", 
                    "Enjoy premium network access"
                ],
                "access_method": "Private Network (Password Protected)"
            }
        
        summary = {
            "total_options": len(esim_data),
            "session_id": session_id,
            "bundle_size_mb": bundle_size_mb,
            "status": "ready_for_activation"
        }
        
        print(f"✅ SM-DP+ ESIM: Generated {len(esim_data)} options")
        
        return {
            "success": True,
            "data": {
                "options": esim_data,
                "summary": summary
            },
            "message": f"Generated {len(esim_data)} eSIM activation options"
        }
        
    except Exception as e:
        print(f"❌ SM-DP+ ESIM ERROR: {str(e)}")
        import traceback
        print(f"❌ SM-DP+ TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smdp/{matching_id}")
async def smdp_activation_endpoint(matching_id: str):
    """SM-DP+ server endpoint for iPhone eSIM activation"""
    try:
        print(f"📱 IPHONE ESIM REQUEST: Matching ID: {matching_id}")
        
        # iPhone is requesting eSIM profile data
        # This is what gets called when iPhone scans the QR code
        
        profile_data = {
            "header": {
                "functionExecutionStatus": {
                    "status": "Executed-Success"
                }
            },
            "profileInstallationResult": {
                "baseResponse": {
                    "functionExecutionStatus": {
                        "status": "Executed-Success"
                    }
                },
                "profileInstallationResultData": {
                    "iccid": f"89014103211118510720{matching_id[:8]}",
                    "smdpOid": "1.3.6.1.4.1.31746",
                    "finalResult": {
                        "successResult": {}
                    }
                }
            }
        }
        
        print(f"✅ IPHONE ESIM: Sending profile data for {matching_id}")
        
        return profile_data
        
    except Exception as e:
        print(f"❌ SMDP ERROR: {str(e)}")
        return {
            "header": {
                "functionExecutionStatus": {
                    "status": "Failed",
                    "statusCodeData": {
                        "subjectCode": "8.11.1",
                        "reasonCode": "3.9",
                        "subjectIdentifier": "ProfileInstallation",
                        "message": str(e)
                    }
                }
            }
        }


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
        print(f"🔄 POST DUAL eSIM: Request received")
        print(f"🔄 POST DUAL eSIM: User ID: {user_id}")
        print(f"🔄 POST DUAL eSIM: Request data: {request.dict()}")
        
        # Use the same logic as the GET test endpoint
        session_id = request.session_id
        bundle_size_mb = request.bundle_size_mb
        access_password = request.access_password
        
        # Generate SM-DP+ compatible activation code
        activation_code = f"LPA:1$kswifi.onrender.com${session_id}"
        
        # Create iPhone-compatible response
        esim_data = {
            "public_wifi": {
                "type": "public_wifi",
                "activation_code": activation_code,
                "matching_id": session_id,
                "qr_code": activation_code,  # iPhone scans this
                "instructions": [
                    "Open iPhone Settings",
                    "Go to Cellular > Add Cellular Plan", 
                    "Scan the QR code below",
                    "Follow iPhone setup prompts"
                ],
                "access_method": "Public WiFi Portal"
            }
        }
        
        # Add private eSIM if password provided
        if access_password == "OLAmilekan@$112":
            private_activation = f"LPA:1$kswifi.onrender.com$private_{session_id}"
            esim_data["private_osmo"] = {
                "type": "private_osmo",
                "activation_code": private_activation,
                "matching_id": f"private_{session_id}",
                "qr_code": private_activation,
                "instructions": [
                    "Open iPhone Settings",
                    "Go to Cellular > Add Cellular Plan",
                    "Scan the private QR code below", 
                    "Enjoy premium network access"
                ],
                "access_method": "Private Network (Password Protected)"
            }
        
        summary = {
            "total_options": len(esim_data),
            "session_id": session_id,
            "bundle_size_mb": bundle_size_mb,
            "status": "ready_for_activation"
        }
        
        print(f"✅ POST DUAL eSIM: Generated {len(esim_data)} options")
        
        return {
            "success": True,
            "data": {
                "options": esim_data,
                "summary": summary
            },
            "message": f"Generated {len(esim_data)} eSIM activation options"
        }
        
    except Exception as e:
        print(f"❌ POST DUAL eSIM ERROR: {str(e)}")
        print(f"❌ POST DUAL eSIM ERROR TYPE: {type(e).__name__}")
        import traceback
        print(f"❌ POST DUAL eSIM TRACEBACK: {traceback.format_exc()}")
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