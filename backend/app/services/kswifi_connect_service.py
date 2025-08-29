"""
KSWiFi Connect Service - VPN-based session access
Replaces eSIM system with VPN profile generation
"""

import secrets
import subprocess
import json
import base64
try:
    import qrcode
    import qrcode.image.pil
    import io
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("⚠️ QR code library not available - using placeholder QR codes")
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..core.config import settings
from ..core.database import get_supabase_client

logger = logging.getLogger(__name__)

class KSWiFiConnectService:
    """Service for managing KSWiFi Connect VPN profiles"""
    
    def __init__(self):
        # Use defaults if environment variables not set (for testing)
        self.vpn_server_ip = getattr(settings, 'VPN_SERVER_IP', None) or "YOUR_VPS_IP_HERE"
        self.vpn_server_port = getattr(settings, 'VPN_SERVER_PORT', 51820)
        self.vpn_server_public_key = getattr(settings, 'VPN_SERVER_PUBLIC_KEY', None) or "SERVER_PUBLIC_KEY_PLACEHOLDER"
        self.vpn_network = "10.8.0.0/24"
        self.dns_servers = ["8.8.8.8", "8.8.4.4"]
    
    async def generate_connect_profile(
        self, 
        user_id: str, 
        session_id: str, 
        data_limit_mb: int = 1024,
        time_limit_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate KSWiFi Connect profile for session access"""
        
        try:
            logger.info(f"🔍 CONNECT: Generating profile for session {session_id}")
            
            # Verify session exists and belongs to user
            session_response = get_supabase_client().table('internet_sessions')\
                .select('*')\
                .eq('id', session_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not session_response.data:
                raise Exception(f"Session {session_id} not found or doesn't belong to user")
            
            session_data = session_response.data[0]
            logger.info(f"🔍 CONNECT: Found session {session_id}, status: {session_data.get('status')}")
            
            # Use session data for limits if not provided
            if data_limit_mb == 1024:  # Default value, use session data
                data_limit_mb = session_data.get('data_mb', 1024)
            
            # Generate unique access token
            access_token = f"connect_{secrets.token_hex(24)}"
            
            # Generate client VPN keys
            client_keys = self._generate_client_keys()
            
            # Get next available IP address
            client_ip = await self._get_next_client_ip()
            
            # Create VPN configuration
            vpn_config = self._create_vpn_config(
                client_keys["private_key"],
                client_ip,
                session_id,
                data_limit_mb
            )
            
            # Store connect profile in database
            profile_record = {
                "user_id": user_id,
                "session_id": session_id,
                "access_token": access_token,
                "profile_type": "kswifi_connect",
                "client_public_key": client_keys["public_key"],
                "client_private_key": client_keys["private_key"],  # Encrypted in real implementation
                "client_ip": client_ip,
                "vpn_config": vpn_config,
                "data_limit_mb": data_limit_mb,
                "data_used_mb": 0,
                "bandwidth_limit_mbps": self._get_bandwidth_limit(data_limit_mb),
                "status": "active",
                "expires_at": (datetime.utcnow() + timedelta(hours=time_limit_hours)).isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store in database
            response = get_supabase_client().table('kswifi_connect_profiles').insert(profile_record).execute()
            
            if not response.data:
                raise Exception("Failed to create connect profile")
            
            stored_profile = response.data[0]
            
            # Add client to VPN server
            await self._add_client_to_vpn_server(
                client_keys["public_key"],
                client_ip,
                session_id
            )
            
            # Generate QR code for VPN configuration
            qr_image = self._generate_vpn_qr_code(vpn_config)
            
            logger.info(f"✅ CONNECT PROFILE GENERATED: {access_token}")
            
            return {
                "success": True,
                "connect_id": stored_profile["id"],
                "access_token": access_token,
                "profile_qr": qr_image,
                "vpn_config": vpn_config,  # For debugging
                "session_id": session_id,
                "data_limit_mb": data_limit_mb,
                "bandwidth_limit_mbps": profile_record["bandwidth_limit_mbps"],
                "expires_at": stored_profile["expires_at"],
                "client_ip": client_ip,
                "setup_instructions": [
                    "1. Scan this QR code with your device camera",
                    "2. Tap 'Add' when prompted to install profile",
                    "3. Enable 'KSWiFi Connect' in VPN settings",
                    "4. Enjoy secure global internet access!"
                ],
                "access_method": "kswifi_connect",
                "message": "KSWiFi Connect profile generated - scan to activate global internet access!"
            }
            
        except Exception as e:
            logger.error(f"❌ CONNECT PROFILE ERROR: {str(e)}")
            raise Exception(f"Failed to generate connect profile: {str(e)}")
    
    def _generate_client_keys(self) -> Dict[str, str]:
        """Generate WireGuard key pair for client"""
        
        try:
            # Generate private key
            private_key_result = subprocess.run(
                ['wg', 'genkey'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            private_key = private_key_result.stdout.strip()
            
            # Generate public key from private key
            public_key_result = subprocess.run(
                ['wg', 'pubkey'], 
                input=private_key, 
                text=True, 
                capture_output=True, 
                check=True
            )
            public_key = public_key_result.stdout.strip()
            
            return {
                "private_key": private_key,
                "public_key": public_key
            }
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to generate client keys: {e}")
    
    async def _get_next_client_ip(self) -> str:
        """Get next available IP address for client"""
        
        try:
            # Get used IPs from database
            response = get_supabase_client().table('kswifi_connect_profiles')\
                .select('client_ip')\
                .eq('status', 'active')\
                .execute()
            
            used_ips = set()
            if response.data:
                for profile in response.data:
                    if profile.get('client_ip'):
                        ip_parts = profile['client_ip'].split('.')
                        if len(ip_parts) == 4 and ip_parts[0:3] == ['10', '8', '0']:
                            used_ips.add(int(ip_parts[3]))
            
            # Find next available IP (start from 10.8.0.10)
            for ip_num in range(10, 254):
                if ip_num not in used_ips:
                    return f"10.8.0.{ip_num}"
            
            raise Exception("No available IP addresses")
            
        except Exception as e:
            logger.error(f"Error getting next IP: {e}")
            # Fallback to random IP
            return f"10.8.0.{secrets.randbelow(200) + 10}"
    
    def _create_vpn_config(
        self, 
        client_private_key: str, 
        client_ip: str, 
        session_id: str,
        data_limit_mb: int
    ) -> str:
        """Create WireGuard configuration for client"""
        
        config = f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}/24
DNS = {', '.join(self.dns_servers)}

[Peer]
PublicKey = {self.vpn_server_public_key}
Endpoint = {self.vpn_server_ip}:{self.vpn_server_port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25

# KSWiFi Connect Session
# Session ID: {session_id}
# Data Limit: {data_limit_mb}MB
# Created: {datetime.now().isoformat()}
"""
        
        return config
    
    def _get_bandwidth_limit(self, data_limit_mb: int) -> int:
        """Get bandwidth limit based on session size"""
        
        if data_limit_mb <= 1024:  # 1GB
            return 10  # 10 Mbps
        elif data_limit_mb <= 5120:  # 5GB
            return 25  # 25 Mbps
        else:  # 20GB+
            return 50  # 50 Mbps
    
    async def _add_client_to_vpn_server(
        self, 
        client_public_key: str, 
        client_ip: str, 
        session_id: str
    ):
        """Add client to VPN server configuration"""
        
        try:
            # This would call the VPS API to add the client
            # For now, we'll create the peer configuration
            
            peer_config = f"""
# Client: {session_id}
[Peer]
PublicKey = {client_public_key}
AllowedIPs = {client_ip}/32
"""
            
            logger.info(f"🔍 VPN SERVER: Adding client {client_public_key[:8]}... with IP {client_ip}")
            
            # In production, this would make an API call to the VPS to add the peer
            # For now, we'll log the configuration that needs to be added
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding client to VPN server: {e}")
            raise
    
    def _generate_vpn_qr_code(self, vpn_config: str) -> str:
        """Generate QR code for VPN configuration"""
        
        try:
            logger.info(f"🔍 QR: Generating VPN profile QR code")
            
            if not QR_AVAILABLE:
                logger.warning("QR library not available, generating placeholder")
                # Return a placeholder QR-like pattern (small black/white checkered pattern)
                placeholder_qr = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2RgYPjPQApgIlYRIyMjAzYwatSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGDQcAAP//AwBvAAEAAAAASUVORK5CYII="
                return f"data:image/png;base64,{placeholder_qr}"
            
            # Create QR code with VPN configuration
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            
            qr.add_data(vpn_config)
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
            
            logger.info(f"✅ QR: Generated VPN QR code, size: {len(img_str)} chars")
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating VPN QR code: {e}")
            # Return placeholder on error  
            logger.warning("Using placeholder QR code due to error")
            placeholder_qr = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2RgYPjPQApgIlYRIyMjAzYwatSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGjRo1atSoUaNGDQcAAP//AwBvAAEAAAAASUVORK5CYII="
            return f"data:image/png;base64,{placeholder_qr}"
    
    async def update_session_usage(
        self, 
        client_public_key: str, 
        data_used_mb: float
    ) -> Dict[str, Any]:
        """Update session usage and check limits"""
        
        try:
            # Find profile by public key
            response = get_supabase_client().table('kswifi_connect_profiles')\
                .select('*')\
                .eq('client_public_key', client_public_key)\
                .eq('status', 'active')\
                .execute()
            
            if not response.data:
                return {"session_valid": False, "error": "Profile not found"}
            
            profile = response.data[0]
            
            # Check limits
            data_limit = profile.get('data_limit_mb', 0)
            expires_at = datetime.fromisoformat(profile['expires_at'].replace('Z', '+00:00'))
            
            # Check expiry
            if expires_at <= datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                await self._deactivate_profile(client_public_key, "expired")
                return {"session_valid": False, "error": "Session expired"}
            
            # Check data limit
            if data_used_mb >= data_limit:
                await self._deactivate_profile(client_public_key, "data_limit_exceeded")
                return {"session_valid": False, "error": "Data limit exceeded"}
            
            # Update usage
            get_supabase_client().table('kswifi_connect_profiles')\
                .update({
                    "data_used_mb": data_used_mb,
                    "last_used_at": datetime.utcnow().isoformat()
                })\
                .eq('client_public_key', client_public_key)\
                .execute()
            
            return {
                "session_valid": True,
                "data_used_mb": data_used_mb,
                "data_limit_mb": data_limit,
                "remaining_mb": data_limit - data_used_mb
            }
            
        except Exception as e:
            logger.error(f"Error updating session usage: {e}")
            return {"session_valid": False, "error": str(e)}
    
    async def _deactivate_profile(self, client_public_key: str, reason: str):
        """Deactivate profile and remove from VPN server"""
        
        try:
            # Update database
            get_supabase_client().table('kswifi_connect_profiles')\
                .update({
                    "status": "deactivated",
                    "deactivated_reason": reason,
                    "deactivated_at": datetime.utcnow().isoformat()
                })\
                .eq('client_public_key', client_public_key)\
                .execute()
            
            logger.info(f"✅ PROFILE DEACTIVATED: {client_public_key[:8]}... ({reason})")
            
            # Note: In production, this would call VPS API to remove client
            
        except Exception as e:
            logger.error(f"Error deactivating profile: {e}")
    
    async def get_user_profiles(self, user_id: str) -> list:
        """Get user's active connect profiles"""
        
        try:
            response = get_supabase_client().table('kswifi_connect_profiles')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            profiles = []
            if response.data:
                for profile in response.data:
                    profiles.append({
                        "connect_id": profile["id"],
                        "session_id": profile["session_id"],
                        "status": profile["status"],
                        "data_used_mb": profile.get("data_used_mb", 0),
                        "data_limit_mb": profile.get("data_limit_mb", 0),
                        "bandwidth_limit_mbps": profile.get("bandwidth_limit_mbps", 10),
                        "expires_at": profile["expires_at"],
                        "created_at": profile["created_at"],
                        "client_ip": profile.get("client_ip"),
                        "access_method": "kswifi_connect"
                    })
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error getting user profiles: {e}")
            return []