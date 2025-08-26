"""
Internet Session Download Service - Core KSWiFi functionality
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.config import settings
from ..core.database import get_supabase_client
from ..models.enums import ESIMStatus, DataPackStatus
from .esim_service import ESIMService


class SessionStatus(str, Enum):
    """Internet session status"""
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    TRANSFERRING = "transferring"
    STORED = "stored"
    ACTIVATING = "activating"
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    FAILED = "failed"


class SessionService:
    """Service for downloading and managing internet sessions"""
    
    def __init__(self):
        self.esim_service = ESIMService()
        self.pricing = settings.BUNDLE_PRICING
    

    
    async def get_available_sessions(self, wifi_network: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available session download options from connected WiFi network"""
        
        print(f"🔍 SESSION DEBUG: get_available_sessions called")
        print(f"🔍 SESSION DEBUG: wifi_network = {wifi_network}")
        print(f"🔍 SESSION DEBUG: user_id = {user_id}")
        
        # Always return sessions - don't require WiFi network for testing
        sessions = []
        
        try:
            print(f"🔍 SESSION DEBUG: Starting session detection...")
            
            # Get sessions from connected WiFi network (if provided)
            supabase = get_supabase_client()
            print(f"🔍 SESSION DEBUG: Supabase client initialized")
            
            if wifi_network:
                print(f"🔍 SESSION DEBUG: Checking database for WiFi network: {wifi_network}")
                # Query for sessions available on this WiFi network
                wifi_sessions_response = supabase.table('internet_sessions').select('*').eq('source_network', wifi_network).eq('status', 'available').execute()
                print(f"🔍 SESSION DEBUG: Database query result: {wifi_sessions_response.data}")
                
                if wifi_sessions_response.data:
                    print(f"🔍 SESSION DEBUG: Found {len(wifi_sessions_response.data)} sessions in database")
                    # Convert database sessions to API format
                    for session_data in wifi_sessions_response.data:
                        session = {
                            'id': session_data['id'],
                            'name': f"{session_data['data_mb'] // 1024}GB",
                            'size': f"{session_data['data_mb'] // 1024}GB",
                            'data_mb': session_data['data_mb'],
                            'price_ngn': session_data.get('price_ngn', 0),
                            'price_usd': session_data.get('price_usd', 0.0),
                            'validity_days': session_data.get('validity_days'),
                            'plan_type': session_data.get('plan_type', 'standard'),
                            'is_unlimited': session_data['data_mb'] == -1,
                            'is_free': session_data.get('price_ngn', 0) == 0,
                            'description': f"Download {session_data['data_mb'] // 1024}GB from {wifi_network}",
                            'features': [
                                f"{session_data['data_mb'] // 1024}GB internet session",
                                f"Available from {wifi_network}",
                                "Download to eSIM for offline use",
                                "No expiry - only when data exhausted"
                            ],
                            'source_network': wifi_network,
                            'network_quality': session_data.get('network_quality', 'good')
                        }
                        sessions.append(session)
                        print(f"🔍 SESSION DEBUG: Added database session: {session['name']}")
                else:
                    print(f"🔍 SESSION DEBUG: No sessions found in database, scanning WiFi network...")
                    # If no sessions found in database, scan the WiFi network for available sessions
                    detected_sessions = await self._scan_wifi_for_sessions(wifi_network)
                    sessions.extend(detected_sessions)
                    print(f"🔍 SESSION DEBUG: Added {len(detected_sessions)} scanned sessions")
            else:
                print(f"🔍 SESSION DEBUG: No WiFi network provided, generating default sessions...")
                # Generate default sessions when no WiFi network is specified
                default_sessions = await self._generate_default_sessions()
                sessions.extend(default_sessions)
                print(f"🔍 SESSION DEBUG: Added {len(default_sessions)} default sessions")
            
            # Always add fallback session to ensure something is returned
            if not sessions:
                print(f"🔍 SESSION DEBUG: No sessions found, adding fallback...")
                fallback_sessions = await self._get_fallback_sessions(wifi_network or "Unknown")
                sessions.extend(fallback_sessions)
                print(f"🔍 SESSION DEBUG: Added {len(fallback_sessions)} fallback sessions")
            
            # Sort by data size
            sessions.sort(key=lambda x: x['data_mb'] if x['data_mb'] != -1 else float('inf'))
            
            print(f"🔍 SESSION DEBUG: Final sessions count: {len(sessions)}")
            for session in sessions:
                print(f"🔍 SESSION DEBUG: - {session['name']}: {session['data_mb']}MB, ${session['price_ngn']} NGN")
            
            return sessions
            
        except Exception as e:
            print(f"❌ SESSION ERROR: Exception in get_available_sessions: {str(e)}")
            print(f"❌ SESSION ERROR: Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ SESSION ERROR: Traceback: {traceback.format_exc()}")
            
            # Always return fallback sessions even on error
            print(f"🔍 SESSION DEBUG: Returning fallback sessions due to error...")
            fallback_sessions = await self._get_fallback_sessions(wifi_network or "Unknown")
            print(f"🔍 SESSION DEBUG: Fallback sessions: {len(fallback_sessions)}")
            return fallback_sessions
    
    async def _generate_default_sessions(self) -> List[Dict[str, Any]]:
        """Generate default session options when no WiFi network is specified"""
        print(f"🔍 SESSION DEBUG: Generating default sessions...")
        
        sessions = []
        default_sizes = [1, 2, 3, 5, 10, 20, 50]  # GB
        
        for size_gb in default_sizes:
            is_free = size_gb <= 5
            session = {
                'id': str(uuid.uuid4()),
                'session_name': f'default_{size_gb}gb',
                'name': f'{size_gb}GB',
                'size': f'{size_gb}GB',
                'data_mb': size_gb * 1024,
                'price_ngn': 0 if is_free else 800,
                'price_usd': 0.0 if is_free else 1.92,
                'validity_days': None,
                'plan_type': 'default' if is_free else 'unlimited_required',
                'is_unlimited': False,
                'is_free': is_free,
                'description': f'Download {size_gb}GB internet session' + (' - Free' if is_free else ' - Requires unlimited access'),
                'features': [
                    f'{size_gb}GB internet session',
                    'Works with any WiFi connection',
                    'Download to eSIM for offline use',
                    'No time expiry - only when data exhausted'
                ] + (['Free up to 5GB'] if is_free else ['Requires ₦800 unlimited access']),
                'source_network': 'Any WiFi',
                'network_quality': 'good'
            }
            sessions.append(session)
            print(f"🔍 SESSION DEBUG: Generated default session: {session['name']}")
        
        return sessions

    async def _scan_wifi_for_sessions(self, wifi_network: str) -> List[Dict[str, Any]]:
        """Scan the connected WiFi network for available internet sessions"""
        print(f"🔍 SESSION DEBUG: _scan_wifi_for_sessions called for: {wifi_network}")
        sessions = []
        
        try:
            # In a real implementation, this would:
            # 1. Connect to the WiFi router's admin interface
            # 2. Check for available bandwidth/data packages
            # 3. Query the network for downloadable sessions
            # 4. Detect what data amounts are available for download
            
            # For now, we'll create standard session sizes based on network capacity
            # This simulates detecting what's available on the connected WiFi
            
            # Simulate network capacity detection
            network_capacity_gb = await self._detect_network_capacity(wifi_network)
            print(f"🔍 SESSION DEBUG: Detected network capacity: {network_capacity_gb}GB")
            
            # Generate available sessions based on network capacity
            available_sizes = []
            if network_capacity_gb >= 100:
                available_sizes = [1, 2, 3, 5, 10, 20, 50, 100]
            elif network_capacity_gb >= 50:
                available_sizes = [1, 2, 3, 5, 10, 20]
            elif network_capacity_gb >= 10:
                available_sizes = [1, 2, 3, 5]
            else:
                available_sizes = [1, 2]
            
            print(f"🔍 SESSION DEBUG: Available sizes for {wifi_network}: {available_sizes}")
            
            for size_gb in available_sizes:
                session = {
                    'id': str(uuid.uuid4()),
                    'session_name': f'wifi_{wifi_network}_{size_gb}gb',
                    'name': f'{size_gb}GB',
                    'size': f'{size_gb}GB',
                    'data_mb': size_gb * 1024,
                    'price_ngn': 0 if size_gb <= 5 else 800,  # Free up to 5GB
                    'price_usd': 0.0 if size_gb <= 5 else 1.92,
                    'validity_days': None,
                    'plan_type': 'wifi_download' if size_gb <= 5 else 'unlimited_required',
                    'is_unlimited': False,
                    'is_free': size_gb <= 5,
                    'description': f'Download {size_gb}GB from connected WiFi network "{wifi_network}"',
                    'features': [
                        f'{size_gb}GB internet session',
                        f'Available from {wifi_network}',
                        'Download while connected to WiFi',
                        'Transfer to eSIM for offline use',
                        'No time expiry - only when data exhausted'
                    ],
                    'source_network': wifi_network,
                    'network_quality': 'good'
                }
                sessions.append(session)
                print(f"🔍 SESSION DEBUG: Generated WiFi session: {session['name']} from {wifi_network}")
                
                # Store detected session in database for future reference
                await self._store_detected_session(session)
            
            return sessions
            
        except Exception as e:
            print(f"❌ SESSION ERROR: Error scanning WiFi network {wifi_network}: {e}")
            import traceback
            print(f"❌ SESSION ERROR: Traceback: {traceback.format_exc()}")
            return []
    
    async def _detect_network_capacity(self, wifi_network: str) -> int:
        """Detect the capacity/bandwidth available on the WiFi network"""
        try:
            # In a real implementation, this would:
            # 1. Perform speed tests
            # 2. Check router capacity
            # 3. Analyze network traffic
            # 4. Determine available bandwidth for session downloads
            
            # For now, simulate based on network name patterns
            network_lower = wifi_network.lower()
            
            if any(keyword in network_lower for keyword in ['fiber', 'gigabit', '5g', 'enterprise']):
                return 100  # High capacity networks
            elif any(keyword in network_lower for keyword in ['broadband', 'cable', '4g']):
                return 50   # Medium capacity networks
            elif any(keyword in network_lower for keyword in ['mobile', '3g', 'hotspot']):
                return 10   # Lower capacity networks
            else:
                return 20   # Default capacity
                
        except Exception as e:
            print(f"❌ Error detecting network capacity: {e}")
            return 5  # Conservative default
    
    async def _store_detected_session(self, session: Dict[str, Any]) -> None:
        """Store detected session in database for future reference"""
        try:
            supabase = get_supabase_client()
            
            session_data = {
                'id': session['id'],
                'session_id': session['session_name'],  # Use session_name for session_id field
                'session_name': session['name'],  # Use name for session_name field
                'data_mb': session['data_mb'],
                'price_ngn': session['price_ngn'],
                'price_usd': session['price_usd'],
                'source_network': session['source_network'],
                'network_quality': session['network_quality'],
                'plan_type': session['plan_type'],
                'status': 'available',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Insert or update session
            supabase.table('internet_sessions').upsert(session_data).execute()
            
        except Exception as e:
            print(f"❌ Error storing detected session: {e}")
    
    async def _get_fallback_sessions(self, wifi_network: str) -> List[Dict[str, Any]]:
        """Get fallback sessions when WiFi scanning fails"""
        return [
            {
                'id': str(uuid.uuid4()),
                'session_name': f'fallback_1gb',
                'name': '1GB',
                'size': '1GB',
                'data_mb': 1024,
                'price_ngn': 0,
                'price_usd': 0.0,
                'validity_days': None,
                'plan_type': 'wifi_download',
                'is_unlimited': False,
                'is_free': True,
                'description': f'Basic 1GB session from {wifi_network}',
                'features': ['1GB internet session', 'Basic connectivity', 'No expiry'],
                'source_network': wifi_network,
                'network_quality': 'unknown'
            }
        ]
    
    def _get_session_description(self, name: str, details: Dict) -> str:
        """Get user-friendly session description"""
        if details['data_mb'] == -1:
            return "Download up to 100GB sessions - no expiry, only when exhausted"
        else:
            size_gb = details['data_mb'] / 1024
            if size_gb >= 1:
                return f"Download {size_gb:.0f}GB internet session - no expiry, only when exhausted"
            else:
                return f"Download {details['data_mb']}MB internet session - no expiry, only when exhausted"
    
    def _get_session_features(self, details: Dict) -> List[str]:
        """Get session features list"""
        features = []
        
        if details['data_mb'] == -1:
            features.append("Download up to 100GB sessions")
            features.append("No size limits per download")
        else:
            size_gb = details['data_mb'] / 1024
            features.append(f"{size_gb:.0f}GB internet session")
            features.append("Full browsing capability")
        
        features.append("No expiry - only when exhausted")
        features.append("Download from connected WiFi")
        features.append("Works offline via eSIM")
        features.append("Activate with QR code")
        
        return features
    
    async def start_session_download(
        self, 
        user_id: str, 
        session_id: str,
        esim_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start downloading an internet session from connected WiFi"""
        try:
            # Parse session details
            session_details = await self._get_session_details(session_id, user_id)
            
            # Check quota and permissions
            await self._check_download_permissions(user_id, session_details)
            
            # Create session record
            session_data = {
                'user_id': user_id,
                'session_id': session_id,
                'session_name': session_details['name'],
                'data_mb': session_details['data_mb'],
                'data_used_mb': 0,  # Start with zero usage
                'price_ngn': session_details.get('price_ngn', 0),
                'plan_type': session_details.get('plan_type', 'standard'),
                'status': SessionStatus.DOWNLOADING.value,
                'download_started_at': datetime.utcnow().isoformat(),
                'progress_percent': 0,
                'esim_id': esim_id,
                'expires_at': None  # No expiry date
            }
            
            response = get_supabase_client().table('internet_sessions').insert(session_data).execute()
            session_record = response.data[0] if response.data else None
            
            # Start background download process from WiFi
            asyncio.create_task(self._download_session_from_wifi(session_record['id']))
            
            return {
                'session_id': session_record['id'],
                'status': SessionStatus.DOWNLOADING.value,
                'message': f'Downloading {session_details["name"]} from connected WiFi',
                'estimated_time_minutes': self._estimate_download_time(session_details['data_mb']),
                'no_expiry': True,
                'expires_when': 'data_exhausted'
            }
            
        except Exception as e:
            raise Exception(f"Failed to start session download: {str(e)}")
    
    async def _get_session_details(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get session details from predefined or custom sizes"""
        print(f"🔍 SESSION DEBUG: Getting details for session_id: {session_id}")
        
        # Handle default session IDs (default_1gb, default_2gb, etc.)
        if session_id.startswith('default_'):
            size_part = session_id.replace('default_', '')
            if size_part.endswith('gb'):
                size_str = size_part.replace('gb', '')
                try:
                    size_gb = int(size_str)
                    print(f"🔍 SESSION DEBUG: Found default session: {size_gb}GB")
                    return {
                        'name': f'{size_gb}GB',
                        'data_mb': size_gb * 1024,
                        'price_ngn': 0 if size_gb <= 5 else 800,
                        'price_usd': 0.0 if size_gb <= 5 else 1.92,
                        'plan_type': 'default' if size_gb <= 5 else 'unlimited_required'
                    }
                except ValueError:
                    pass
        
        # Handle WiFi session IDs (wifi_NetworkName_2gb, etc.)
        if session_id.startswith('wifi_'):
            # Extract size from WiFi session ID: wifi_NetworkName_2gb -> 2gb
            parts = session_id.split('_')
            if len(parts) >= 3 and parts[-1].endswith('gb'):
                size_part = parts[-1]  # Get the last part (e.g., "2gb")
                size_str = size_part.replace('gb', '')
                try:
                    size_gb = int(size_str)
                    print(f"🔍 SESSION DEBUG: Found WiFi session: {size_gb}GB")
                    return {
                        'name': f'{size_gb}GB',
                        'data_mb': size_gb * 1024,
                        'price_ngn': 0 if size_gb <= 5 else 800,
                        'price_usd': 0.0 if size_gb <= 5 else 1.92,
                        'plan_type': 'wifi_download' if size_gb <= 5 else 'unlimited_required'
                    }
                except ValueError:
                    pass
        
        # Check predefined sessions in pricing
        for name, details in self.pricing.items():
            if name.lower().replace(' ', '_') == session_id:
                print(f"🔍 SESSION DEBUG: Found pricing session: {name}")
                return {
                    'name': name,
                    'data_mb': details['data_mb'],
                    'price_ngn': details.get('price_ngn', 0),
                    'plan_type': details.get('plan_type', 'standard')
                }
        
        # Check custom GB sizes (6gb-100gb)
        if session_id.endswith('gb'):
            size_str = session_id.replace('gb', '')
            try:
                size_gb = int(size_str)
                if 6 <= size_gb <= 100:
                    print(f"🔍 SESSION DEBUG: Found custom session: {size_gb}GB")
                    return {
                        'name': f'{size_gb}GB',
                        'data_mb': size_gb * 1024,
                        'price_ngn': 0,
                        'plan_type': 'unlimited_required'
                    }
            except ValueError:
                pass
        
        print(f"❌ SESSION ERROR: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")
    
    async def _check_download_permissions(self, user_id: str, session_details: Dict) -> None:
        """Check if user can download this session"""
        plan_type = session_details.get('plan_type', 'standard')
        
        if plan_type == 'free':
            # Check free quota (up to 5GB total)
            await self._check_free_quota(user_id)
            
        elif plan_type == 'unlimited_required':
            # Check if user has unlimited access (₦800 payment)
            await self._check_unlimited_access(user_id)
    
    async def _check_unlimited_access(self, user_id: str) -> None:
        """Check if user has paid for unlimited access"""
        # Check for unlimited subscription
        response = get_supabase_client().table('user_subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('subscription_type', 'unlimited')\
            .eq('status', 'active')\
            .execute()
        
        if not response.data:
            raise Exception("Unlimited access required. Pay ₦800 to download sessions above 5GB")
    
    async def _check_free_quota(self, user_id: str) -> None:
        """Check if user has exceeded free session quota"""
        # Get user's free sessions this month
        current_month = datetime.utcnow().replace(day=1)
        
        response = get_supabase_client().table('internet_sessions')\
            .select('data_mb')\
            .eq('user_id', user_id)\
            .eq('price_ngn', 0)\
            .gte('download_started_at', current_month.isoformat())\
            .execute()
        
        total_free_mb = sum(session['data_mb'] for session in response.data if session['data_mb'] > 0)
        free_limit_mb = 5 * 1024  # 5GB limit
        
        if total_free_mb >= free_limit_mb:
            raise Exception("Free quota exceeded. Upgrade to unlimited for ₦800/week")
    
    def _estimate_download_time(self, data_mb: int) -> int:
        """Estimate download time in minutes"""
        if data_mb == -1:  # Unlimited
            return 2  # Quick setup for unlimited
        
        # Estimate based on typical WiFi speeds (10-50 Mbps)
        # Conservative estimate: 5 Mbps = 0.625 MB/s
        estimated_seconds = data_mb / 0.625  # MB per second
        return max(1, int(estimated_seconds / 60))  # Convert to minutes, minimum 1
    
    async def _download_session_from_wifi(self, session_record_id: str) -> None:
        """Background process to download session from connected WiFi with chunked processing"""
        try:
            # Get session record
            response = get_supabase_client().table('internet_sessions')\
                .select('*')\
                .eq('id', session_record_id)\
                .single()\
                .execute()
            
            session = response.data
            data_mb = session['data_mb']
            
            # Check WiFi connection
            await self._verify_wifi_connection()
            
            print(f"🔄 DOWNLOAD: Starting chunked download for {data_mb}MB session")
            
            # Use chunked download approach
            if data_mb == -1:  # Unlimited sessions
                await self._download_unlimited_session(session_record_id)
            else:
                await self._download_chunked_session(session_record_id, data_mb)
            
        except Exception as e:
            print(f"❌ DOWNLOAD ERROR: {str(e)}")
            await self._update_session_status(session_record_id, SessionStatus.FAILED, str(e))
    
    async def _download_chunked_session(self, session_record_id: str, total_mb: int) -> None:
        """Download session in chunks (50-100MB each) with realistic progress"""
        print(f"🔄 CHUNKED DOWNLOAD: Processing {total_mb}MB in chunks")
        
        # Define chunk size (50-100MB per chunk)
        chunk_size_mb = min(100, max(50, total_mb // 10))  # Adaptive chunk size
        total_chunks = max(1, total_mb // chunk_size_mb)
        
        print(f"🔄 CHUNKED DOWNLOAD: {total_chunks} chunks of {chunk_size_mb}MB each")
        
        downloaded_mb = 0
        
        for chunk_num in range(total_chunks):
            # Calculate chunk progress
            current_chunk_mb = min(chunk_size_mb, total_mb - downloaded_mb)
            progress_percent = int((downloaded_mb / total_mb) * 100)
            
            print(f"🔄 CHUNK {chunk_num + 1}/{total_chunks}: Downloading {current_chunk_mb}MB (Progress: {progress_percent}%)")
            
            # Update progress before processing chunk
            await self._update_session_progress(session_record_id, progress_percent)
            
            # Simulate realistic chunk download time (2-5 seconds per chunk)
            chunk_time = min(5, max(2, current_chunk_mb / 25))  # ~25MB/second
            await asyncio.sleep(chunk_time)
            
            # Update downloaded amount
            downloaded_mb += current_chunk_mb
            
            # Update progress after chunk completion
            final_progress = int((downloaded_mb / total_mb) * 100)
            await self._update_session_progress(session_record_id, final_progress)
            
            # Status updates at key milestones
            if final_progress >= 35 and chunk_num == 0:
                await self._update_session_status(session_record_id, SessionStatus.TRANSFERRING)
                print(f"🔄 STATUS: Started transferring to eSIM at {final_progress}%")
        
        # Complete download
        await self._update_session_progress(session_record_id, 100)
        await self._complete_session_download(session_record_id)
        print(f"✅ CHUNKED DOWNLOAD: Completed {total_mb}MB session")
    
    async def _download_unlimited_session(self, session_record_id: str) -> None:
        """Download unlimited session with quick setup"""
        print(f"🔄 UNLIMITED DOWNLOAD: Quick setup for unlimited session")
        
        # Quick progress updates for unlimited
        progress_steps = [25, 50, 75, 100]
        
        for progress in progress_steps:
            await self._update_session_progress(session_record_id, progress)
            
            if progress == 50:
                await self._update_session_status(session_record_id, SessionStatus.TRANSFERRING)
            
            # Quick intervals for unlimited
            await asyncio.sleep(1)
        
        await self._complete_session_download(session_record_id)
        print(f"✅ UNLIMITED DOWNLOAD: Completed unlimited session setup")
    
    async def _verify_wifi_connection(self) -> None:
        """Verify WiFi connection is available for download"""
        # In a real implementation, this would check actual WiFi connectivity
        # For now, we'll assume connection is available
        await asyncio.sleep(0.1)  # Simulate connection check
    
    async def _update_session_progress(self, session_id: str, progress: int) -> None:
        """Update session download progress"""
        get_supabase_client().table('internet_sessions')\
            .update({'progress_percent': progress})\
            .eq('id', session_id)\
            .execute()
    
    async def _update_session_status(self, session_id: str, status: SessionStatus, error: str = None) -> None:
        """Update session status"""
        update_data = {'status': status.value}
        # Note: error_message column doesn't exist in current schema
        if error:
            print(f"⚠️ Session {session_id} error: {error}")  # Log error instead
        
        get_supabase_client().table('internet_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
    
    async def _complete_session_download(self, session_record_id: str) -> None:
        """Complete the session download process"""
        try:
            # Get session record
            response = get_supabase_client().table('internet_sessions')\
                .select('*')\
                .eq('id', session_record_id)\
                .single()\
                .execute()
            
            session = response.data
            
            # Provision eSIM if not provided
            if not session.get('esim_id'):
                esim_result = await self.esim_service.provision_esim(
                    user_id=session['user_id'],
                    bundle_size_mb=session['data_mb']
                )
                esim_id = esim_result['esim_id']
            else:
                esim_id = session['esim_id']
            
            # Update session record with completion (no expiry date)
            update_data = {
                'status': 'available',  # Use 'available' status as per database constraint
                'progress_percent': 100,
                'download_completed_at': datetime.utcnow().isoformat(),
                'esim_id': esim_id,
                'expires_at': None,  # No expiry - only when data is exhausted
                'data_remaining_mb': session['data_mb'] if session['data_mb'] != -1 else 100 * 1024  # 100GB for unlimited
            }
            
            get_supabase_client().table('internet_sessions')\
                .update(update_data)\
                .eq('id', session_record_id)\
                .execute()
            
        except Exception as e:
            await self._update_session_status(session_record_id, SessionStatus.FAILED, str(e))
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user with can_activate status"""
        try:
            # Get user sessions from database
            response = get_supabase_client().table('internet_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            print(f"🔍 GET USER SESSIONS DEBUG: user_id = {user_id}")
            print(f"🔍 GET USER SESSIONS DEBUG: Raw response data count: {len(response.data) if response.data else 0}")
            if response.data:
                for i, session in enumerate(response.data):
                    print(f"🔍 SESSION {i+1}: id={session.get('id')}, status='{session.get('status')}', data_mb={session.get('data_mb')}")
            
            sessions = []
            for session in response.data:
                # Calculate data size display
                data_mb = session.get('data_mb', 0)
                if data_mb == -1:
                    size_display = "Unlimited"
                elif data_mb >= 1024:
                    size_display = f"{data_mb // 1024}GB"
                else:
                    size_display = f"{data_mb}MB"
                
                # Determine if session can be activated (available but not already active)
                status = session.get('status', 'downloading')
                can_activate = status == 'available'  # Only available sessions, excludes active/downloading/etc
                
                print(f"🔍 SESSION PROCESSING: status='{status}', can_activate={can_activate}")
                
                sessions.append({
                    "id": session['id'],
                    "name": session.get('session_name', size_display),
                    "size": size_display,
                    "status": status,
                    "progress_percent": session.get('progress_percent', 0),
                    "download_started_at": session.get('download_started_at', session.get('created_at')),
                    "expires_at": session.get('expires_at'),
                    "is_active": session.get('status') == 'active',
                    "can_activate": can_activate,
                    "data_remaining_mb": session.get('data_remaining_mb', data_mb if data_mb != -1 else 100 * 1024)
                })
            
            activatable_count = sum(1 for s in sessions if s['can_activate'])
            print(f"🔍 GET USER SESSIONS RESULT: Total sessions: {len(sessions)}, Can activate: {activatable_count}")
            
            return sessions
            
        except Exception as e:
            print(f"❌ GET USER SESSIONS ERROR: {str(e)}")
            raise Exception(f"Failed to get user sessions: {str(e)}")
    
    async def activate_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Activate a downloaded session for use"""
        try:
            # Get session record
            response = get_supabase_client().table('internet_sessions')\
                .select('*')\
                .eq('id', session_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            session = response.data
            
            if session['status'] != 'available':
                raise ValueError("Session must be downloaded before activation")
            
            # Check if session data is exhausted
            data_remaining = session.get('data_remaining_mb', session.get('data_mb', 0))
            if data_remaining <= 0:
                raise ValueError("Session data has been exhausted")
            
            # Activate eSIM for internet browsing
            esim_id = session.get('esim_id')
            if not esim_id:
                # Create eSIM if it doesn't exist
                esim_result = await self.esim_service.provision_esim(
                    user_id=user_id,
                    bundle_size_mb=session['data_mb']
                )
                esim_id = esim_result['esim_id']
                
                # Update session with new eSIM ID
                get_supabase_client().table('internet_sessions')\
                    .update({'esim_id': esim_id})\
                    .eq('id', session_id)\
                    .execute()
            
            esim_activation = await self.esim_service.activate_esim(
                esim_id=esim_id
            )
            
            # Update session status
            print(f"🔍 ACTIVATION: Updating session {session_id} status to {SessionStatus.ACTIVE.value}")
            update_response = get_supabase_client().table('internet_sessions')\
                .update({
                    'status': SessionStatus.ACTIVE.value,
                    'activated_at': datetime.utcnow().isoformat(),
                    'used_data_mb': 0
                })\
                .eq('id', session_id)\
                .execute()
            print(f"🔍 ACTIVATION: Update response: {update_response}")
            print(f"🔍 ACTIVATION: Session {session_id} should now have status='active'")
            
            return {
                'status': 'success',
                'message': 'Session activated - Internet browsing enabled',
                'session_id': session_id,
                'esim_activation': esim_activation,
                'data_remaining_mb': session.get('data_remaining_mb', session['data_mb']) if session['data_mb'] > 0 else 100*1024,
                'internet_access': {
                    'enabled': True,
                    'data_available': True,
                    'connection_type': 'eSIM',
                    'browsing_ready': True
                },
                'usage_info': {
                    'data_used_mb': session.get('data_used_mb', 0),
                    'data_remaining_mb': session.get('data_remaining_mb', session['data_mb']) if session['data_mb'] > 0 else 100*1024,
                    'expires_when': 'data_exhausted',
                    'no_time_limit': True
                },
                'next_steps': [
                    'Your eSIM is now active',
                    'Internet connection is ready',
                    'Start browsing with your available data',
                    'Data will be tracked automatically'
                ]
            }
            
        except Exception as e:
            raise Exception(f"Failed to activate session: {str(e)}")

    
    async def track_session_usage(self, session_id: str, data_used_mb: int) -> Dict[str, Any]:
        """Track data usage for an active session"""
        try:
            # Get current session
            response = get_supabase_client().table('internet_sessions')\
                .select('*')\
                .eq('id', session_id)\
                .single()\
                .execute()
            
            session = response.data
            current_usage = session.get('used_data_mb', 0)
            new_usage = current_usage + data_used_mb
            
            # Check if session is exhausted (for non-unlimited plans)
            is_exhausted = False
            if session['data_mb'] > 0 and new_usage >= session['data_mb']:
                is_exhausted = True
                new_status = SessionStatus.EXHAUSTED.value
            else:
                new_status = session['status']
            
            # Update usage
            get_supabase_client().table('internet_sessions')\
                .update({
                    'used_data_mb': new_usage,
                    'status': new_status,
                    'last_usage_at': datetime.utcnow().isoformat()
                })\
                .eq('id', session_id)\
                .execute()
            
            # If exhausted, deactivate eSIM
            if is_exhausted and session.get('esim_id'):
                await self.esim_service.deactivate_esim(session['esim_id'])
            
            return {
                'status': 'success',
                'data_used_mb': new_usage,
                'data_remaining_mb': max(0, session['data_mb'] - new_usage) if session['data_mb'] > 0 else 999999,
                'is_exhausted': is_exhausted
            }
            
        except Exception as e:
            raise Exception(f"Failed to track usage: {str(e)}")