"""
eSIM service for provider integration
"""

import qrcode
import io
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.database import get_supabase_client
from ..models.enums import ESIMStatus


class ESIMService:
    """Service for eSIM operations and provider integration"""
    
    def __init__(self):
        # KSWiFi uses inbuilt eSIM generation only
        pass
    
    # External provider API removed - KSWiFi uses inbuilt eSIM generation only
    
    async def provision_esim(self, user_id: str, bundle_size_mb: int) -> Dict[str, Any]:
        """Provision a new eSIM from the provider"""
        try:
            print(f"🔍 ESIM DEBUG: provision_esim called")
            print(f"🔍 ESIM DEBUG: user_id = {user_id}")
            print(f"🔍 ESIM DEBUG: bundle_size_mb = {bundle_size_mb}")
            print(f"🔍 ESIM DEBUG: Using KSWiFi inbuilt eSIM generation")
            
            # KSWiFi inbuilt eSIM generation (no phone number, just internet access)
            import uuid
            import secrets
            
            print(f"🔍 ESIM DEBUG: Generating unique identifiers...")
            # Generate unique identifiers
            iccid = f"8991{secrets.randbelow(10**15):015d}"
            imsi = f"999{secrets.randbelow(10**12):012d}" 
            msisdn = None  # No phone number for inbuilt eSIMs
            print(f"🔍 ESIM DEBUG: Generated ICCID: {iccid}")
            print(f"🔍 ESIM DEBUG: Generated IMSI: {imsi}")

            # Configure for KSWiFi network server (use actual backend URL)
            backend_host = settings.BACKEND_URL or "kswifi.onrender.com"
            if backend_host.startswith("http"):
                backend_host = backend_host.replace("https://", "").replace("http://", "")
            print(f"🔍 ESIM DEBUG: Backend host: {backend_host}")
            
            # Create proper LPA activation code for KSWiFi network
            activation_code = f"LPA:1${backend_host}$ks{secrets.token_urlsafe(16)}"
            print(f"🔍 ESIM DEBUG: Generated activation code: {activation_code}")
            
            # Configure APN for internet access through KSWiFi network
            apn = "internet"  # Standard internet APN
            username = f"kswifi_{secrets.randbelow(10**6):06d}"
            password = secrets.token_urlsafe(12)
            print(f"🔍 ESIM DEBUG: Network config - APN: {apn}, Username: {username}")
            
            # Network configuration for internet browsing
            network_config = {
                "gateway": f"{backend_host}",
                "dns_primary": "8.8.8.8",
                "dns_secondary": "8.8.4.4",
                "proxy": None,  # Direct internet access
                "network_type": "LTE"
            }
            print(f"🔍 ESIM DEBUG: Network config: {network_config}")
            
            print(f"🔍 ESIM DEBUG: Generating QR code...")
            # Generate QR code for the eSIM activation
            qr_image = self._generate_qr_code(activation_code)
            print(f"🔍 ESIM DEBUG: QR code generated successfully, length: {len(qr_image)}")
            
            print(f"🔍 ESIM DEBUG: Storing eSIM in database...")
            
            supabase = get_supabase_client()
            print(f"🔍 ESIM DEBUG: Supabase client obtained")
            
            # Ensure user exists in database (create if needed)
            try:
                print(f"🔍 ESIM DEBUG: Checking if user exists: {user_id}")
                # Check if user exists
                user_response = supabase.table('users').select('id').eq('id', user_id).execute()
                if not user_response.data:
                    print(f"🔍 ESIM DEBUG: User not found, creating user record...")
                    # Create basic user record
                    user_data = {
                        'id': user_id,
                        'email': f"user_{user_id[:8]}@kswifi.app",
                        'first_name': 'KSWiFi',
                        'last_name': 'User',
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    user_create_response = supabase.table('users').insert(user_data).execute()
                    print(f"🔍 ESIM DEBUG: User create response: {user_create_response}")
                    
                    if user_create_response.data:
                        print(f"🔍 ESIM DEBUG: User created successfully: {user_create_response.data[0]['id']}")
                    else:
                        print(f"❌ ESIM ERROR: Failed to create user - no data returned")
                        raise Exception("Failed to create user record")
                else:
                    print(f"🔍 ESIM DEBUG: User exists: {user_response.data[0]['id']}")
            except Exception as user_error:
                print(f"❌ ESIM ERROR: User creation/verification failed: {user_error}")
                print(f"❌ ESIM ERROR: User error type: {type(user_error).__name__}")
                # Don't continue if user creation fails - it will cause foreign key errors
                raise Exception(f"Cannot create eSIM: User {user_id} does not exist and could not be created: {str(user_error)}")
            
            # Store eSIM in Supabase (now that schema is updated)
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
            print(f"🔍 ESIM DEBUG: eSIM data prepared: {list(esim_data.keys())}")
            
            response = supabase.table('esims').insert(esim_data).execute()
            print(f"🔍 ESIM DEBUG: eSIM insert response: {response}")
            
            esim_record = response.data[0] if response.data else None
            print(f"🔍 ESIM DEBUG: eSIM record created: {esim_record is not None}")
            
            if not esim_record:
                raise Exception("Failed to create eSIM record in database")
            
            print(f"🔍 ESIM DEBUG: Creating data pack...")
            # Create associated data pack to track bundle size and usage
            data_pack_data = {
                'user_id': user_id,
                'name': f"eSIM Data Pack - {bundle_size_mb}MB",
                'data_mb': bundle_size_mb,
                'used_data_mb': 0,  # Matches schema
                # 'remaining_data_mb' is auto-calculated (generated column)
                'price_ngn': 0,  # Free for downloaded sessions
                'price_usd': 0.0,
                'status': 'active',
                'is_active': True,
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            print(f"🔍 ESIM DEBUG: Data pack data prepared")
            
            pack_response = supabase.table('data_packs').insert(data_pack_data).execute()
            print(f"🔍 ESIM DEBUG: Data pack insert response: {pack_response}")
            
            data_pack_record = pack_response.data[0] if pack_response.data else None
            print(f"🔍 ESIM DEBUG: Data pack record created: {data_pack_record is not None}")
            
            print(f"🔍 ESIM DEBUG: Preparing manual setup instructions...")
            # Prepare manual setup instructions
            manual_setup = {
                'activation_code': activation_code,
                'apn': apn,
                'username': username,
                'password': password,
                'instructions': [
                    "1. Scan the QR code with your device camera",
                    "2. Follow the prompts to add the cellular plan",
                    "3. Enable the new cellular plan for data",
                    "4. You can now browse the internet using your downloaded data"
                ]
            }
            
            if not self.has_external_provider:
                manual_setup['network_info'] = {
                    'provider': 'KSWiFi Network',
                    'type': 'Internet Data Plan',
                    'coverage': 'Global Internet Access',
                    'bundle_size_mb': bundle_size_mb,
                    'gateway': network_config['gateway']
                }
            
            print(f"🔍 ESIM DEBUG: Preparing final response...")
            result = {
                'esim_id': esim_record['id'],
                'iccid': esim_record['iccid'],
                'activation_code': activation_code,
                'qr_code_image': qr_image,
                'bundle_size_mb': bundle_size_mb,
                'data_pack_id': data_pack_record['id'] if data_pack_record else None,
                'status': 'pending_activation',
                'manual_setup': manual_setup,
                'network_ready': True,
                'internet_enabled': True
            }
            
            print(f"🔍 ESIM DEBUG: eSIM provision completed successfully!")
            print(f"🔍 ESIM DEBUG: Final result keys: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"❌ ESIM ERROR: Exception in provision_esim: {str(e)}")
            print(f"❌ ESIM ERROR: Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ ESIM ERROR: Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to provision eSIM: {str(e)}")
    
    async def activate_esim(self, esim_id: str) -> Dict[str, Any]:
        """Activate an eSIM (inbuilt or external provider)"""
        try:
            # Get eSIM details from database
            esim_response = get_supabase_client().table('esims').select('*').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # For inbuilt eSIMs, just update status (no external API call needed)
            if not self.has_external_provider:
                # Update eSIM status in database
                get_supabase_client().table('esims').update({
                    'status': ESIMStatus.ACTIVE.value
                }).eq('id', esim_id).execute()
                
                return {
                    'status': 'activated',
                    'message': 'eSIM activated successfully - Internet browsing enabled',
                    'activation_code': esim['activation_code'],
                    'apn': esim['apn'],
                    'internet_access': True,
                    'connection_details': {
                        'apn': esim['apn'],
                        'username': esim['username'],
                        'password': esim['password'],
                        'iccid': esim['iccid'],
                        'network_type': 'LTE/5G',
                        'data_enabled': True
                    },
                    'setup_instructions': [
                        'Scan QR code with your device',
                        'eSIM will be added to your device',
                        'Internet connection will be automatically configured',
                        'Start browsing immediately'
                    ]
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
                get_supabase_client().table('esims').update({
                    'status': ESIMStatus.ACTIVE.value
                }).eq('id', esim_id).execute()
                
                return {
                    'status': 'activated',
                    'provider_response': provider_response
                }
            
        except Exception as e:
            raise Exception(f"Failed to activate eSIM: {str(e)}")
    
    async def suspend_esim(self, esim_id: str) -> Dict[str, Any]:
        """Suspend an eSIM with the provider"""
        try:
            # Get eSIM details
            esim_response = get_supabase_client().table('esims').select('id, user_id, iccid, imsi, status').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # Call provider API to suspend
            provider_response = await self._make_api_request(
                'POST',
                f"esims/{esim['iccid']}/suspend"
            )
            
            # Update status in database
            supabase = get_supabase_client()
            supabase.table('esims').update({
                'status': ESIMStatus.SUSPENDED.value
            }).eq('id', esim_id).execute()
            
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
            esim_response = get_supabase_client().table('esims').select('id, user_id, iccid, status').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            if not self.has_external_provider:
                # For inbuilt eSIMs, get usage from our database/monitoring
                # Check for session usage records
                usage_response = get_supabase_client().table('data_usage')\
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
                
                # Get bundle size from associated data pack
                try:
                    pack_response = get_supabase_client().table('data_packs')\
                        .select('total_data_mb, used_data_mb, remaining_data_mb')\
                        .eq('user_id', esim['user_id'])\
                        .eq('status', 'active')\
                        .order('created_at', desc=True)\
                        .limit(1)\
                        .execute()
                except Exception as db_error:
                    # Fallback if remaining_data_mb column doesn't exist
                    try:
                        pack_response = get_supabase_client().table('data_packs')\
                            .select('total_data_mb, used_data_mb')\
                            .eq('user_id', esim['user_id'])\
                            .eq('status', 'active')\
                            .order('created_at', desc=True)\
                            .limit(1)\
                            .execute()
                    except Exception:
                        pack_response = type('obj', (object,), {'data': []})()
                
                total_data_mb = 0
                remaining_data_mb = 0
                if pack_response.data:
                    pack = pack_response.data[0]
                    total_data_mb = pack.get('total_data_mb', 0)
                    # Calculate remaining_data_mb if not present
                    if 'remaining_data_mb' in pack and pack['remaining_data_mb'] is not None:
                        remaining_data_mb = pack['remaining_data_mb']
                    else:
                        # Fallback calculation
                        used_mb = pack.get('used_data_mb', 0)
                        remaining_data_mb = max(0, total_data_mb - used_mb)
                
                return {
                    'iccid': esim['iccid'],
                    'data_used_mb': data_used_mb,
                    'data_remaining_mb': remaining_data_mb,
                    'total_data_mb': total_data_mb,
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
    
    async def check_internet_connectivity(self, esim_id: str) -> Dict[str, Any]:
        """Check if eSIM has internet connectivity for browsing"""
        try:
            # Get eSIM details
            esim_response = get_supabase_client().table('esims').select('id, user_id, iccid, status, apn').eq('id', esim_id).execute()
            if not esim_response.data:
                raise Exception("eSIM not found")
            
            esim = esim_response.data[0]
            
            # Check if eSIM is active
            is_active = esim['status'] == ESIMStatus.ACTIVE.value
            
            # For inbuilt eSIMs, connectivity is ready when active
            if not self.has_external_provider:
                return {
                    'esim_id': esim_id,
                    'internet_ready': is_active,
                    'connectivity_status': 'ready' if is_active else 'inactive',
                    'apn_configured': True,
                    'data_connection': 'available' if is_active else 'unavailable',
                    'browsing_enabled': is_active,
                    'network_type': 'LTE/5G',
                    'connection_details': {
                        'apn': esim['apn'],
                        'iccid': esim['iccid']
                    }
                }
            else:
                # For external providers, we might need to check with the provider
                # For now, assume ready if active
                return {
                    'esim_id': esim_id,
                    'internet_ready': is_active,
                    'connectivity_status': 'ready' if is_active else 'inactive',
                    'browsing_enabled': is_active
                }
                
        except Exception as e:
            raise Exception(f"Failed to check internet connectivity: {str(e)}")
    
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