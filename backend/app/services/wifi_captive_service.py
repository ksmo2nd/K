"""
WiFi captive portal service for public network access
"""

import secrets
import qrcode
import io
import base64
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import json

from ..core.config import settings
from ..core.database import get_supabase_client


class WiFiCaptiveService:
    """Service for WiFi captive portal and public access"""
    
    def __init__(self):
        self.captive_portal_domain = "portal.kswifi.app"
        self.public_wifi_name = "KSWiFi-Public"
        self.default_session_limit = 60  # minutes
        self.default_bandwidth_limit = 10  # Mbps
    
    async def create_wifi_access_token(self, user_id: str, session_id: str, data_limit_mb: int) -> Dict[str, Any]:
        """Create WiFi access token for public use"""
        
        try:
            print(f"🌐 WIFI DEBUG: Creating public WiFi token for user {user_id}")
            
            # Generate secure access token
            access_token = f"wifi_{secrets.token_hex(24)}"
            
            # Create captive portal URL
            captive_portal_url = f"https://{self.captive_portal_domain}/connect?token={access_token}"
            
            # Generate QR code data (direct WiFi connection + portal)
            wifi_qr_data = self._generate_wifi_qr_data(access_token)
            
            # Create token record
            token_record = {
                "user_id": user_id,
                "session_id": session_id,
                "access_token": access_token,
                "qr_code_data": wifi_qr_data,
                "token_type": "wifi_access",
                "network_name": self.public_wifi_name,
                "captive_portal_url": captive_portal_url,
                "redirect_url": "https://kswifi.app/welcome",
                "bandwidth_limit_mbps": self.default_bandwidth_limit,
                "time_limit_minutes": self.default_session_limit,
                "data_limit_mb": data_limit_mb,
                "status": "active",
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            # Store in database
            response = get_supabase_client().table('wifi_access_tokens').insert(token_record).execute()
            
            if not response.data:
                raise Exception("Failed to create WiFi access token")
            
            stored_token = response.data[0]
            
            print(f"🌐 WIFI DEBUG: Token created with ID: {stored_token['id']}")
            
            return {
                "success": True,
                "token_id": stored_token["id"],
                "access_token": access_token,
                "captive_portal_url": captive_portal_url,
                "wifi_qr_data": wifi_qr_data,
                "network_name": self.public_wifi_name,
                "data_limit_mb": data_limit_mb,
                "time_limit_minutes": self.default_session_limit,
                "access_type": "public",
                "message": "Public WiFi access token created successfully"
            }
            
        except Exception as e:
            print(f"❌ WIFI ERROR: {str(e)}")
            raise Exception(f"Failed to create WiFi access token: {str(e)}")
    
    def _generate_wifi_qr_data(self, access_token: str) -> str:
        """Generate WiFi QR code data for direct connection"""
        
        # WiFi QR code format: WIFI:T:WPA;S:network_name;P:password;H:;;
        # For open network with captive portal: WIFI:T:nopass;S:network_name;H:;;
        
        wifi_config = {
            "type": "wifi",
            "network": self.public_wifi_name,
            "security": "open",  # Open network with captive portal
            "portal_url": f"https://{self.captive_portal_domain}/connect?token={access_token}",
            "token": access_token
        }
        
        # Standard WiFi QR format for open network
        wifi_qr_string = f"WIFI:T:nopass;S:{self.public_wifi_name};H:;;"
        
        return wifi_qr_string
    
    def generate_wifi_qr_code(self, wifi_qr_data: str) -> str:
        """Generate QR code image for WiFi connection"""
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(wifi_qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    async def validate_access_token(self, access_token: str, mac_address: str, ip_address: str) -> Dict[str, Any]:
        """Validate WiFi access token for captive portal"""
        
        try:
            # Get token from database
            response = get_supabase_client().table('wifi_access_tokens').select('*').eq('access_token', access_token).eq('status', 'active').execute()
            
            if not response.data:
                return {"valid": False, "error": "Invalid or expired access token"}
            
            token = response.data[0]
            
            # Check if token is expired
            if datetime.fromisoformat(token['expires_at'].replace('Z', '+00:00')) < datetime.utcnow().replace(tzinfo=None):
                return {"valid": False, "error": "Access token has expired"}
            
            # Check data limit
            if token['data_used_mb'] >= token['data_limit_mb']:
                return {"valid": False, "error": "Data limit exceeded"}
            
            return {
                "valid": True,
                "token_data": token,
                "remaining_data_mb": token['data_limit_mb'] - token['data_used_mb'],
                "time_limit_minutes": token['time_limit_minutes'],
                "bandwidth_limit_mbps": token['bandwidth_limit_mbps']
            }
            
        except Exception as e:
            print(f"❌ WIFI ERROR: Token validation failed: {str(e)}")
            return {"valid": False, "error": "Token validation failed"}
    
    async def create_captive_session(self, access_token: str, mac_address: str, ip_address: str, device_info: Dict = None) -> Dict[str, Any]:
        """Create captive portal session"""
        
        try:
            # Validate token first
            validation = await self.validate_access_token(access_token, mac_address, ip_address)
            
            if not validation["valid"]:
                raise Exception(validation["error"])
            
            token_data = validation["token_data"]
            
            # Generate session token
            session_token = f"session_{secrets.token_hex(16)}"
            
            # Create captive session record
            session_record = {
                "access_token_id": token_data["id"],
                "user_id": token_data["user_id"],
                "session_token": session_token,
                "mac_address": mac_address,
                "ip_address": ip_address,
                "device_type": device_info.get("device_type", "unknown") if device_info else "unknown",
                "user_agent": device_info.get("user_agent", "") if device_info else "",
                "device_fingerprint": device_info.get("fingerprint", "") if device_info else "",
                "gateway_ip": "192.168.1.1",  # Default gateway
                "dns_servers": ["8.8.8.8", "8.8.4.4"],
                "status": "active",
                "expires_at": (datetime.utcnow() + timedelta(minutes=token_data["time_limit_minutes"])).isoformat()
            }
            
            # Store session
            response = get_supabase_client().table('captive_portal_sessions').insert(session_record).execute()
            
            if not response.data:
                raise Exception("Failed to create captive session")
            
            session = response.data[0]
            
            # Update token usage
            get_supabase_client().table('wifi_access_tokens').update({
                "sessions_used": token_data["sessions_used"] + 1,
                "first_used_at": datetime.utcnow().isoformat() if not token_data.get("first_used_at") else token_data["first_used_at"],
                "last_used_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq('id', token_data["id"]).execute()
            
            return {
                "success": True,
                "session_id": session["id"],
                "session_token": session_token,
                "access_granted": True,
                "redirect_url": token_data["redirect_url"],
                "data_limit_mb": validation["remaining_data_mb"],
                "time_limit_minutes": token_data["time_limit_minutes"],
                "bandwidth_limit_mbps": token_data["bandwidth_limit_mbps"],
                "message": "Internet access granted"
            }
            
        except Exception as e:
            print(f"❌ WIFI ERROR: Session creation failed: {str(e)}")
            raise Exception(f"Failed to create captive session: {str(e)}")
    
    async def track_session_usage(self, session_token: str, data_used_mb: int, duration_minutes: int = 0) -> Dict[str, Any]:
        """Track captive portal session usage"""
        
        try:
            # Get session
            response = get_supabase_client().table('captive_portal_sessions').select('*, wifi_access_tokens!inner(*)').eq('session_token', session_token).execute()
            
            if not response.data:
                raise Exception("Session not found")
            
            session = response.data[0]
            token = session["wifi_access_tokens"]
            
            # Update session usage
            get_supabase_client().table('captive_portal_sessions').update({
                "data_used_mb": session["data_used_mb"] + data_used_mb,
                "duration_minutes": session["duration_minutes"] + duration_minutes,
                "updated_at": datetime.utcnow().isoformat()
            }).eq('session_token', session_token).execute()
            
            # Update token usage
            new_total_usage = token["data_used_mb"] + data_used_mb
            token_status = "used" if new_total_usage >= token["data_limit_mb"] else "active"
            
            get_supabase_client().table('wifi_access_tokens').update({
                "data_used_mb": new_total_usage,
                "status": token_status,
                "last_used_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq('id', token["id"]).execute()
            
            return {
                "success": True,
                "data_used_mb": new_total_usage,
                "remaining_data_mb": max(0, token["data_limit_mb"] - new_total_usage),
                "status": token_status
            }
            
        except Exception as e:
            print(f"❌ WIFI ERROR: Usage tracking failed: {str(e)}")
            raise Exception(f"Failed to track session usage: {str(e)}")
    
    async def get_user_wifi_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's WiFi access tokens"""
        try:
            response = get_supabase_client().table('wifi_access_tokens').select('*').eq('user_id', user_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ WIFI ERROR: Failed to get user tokens: {str(e)}")
            return []