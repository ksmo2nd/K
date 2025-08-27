"""
osmo-smdpp SM-DP+ server integration for private eSIM profiles
"""

import asyncio
import subprocess
import json
import secrets
import hashlib
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import struct
import os
import tempfile

from ..core.config import settings
from ..core.database import get_supabase_client
from ..models.enums import ESIMStatus


class OsmoSMDPService:
    """Service for osmo-smdpp SM-DP+ server integration"""
    
    def __init__(self):
        self.osmo_server_url = "osmo.kswifi.local"
        self.private_password = "OLAmilekan@$112"
        self.private_password_hash = hashlib.sha256(self.private_password.encode()).hexdigest()
        
        # osmo-smdpp configuration
        self.osmo_config = {
            "server_name": "KSWiFi Private Network",
            "server_address": self.osmo_server_url,
            "port": 8443,
            "certificate_path": "/etc/osmo-smdpp/certs/",
            "profile_storage": "/var/lib/osmo-smdpp/profiles/"
        }
    
    def validate_private_access(self, password: str) -> bool:
        """Validate private access password"""
        return password == self.private_password
    
    def generate_gsma_compliant_profile(self, user_id: str, session_id: str, bundle_size_mb: int) -> Dict[str, Any]:
        """Generate GSMA-compliant eSIM profile data"""
        
        # Generate unique identifiers following GSMA standards
        iccid = self._generate_iccid()
        imsi = self._generate_imsi()
        ki = self._generate_ki()
        opc = self._generate_opc()
        
        # Generate profile ID and activation code
        profile_id = f"kswifi_private_{secrets.token_hex(8)}"
        activation_code = f"LPA:1${self.osmo_server_url}${profile_id}"
        
        profile_data = {
            "profile_id": profile_id,
            "iccid": iccid,
            "imsi": imsi,
            "ki": ki,
            "opc": opc,
            "activation_code": activation_code,
            "profile_name": "KSWiFi Private Network",
            "profile_nickname": f"KSWiFi-{bundle_size_mb}MB",
            "bundle_size_mb": bundle_size_mb,
            "apn": "internet",
            "apn_username": f"kswifi_private_{secrets.token_hex(4)}",
            "apn_password": secrets.token_urlsafe(16),
            "smdp_server": self.osmo_server_url,
            "access_type": "private",
            "password_hash": self.private_password_hash
        }
        
        return profile_data
    
    def _generate_iccid(self) -> str:
        """Generate GSMA-compliant ICCID"""
        # Format: 89 + Country Code (91) + Issuer (KSWiFi: 001) + Account (12 digits) + Check digit
        country_code = "91"  # India (you can change this)
        issuer_code = "001"  # KSWiFi identifier
        account_number = f"{secrets.randbelow(10**12):012d}"
        
        # Calculate Luhn check digit
        partial_iccid = f"89{country_code}{issuer_code}{account_number}"
        check_digit = self._luhn_check_digit(partial_iccid)
        
        return f"{partial_iccid}{check_digit}"
    
    def _generate_imsi(self) -> str:
        """Generate GSMA-compliant IMSI"""
        # Format: MCC (3 digits) + MNC (2-3 digits) + MSIN (9-10 digits)
        mcc = "999"  # Test network
        mnc = "01"   # KSWiFi network
        msin = f"{secrets.randbelow(10**10):010d}"
        
        return f"{mcc}{mnc}{msin}"
    
    def _generate_ki(self) -> str:
        """Generate 128-bit authentication key (Ki)"""
        return secrets.token_hex(16).upper()
    
    def _generate_opc(self) -> str:
        """Generate 128-bit operator code (OPc)"""
        return secrets.token_hex(16).upper()
    
    def _luhn_check_digit(self, number: str) -> str:
        """Calculate Luhn algorithm check digit"""
        digits = [int(d) for d in number]
        checksum = 0
        
        # Process digits from right to left
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 0:  # Every second digit from right
                doubled = digit * 2
                checksum += doubled // 10 + doubled % 10
            else:
                checksum += digit
        
        return str((10 - (checksum % 10)) % 10)
    
    async def create_osmo_profile(self, user_id: str, session_id: str, bundle_size_mb: int, password: str) -> Dict[str, Any]:
        """Create osmo-smdpp eSIM profile with password validation"""
        
        # Validate private access
        if not self.validate_private_access(password):
            raise Exception("Invalid password for private eSIM access")
        
        try:
            print(f"🔒 OSMO DEBUG: Creating private eSIM profile for user {user_id}")
            
            # Generate GSMA-compliant profile
            profile_data = self.generate_gsma_compliant_profile(user_id, session_id, bundle_size_mb)
            
            # Create osmo-smdpp profile configuration
            osmo_profile_config = {
                "profile": {
                    "iccid": profile_data["iccid"],
                    "imsi": profile_data["imsi"],
                    "ki": profile_data["ki"],
                    "opc": profile_data["opc"],
                    "profile_name": profile_data["profile_name"],
                    "profile_nickname": profile_data["profile_nickname"],
                    "apn": {
                        "name": profile_data["apn"],
                        "username": profile_data["apn_username"],
                        "password": profile_data["apn_password"],
                        "auth_type": "PAP"
                    },
                    "network": {
                        "mcc": "999",
                        "mnc": "01",
                        "operator_name": "KSWiFi Private"
                    }
                },
                "sm_dp_plus": {
                    "server": self.osmo_server_url,
                    "port": 8443,
                    "certificate": "kswifi_private.crt"
                }
            }
            
            # Store profile in database
            profile_record = {
                "user_id": user_id,
                "session_id": session_id,
                "iccid": profile_data["iccid"],
                "imsi": profile_data["imsi"],
                "ki": profile_data["ki"],
                "opc": profile_data["opc"],
                "smdp_server": profile_data["smdp_server"],
                "activation_code": profile_data["activation_code"],
                "profile_id": profile_data["profile_id"],
                "profile_name": profile_data["profile_name"],
                "profile_nickname": profile_data["profile_nickname"],
                "apn": profile_data["apn"],
                "apn_username": profile_data["apn_username"],
                "apn_password": profile_data["apn_password"],
                "access_type": "private",
                "password_hash": profile_data["password_hash"],
                "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            # Insert into osmo_esim_profiles table
            response = get_supabase_client().table('osmo_esim_profiles').insert(profile_record).execute()
            
            if not response.data:
                raise Exception("Failed to store osmo profile in database")
            
            stored_profile = response.data[0]
            
            print(f"🔒 OSMO DEBUG: Profile created with ID: {stored_profile['id']}")
            
            return {
                "success": True,
                "profile_id": stored_profile["id"],
                "activation_code": profile_data["activation_code"],
                "iccid": profile_data["iccid"],
                "profile_name": profile_data["profile_name"],
                "profile_nickname": profile_data["profile_nickname"],
                "bundle_size_mb": bundle_size_mb,
                "access_type": "private",
                "smdp_server": self.osmo_server_url,
                "osmo_config": osmo_profile_config,
                "message": "Private eSIM profile created successfully"
            }
            
        except Exception as e:
            print(f"❌ OSMO ERROR: {str(e)}")
            raise Exception(f"Failed to create osmo profile: {str(e)}")
    
    async def get_user_osmo_profiles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's osmo-smdpp profiles"""
        try:
            response = get_supabase_client().table('osmo_esim_profiles').select('*').eq('user_id', user_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ OSMO ERROR: Failed to get user profiles: {str(e)}")
            return []
    
    async def activate_osmo_profile(self, profile_id: str, user_id: str) -> Dict[str, Any]:
        """Activate osmo-smdpp eSIM profile"""
        try:
            # Get profile from database
            response = get_supabase_client().table('osmo_esim_profiles').select('*').eq('id', profile_id).eq('user_id', user_id).execute()
            
            if not response.data:
                raise Exception("Profile not found or access denied")
            
            profile = response.data[0]
            
            # Update profile state to installed
            get_supabase_client().table('osmo_esim_profiles').update({
                'profile_state': 'installed',
                'installed_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', profile_id).execute()
            
            return {
                "success": True,
                "profile_id": profile_id,
                "activation_code": profile["activation_code"],
                "status": "installed",
                "message": "Private eSIM profile activated successfully"
            }
            
        except Exception as e:
            print(f"❌ OSMO ERROR: Failed to activate profile: {str(e)}")
            raise Exception(f"Failed to activate osmo profile: {str(e)}")
    
    def generate_osmo_qr_code(self, activation_code: str) -> str:
        """Generate QR code for osmo-smdpp activation"""
        import qrcode
        import io
        import base64
        
        # Create QR code with osmo-smdpp specific format
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(activation_code)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"