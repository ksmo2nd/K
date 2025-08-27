"""
Dual eSIM service integrating osmo-smdpp and WiFi captive portal
"""

from typing import Dict, Optional, Any, List
from datetime import datetime

from .osmo_smdp_service import OsmoSMDPService
from .wifi_captive_service import WiFiCaptiveService
from ..core.database import get_supabase_client


class DualESIMService:
    """Service managing both private osmo-smdpp and public WiFi eSIM systems"""
    
    def __init__(self):
        self.osmo_service = OsmoSMDPService()
        self.wifi_service = WiFiCaptiveService()
        self.private_password = "OLAmilekan@$112"
    
    async def generate_esim_options(self, user_id: str, session_id: str, bundle_size_mb: int, access_password: Optional[str] = None) -> Dict[str, Any]:
        """Generate eSIM options based on access level"""
        
        try:
            print(f"🔄 DUAL eSIM: Generating options for user {user_id}, session {session_id}")
            
            # Check if user provided private access password
            has_private_access = access_password and self.osmo_service.validate_private_access(access_password)
            
            result = {
                "user_id": user_id,
                "session_id": session_id,
                "bundle_size_mb": bundle_size_mb,
                "timestamp": datetime.utcnow().isoformat(),
                "options": []
            }
            
            # Always provide public WiFi option
            try:
                wifi_token = await self.wifi_service.create_wifi_access_token(user_id, session_id, bundle_size_mb)
                wifi_qr_code = self.wifi_service.generate_wifi_qr_code(wifi_token["wifi_qr_data"])
                
                public_option = {
                    "type": "public_wifi",
                    "access_level": "public",
                    "title": "🌐 Public WiFi Access",
                    "description": f"Connect to {wifi_token['network_name']} for {bundle_size_mb}MB internet access",
                    "qr_code_image": wifi_qr_code,
                    "qr_code_data": wifi_token["wifi_qr_data"],
                    "captive_portal_url": wifi_token["captive_portal_url"],
                    "access_token": wifi_token["access_token"],
                    "network_name": wifi_token["network_name"],
                    "data_limit_mb": bundle_size_mb,
                    "time_limit_minutes": wifi_token["time_limit_minutes"],
                    "setup_instructions": [
                        "📱 AUTOMATIC SETUP:",
                        "1. Scan the QR code with your device camera",
                        "2. Connect to the WiFi network that appears",
                        "3. Open any website - you'll be redirected to the portal",
                        "4. Your internet access will be activated automatically",
                        "",
                        "🔧 MANUAL SETUP:",
                        f"1. Connect to WiFi network: {wifi_token['network_name']}",
                        "2. Open browser and go to any website",
                        f"3. You'll be redirected to: {wifi_token['captive_portal_url']}",
                        "4. Follow the portal instructions for access"
                    ]
                }
                
                result["options"].append(public_option)
                print(f"✅ DUAL eSIM: Public WiFi option created")
                
            except Exception as e:
                print(f"❌ DUAL eSIM: Failed to create public option: {str(e)}")
            
            # Add private osmo-smdpp option if password is correct
            if has_private_access:
                try:
                    osmo_profile = await self.osmo_service.create_osmo_profile(user_id, session_id, bundle_size_mb, access_password)
                    osmo_qr_code = self.osmo_service.generate_osmo_qr_code(osmo_profile["activation_code"])
                    
                    private_option = {
                        "type": "private_osmo",
                        "access_level": "private",
                        "title": "🔒 Private eSIM Profile",
                        "description": f"GSMA-compliant eSIM profile for {bundle_size_mb}MB with osmo-smdpp",
                        "qr_code_image": osmo_qr_code,
                        "activation_code": osmo_profile["activation_code"],
                        "profile_id": osmo_profile["profile_id"],
                        "iccid": osmo_profile["iccid"],
                        "profile_name": osmo_profile["profile_name"],
                        "smdp_server": osmo_profile["smdp_server"],
                        "bundle_size_mb": bundle_size_mb,
                        "setup_instructions": [
                            "📱 AUTOMATIC SETUP:",
                            "1. Scan the QR code with your device camera",
                            "2. Follow iPhone/Android prompts to add cellular plan",
                            "3. Enable the new cellular plan for data",
                            "4. Internet access through private network activated",
                            "",
                            "🔧 MANUAL SETUP:",
                            "1. Go to Settings > Cellular > Add Cellular Plan",
                            "2. Choose 'Enter Details Manually'",
                            f"3. SM-DP+ Address: {osmo_profile['smdp_server']}",
                            f"4. Activation Code: {osmo_profile['activation_code']}",
                            "5. Follow setup prompts to complete installation"
                        ]
                    }
                    
                    result["options"].append(private_option)
                    print(f"🔒 DUAL eSIM: Private osmo option created")
                    
                except Exception as e:
                    print(f"❌ DUAL eSIM: Failed to create private option: {str(e)}")
            
            # Add summary information
            result["summary"] = {
                "total_options": len(result["options"]),
                "has_public_access": any(opt["type"] == "public_wifi" for opt in result["options"]),
                "has_private_access": any(opt["type"] == "private_osmo" for opt in result["options"]),
                "private_access_available": has_private_access,
                "bundle_size_mb": bundle_size_mb
            }
            
            print(f"✅ DUAL eSIM: Generated {len(result['options'])} options")
            return result
            
        except Exception as e:
            print(f"❌ DUAL eSIM ERROR: {str(e)}")
            raise Exception(f"Failed to generate eSIM options: {str(e)}")
    
    async def get_user_esim_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's eSIM history from both systems"""
        
        try:
            # Get osmo profiles
            osmo_profiles = await self.osmo_service.get_user_osmo_profiles(user_id)
            
            # Get WiFi tokens
            wifi_tokens = await self.wifi_service.get_user_wifi_tokens(user_id)
            
            return {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "private_profiles": {
                    "count": len(osmo_profiles),
                    "profiles": osmo_profiles
                },
                "public_tokens": {
                    "count": len(wifi_tokens),
                    "tokens": wifi_tokens
                },
                "total_esims": len(osmo_profiles) + len(wifi_tokens)
            }
            
        except Exception as e:
            print(f"❌ DUAL eSIM ERROR: Failed to get history: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e),
                "private_profiles": {"count": 0, "profiles": []},
                "public_tokens": {"count": 0, "tokens": []},
                "total_esims": 0
            }
    
    def validate_private_access(self, password: str) -> bool:
        """Validate private access password"""
        return self.osmo_service.validate_private_access(password)
    
    async def activate_esim_by_type(self, esim_type: str, esim_id: str, user_id: str) -> Dict[str, Any]:
        """Activate eSIM based on type"""
        
        try:
            if esim_type == "private_osmo":
                return await self.osmo_service.activate_osmo_profile(esim_id, user_id)
            elif esim_type == "public_wifi":
                # WiFi tokens are activated when used in captive portal
                return {
                    "success": True,
                    "message": "WiFi access token is ready for use",
                    "activation_method": "captive_portal"
                }
            else:
                raise Exception(f"Unknown eSIM type: {esim_type}")
                
        except Exception as e:
            print(f"❌ DUAL eSIM ERROR: Activation failed: {str(e)}")
            raise Exception(f"Failed to activate eSIM: {str(e)}")
    
    async def get_session_esim_options(self, session_id: str) -> Dict[str, Any]:
        """Get eSIM options for a specific session"""
        
        try:
            # Get session details
            response = get_supabase_client().table('internet_sessions').select('*').eq('id', session_id).execute()
            
            if not response.data:
                raise Exception("Session not found")
            
            session = response.data[0]
            
            # Check for existing eSIM options
            osmo_response = get_supabase_client().table('osmo_esim_profiles').select('*').eq('session_id', session_id).execute()
            wifi_response = get_supabase_client().table('wifi_access_tokens').select('*').eq('session_id', session_id).execute()
            
            return {
                "session_id": session_id,
                "session_data": session,
                "existing_options": {
                    "private_profiles": osmo_response.data if osmo_response.data else [],
                    "public_tokens": wifi_response.data if wifi_response.data else []
                },
                "can_create_new": session["status"] == "active",
                "bundle_size_mb": session["data_mb"]
            }
            
        except Exception as e:
            print(f"❌ DUAL eSIM ERROR: Failed to get session options: {str(e)}")
            raise Exception(f"Failed to get session eSIM options: {str(e)}")