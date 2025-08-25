"""
eSIM service for provider integration
"""

import httpx
import qrcode
import io
import base64
from typing import Dict, Optional, Any
from datetime import datetime

from ..core.config import settings
from ..core.database import supabase_client
from ..models.enums import ESIMStatus


class ESIMService:
    """Service for eSIM operations and provider integration"""
    
    def __init__(self):
        # External provider credentials (optional - we have inbuilt eSIM generation)
        self.api_url = settings.ESIM_PROVIDER_API_URL
        self.api_key = settings.ESIM_PROVIDER_API_KEY
        self.username = settings.ESIM_PROVIDER_USERNAME
        self.password = settings.ESIM_PROVIDER_PASSWORD
        
        # Check if external provider is configured
        self.has_external_provider = all([
            self.api_url, self.api_key, self.username, self.password
        ])
    
    async def _make_api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to eSIM provider API"""
        # This is for external providers only - KSWiFi uses inbuilt eSIMs
        if not self.has_external_provider:
            raise Exception("External eSIM provider not configured - using inbuilt eSIM system")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.api_url}/{endpoint}",
                headers=headers,
                json=data,
                auth=(self.username, self.password) if self.username else None
            )
            response.raise_for_status()
            return response.json()
    
    async def provision_esim(self, user_id: str, bundle_size_mb: int) -> Dict[str, Any]:
        """Provision a new eSIM from the provider"""
        try:
            # Use inbuilt eSIM generation (default) or external provider
            if self.has_external_provider:
                # External provider
                provision_data = {
                    'bundle_size': bundle_size_mb,
                    'user_reference': user_id
                }
                
                provider_response = await self._make_api_request(
                    'POST', 
                    'esims/provision', 
                    provision_data
                )
                
                iccid = provider_response.get('iccid')
                imsi = provider_response.get('imsi') 
                msisdn = provider_response.get('msisdn')
                activation_code = provider_response.get('activation_code')
                apn = provider_response.get('apn', 'internet')
                username = provider_response.get('username')
                password = provider_response.get('password')
                
            else:
                # Inbuilt eSIM generation (no phone number, just internet access)
                import uuid
                import secrets
                
                iccid = f"8991{secrets.randbelow(10**15):015d}"
                imsi = f"999{secrets.randbelow(10**12):012d}" 
                msisdn = None  # No phone number for inbuilt eSIMs
                activation_code = f"LPA:1$sm-dp.kswifi.com${secrets.token_urlsafe(32)}"
                apn = "kswifi.internet"
                username = f"ks{secrets.randbelow(10**6):06d}"
                password = secrets.token_urlsafe(16)
            
            # Generate QR code for the eSIM
            qr_image = self._generate_qr_code(activation_code)
            
            # Store eSIM in Supabase
            esim_data = {
                'user_id': user_id,
                'iccid': iccid,
                'imsi': imsi,
                'msisdn': msisdn,
                'activation_code': activation_code,
                'qr_code_data': activation_code,
                'status': ESIMStatus.PENDING.value,
                'apn': apn,
                'username': username,
                'password': password,
                'bundle_size_mb': bundle_size_mb,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            response = supabase_client.client.table('esims').insert(esim_data).execute()
            esim_record = response.data[0] if response.data else None
            
            return {
                'esim_id': esim_record['id'],
                'iccid': esim_record['iccid'],
                'activation_code': esim_record['activation_code'],
                'qr_code_image': qr_image,
                'manual_setup': {
                    'sm_dp_address': provider_response.get('sm_dp_address'),
                    'activation_code': esim_record['activation_code'],
                    'apn': esim_record['apn'],
                    'username': esim_record['username'],
                    'password': esim_record['password']
                }
            }
            
        except Exception as e:
            raise Exception(f"Failed to provision eSIM: {str(e)}")
    
    async def activate_esim(self, esim_id: str) -> Dict[str, Any]:
        """Activate an eSIM (inbuilt or external provider)"""
        try:
            # Get eSIM details from database
            esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # For inbuilt eSIMs, just update status (no external API call needed)
            if not self.has_external_provider:
                # Update eSIM status in database
                supabase_client.client.table('esims').update({
                    'status': ESIMStatus.ACTIVE.value,
                    'activated_at': datetime.utcnow().isoformat()
                }).eq('id', esim_id).execute()
                
                return {
                    'status': 'activated',
                    'activated_at': datetime.utcnow().isoformat(),
                    'message': 'Inbuilt eSIM activated successfully',
                    'activation_code': esim['activation_code'],
                    'apn': esim['apn']
                }
            else:
                # External provider activation
                activation_data = {
                    'iccid': esim['iccid'],
                    'activation_code': esim['activation_code']
                }
                
                provider_response = await self._make_api_request(
                    'POST',
                    f"esims/{esim['iccid']}/activate",
                    activation_data
                )
                
                # Update eSIM status in database
                supabase_client.client.table('esims').update({
                    'status': ESIMStatus.ACTIVE.value,
                    'activated_at': datetime.utcnow().isoformat()
                }).eq('id', esim_id).execute()
                
                return {
                    'status': 'activated',
                    'activated_at': datetime.utcnow().isoformat(),
                    'provider_response': provider_response
                }
            
        except Exception as e:
            raise Exception(f"Failed to activate eSIM: {str(e)}")
    
    async def suspend_esim(self, esim_id: str) -> Dict[str, Any]:
        """Suspend an eSIM with the provider"""
        try:
            # Get eSIM details
            esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # Call provider API to suspend
            provider_response = await self._make_api_request(
                'POST',
                f"esims/{esim['iccid']}/suspend"
            )
            
            # Update status in database
            await supabase_client.update_esim_status(esim_id, ESIMStatus.SUSPENDED.value)
            
            return {
                'status': 'suspended',
                'provider_response': provider_response
            }
            
        except Exception as e:
            raise Exception(f"Failed to suspend eSIM: {str(e)}")
    
    async def get_esim_usage(self, esim_id: str) -> Dict[str, Any]:
        """Get current data usage from eSIM (inbuilt or external provider)"""
        try:
            # Get eSIM details
            esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            if not self.has_external_provider:
                # For inbuilt eSIMs, get usage from our database/monitoring
                # Check for session usage records
                usage_response = supabase_client.client.table('data_usage')\
                    .select('*')\
                    .eq('esim_id', esim_id)\
                    .order('created_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                if usage_response.data:
                    latest_usage = usage_response.data[0]
                    data_used_mb = latest_usage.get('data_used_mb', 0)
                    last_updated = latest_usage.get('created_at')
                else:
                    data_used_mb = 0
                    last_updated = datetime.utcnow().isoformat()
                
                return {
                    'iccid': esim['iccid'],
                    'data_used_mb': data_used_mb,
                    'data_remaining_mb': esim.get('bundle_size_mb', 0) - data_used_mb,
                    'last_updated': last_updated,
                    'status': esim['status'],
                    'is_inbuilt': True
                }
            else:
                # Get usage from external provider
                usage_response = await self._make_api_request(
                    'GET',
                    f"esims/{esim['iccid']}/usage"
                )
                
                return {
                    'iccid': esim['iccid'],
                    'data_used_mb': usage_response.get('data_used_mb', 0),
                    'last_updated': usage_response.get('last_updated'),
                    'session_duration': usage_response.get('session_duration'),
                    'location': usage_response.get('location'),
                    'is_inbuilt': False
                }
            
        except Exception as e:
            raise Exception(f"Failed to get eSIM usage: {str(e)}")
    
    def _generate_qr_code(self, data: str) -> str:
        """Generate QR code image as base64 string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"