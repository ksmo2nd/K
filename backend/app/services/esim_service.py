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
        self.api_url = settings.ESIM_PROVIDER_API_URL
        self.api_key = settings.ESIM_PROVIDER_API_KEY
        self.username = settings.ESIM_PROVIDER_USERNAME
        self.password = settings.ESIM_PROVIDER_PASSWORD
    
    async def _make_api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to eSIM provider API"""
        # Check if we have real credentials
        if not self.api_key or not self.api_url or self.api_url == "https://api.example-provider.com":
            # Return mock data for development
            return self._get_mock_response(endpoint, method, data)
        
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
    
    def _get_mock_response(self, endpoint: str, method: str, data: Dict = None) -> Dict:
        """Generate mock responses for development"""
        import uuid
        from datetime import datetime
        
        if endpoint == 'esims/provision':
            return {
                'iccid': f"89014{uuid.uuid4().hex[:15]}",
                'imsi': f"901{uuid.uuid4().hex[:12]}",
                'msisdn': f"+234{uuid.uuid4().hex[:10]}",
                'activation_code': f"LPA:1$api.example.com${uuid.uuid4().hex[:16]}",
                'sm_dp_address': 'api.example.com',
                'apn': 'internet',
                'username': 'kswifi',
                'password': 'kswifi123',
                'status': 'provisioned'
            }
        elif endpoint.startswith('esims/') and endpoint.endswith('/activate'):
            return {
                'status': 'active',
                'activated_at': datetime.utcnow().isoformat(),
                'message': 'eSIM activated successfully'
            }
        elif endpoint.startswith('esims/') and endpoint.endswith('/status'):
            return {
                'status': 'active',
                'data_used_mb': 0,
                'data_remaining_mb': data.get('bundle_size_mb', 1024) if data else 1024,
                'last_updated': datetime.utcnow().isoformat()
            }
        elif endpoint.startswith('esims/') and endpoint.endswith('/deactivate'):
            return {
                'status': 'inactive',
                'deactivated_at': datetime.utcnow().isoformat(),
                'message': 'eSIM deactivated successfully'
            }
        else:
            return {'status': 'success', 'message': 'Mock response'}
    
    async def provision_esim(self, user_id: str, bundle_size_mb: int) -> Dict[str, Any]:
        """Provision a new eSIM from the provider"""
        try:
            # Call eSIM provider API to provision new eSIM
            provision_data = {
                'bundle_size': bundle_size_mb,
                'user_reference': user_id
            }
            
            provider_response = await self._make_api_request(
                'POST', 
                'esims/provision', 
                provision_data
            )
            
            # Generate QR code for the eSIM
            qr_code_data = provider_response.get('activation_code', '')
            qr_image = self._generate_qr_code(qr_code_data)
            
            # Store eSIM in Supabase
            esim_data = {
                'user_id': user_id,
                'iccid': provider_response.get('iccid'),
                'imsi': provider_response.get('imsi'),
                'msisdn': provider_response.get('msisdn'),
                'activation_code': provider_response.get('activation_code'),
                'qr_code_data': qr_code_data,
                'status': ESIMStatus.PENDING.value,
                'apn': provider_response.get('apn', 'internet'),
                'username': provider_response.get('username'),
                'password': provider_response.get('password'),
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
        """Activate an eSIM with the provider"""
        try:
            # Get eSIM details from database
            esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # Call provider API to activate
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
            await supabase_client.update_esim_status(
                esim_id, 
                ESIMStatus.ACTIVE.value,
                activated_at=datetime.utcnow().isoformat()
            )
            
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
        """Get current data usage from eSIM provider"""
        try:
            # Get eSIM details
            esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # Get usage from provider
            usage_response = await self._make_api_request(
                'GET',
                f"esims/{esim['iccid']}/usage"
            )
            
            return {
                'iccid': esim['iccid'],
                'data_used_mb': usage_response.get('data_used_mb', 0),
                'last_updated': usage_response.get('last_updated'),
                'session_duration': usage_response.get('session_duration'),
                'location': usage_response.get('location')
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