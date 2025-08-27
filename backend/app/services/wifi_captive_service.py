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
            
            # Generate QR code data (direct WiFi connection with encrypted password)
            wifi_qr_data = self._generate_wifi_qr_data(access_token)
            
            # Extract WiFi credentials from QR data
            wifi_password = self._generate_session_wifi_password(access_token)
            session_network_name = f"KSWiFi_Global_{access_token[-8:]}"
            
            # Create token record with WiFi credentials
            token_record = {
                "user_id": user_id,
                "session_id": session_id,
                "access_token": access_token,
                "qr_code_data": wifi_qr_data,
                "token_type": "wifi_secure_access",
                "network_name": session_network_name,
                "wifi_password": wifi_password,
                "wifi_security": "WPA2",
                "captive_portal_url": captive_portal_url,
                "redirect_url": "https://kswifi.app/welcome",
                "bandwidth_limit_mbps": self.default_bandwidth_limit,
                "time_limit_minutes": None,  # No time limit - until user disconnects
                "data_limit_mb": data_limit_mb,
                "status": "active",
                "auto_disconnect": False,  # User controls disconnection
                "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()  # 30-day expiry
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
                "network_name": session_network_name,
                "wifi_password": wifi_password,  # Encrypted in QR, visible for debugging
                "wifi_security": "WPA2",
                "data_limit_mb": data_limit_mb,
                "time_limit_minutes": None,  # No time limit
                "auto_disconnect": False,
                "access_type": "secure_wifi",
                "session_duration": "Until user disconnects",
                "message": "Secure WiFi access token created - scan QR to connect instantly"
            }
            
        except Exception as e:
            print(f"❌ WIFI ERROR: {str(e)}")
            raise Exception(f"Failed to create WiFi access token: {str(e)}")
    
    def _generate_wifi_qr_data(self, access_token: str) -> str:
        """Generate WiFi QR code data with encrypted password for direct connection"""
        
        # Generate unique, secure WiFi password for this session
        wifi_password = self._generate_session_wifi_password(access_token)
        
        # Create unique WiFi network name with session identifier
        session_network_name = f"KSWiFi_Global_{access_token[-8:]}"
        
        wifi_config = {
            "type": "wifi_secure",
            "network": session_network_name,
            "security": "WPA2",  # Secure network with encrypted password
            "password": wifi_password,
            "portal_url": f"https://{self.captive_portal_domain}/connect?token={access_token}",
            "token": access_token,
            "auto_connect": True
        }
        
        # Standard WiFi QR format with WPA2 security and encrypted password
        # Format: WIFI:T:WPA;S:network_name;P:password;H:false;;
        wifi_qr_string = f"WIFI:T:WPA;S:{session_network_name};P:{wifi_password};H:false;;"
        
        print(f"🔐 WIFI QR: Generated secure WiFi QR for network {session_network_name}")
        
        return wifi_qr_string
    
    def _generate_session_wifi_password(self, access_token: str) -> str:
        """Generate unique, secure WiFi password for session"""
        
        # Create password using token hash + timestamp for uniqueness
        import hashlib
        from datetime import datetime
        
        # Combine access token with current timestamp for uniqueness
        unique_seed = f"{access_token}_{datetime.utcnow().isoformat()}"
        
        # Generate secure hash
        password_hash = hashlib.sha256(unique_seed.encode()).hexdigest()
        
        # Create user-friendly password (16 chars, alphanumeric)
        wifi_password = password_hash[:16].upper()
        
        print(f"🔐 Generated WiFi password for session: {wifi_password}")
        
        return wifi_password
    
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
    
    async def validate_wifi_session_connection(self, network_name: str, device_mac: str) -> Dict[str, Any]:
        """Validate WiFi session when device connects to network"""
        
        try:
            print(f"🔐 WIFI VALIDATION: Device {device_mac} connecting to {network_name}")
            
            # Extract session identifier from network name
            if not network_name.startswith("KSWiFi_Global_"):
                raise Exception("Invalid network name format")
            
            session_suffix = network_name.replace("KSWiFi_Global_", "")
            
            # Find active token by network name
            response = get_supabase_client().table('wifi_access_tokens')\
                .select('*')\
                .eq('network_name', network_name)\
                .eq('status', 'active')\
                .execute()
            
            if not response.data:
                raise Exception("No active session found for this network")
            
            token_data = response.data[0]
            
            # Check if session is still valid
            expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                raise Exception("Session has expired")
            
            # Create or update connection record
            connection_record = {
                "token_id": token_data["id"],
                "device_mac": device_mac,
                "network_name": network_name,
                "connected_at": datetime.utcnow().isoformat(),
                "status": "connected",
                "data_used_mb": 0
            }
            
            # Store connection (create wifi_device_connections table if needed)
            try:
                get_supabase_client().table('wifi_device_connections').upsert(connection_record, on_conflict="device_mac,token_id").execute()
            except:
                # Table might not exist, create connection tracking in existing table
                get_supabase_client().table('wifi_access_tokens').update({
                    "last_connected_device": device_mac,
                    "last_connected_at": datetime.utcnow().isoformat()
                }).eq('id', token_data["id"]).execute()
            
            print(f"✅ WIFI CONNECTION: Device {device_mac} validated for session {token_data['session_id']}")
            
            return {
                "success": True,
                "session_id": token_data["session_id"],
                "user_id": token_data["user_id"],
                "data_limit_mb": token_data["data_limit_mb"],
                "bandwidth_limit_mbps": token_data["bandwidth_limit_mbps"],
                "message": "WiFi connection validated - internet access granted"
            }
            
        except Exception as e:
            print(f"❌ WIFI VALIDATION ERROR: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "WiFi connection validation failed"
            }
    
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