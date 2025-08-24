"""
Internet Session Download Service - Core KSWiFi functionality
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.config import settings
from ..core.database import supabase_client
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
    
    def _safe_db_operation(self, operation_func, fallback_data=None):
        """Safely execute database operations with fallback"""
        try:
            return operation_func()
        except Exception as e:
            print(f"Database operation failed: {e}")
            if fallback_data:
                return fallback_data
            else:
                # Return mock response structure
                return type('MockResponse', (), {'data': []})() 
    
    async def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get available session download options"""
        sessions = []
        
        for session_name, details in self.pricing.items():
            session = {
                'id': session_name.lower().replace(' ', '_'),
                'name': session_name,
                'size': session_name,
                'data_mb': details['data_mb'],
                'price_ngn': details.get('price_ngn', 0),
                'price_usd': details['price_usd'],
                'validity_days': details['validity_days'],
                'plan_type': details.get('plan_type', 'standard'),
                'is_unlimited': details['data_mb'] == -1,
                'is_free': details.get('price_ngn', 0) == 0,
                'description': self._get_session_description(session_name, details),
                'features': self._get_session_features(details)
            }
            sessions.append(session)
        
        # Sort: Free sessions first, then by size
        sessions.sort(key=lambda x: (not x['is_free'], x['price_ngn']))
        return sessions
    
    def _get_session_description(self, name: str, details: Dict) -> str:
        """Get user-friendly session description"""
        if details['data_mb'] == -1:
            return f"Download unlimited internet sessions for {details['validity_days']} days"
        else:
            size_gb = details['data_mb'] / 1024
            if size_gb >= 1:
                return f"Download {size_gb:.0f}GB internet session - use offline for {details['validity_days']} days"
            else:
                return f"Download {details['data_mb']}MB internet session - use offline for {details['validity_days']} days"
    
    def _get_session_features(self, details: Dict) -> List[str]:
        """Get session features list"""
        features = []
        
        if details['data_mb'] == -1:
            features.append("Unlimited session downloads")
            features.append("No download size limits")
        else:
            size_gb = details['data_mb'] / 1024
            features.append(f"{size_gb:.0f}GB internet session")
            features.append("Full browsing capability")
        
        features.append(f"Valid for {details['validity_days']} days")
        features.append("Works offline via eSIM")
        features.append("Activate with QR code")
        
        return features
    
    async def start_session_download(
        self, 
        user_id: str, 
        session_id: str,
        esim_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start downloading an internet session"""
        try:
            # Get session details
            session_details = None
            for name, details in self.pricing.items():
                if name.lower().replace(' ', '_') == session_id:
                    session_details = details
                    break
            
            if not session_details:
                raise ValueError(f"Session {session_id} not found")
            
            # Check user's download quota (for free users)
            if session_details.get('price_ngn', 0) == 0:
                await self._check_free_quota(user_id)
            
            # Create session record
            session_data = {
                'user_id': user_id,
                'session_id': session_id,
                'session_name': session_id.replace('_', ' ').title(),
                'data_mb': session_details['data_mb'],
                'price_ngn': session_details.get('price_ngn', 0),
                'validity_days': session_details['validity_days'],
                'plan_type': session_details.get('plan_type', 'standard'),
                'status': SessionStatus.DOWNLOADING.value,
                'download_started_at': datetime.utcnow().isoformat(),
                'progress_percent': 0,
                'esim_id': esim_id
            }
            
            response = supabase_client.client.table('internet_sessions').insert(session_data).execute()
            session_record = response.data[0] if response.data else None
            
            # Start background download process
            asyncio.create_task(self._download_session_background(session_record['id']))
            
            return {
                'session_id': session_record['id'],
                'status': SessionStatus.DOWNLOADING.value,
                'message': 'Session download started',
                'estimated_time_minutes': self._estimate_download_time(session_details['data_mb'])
            }
            
        except Exception as e:
            raise Exception(f"Failed to start session download: {str(e)}")
    
    async def _check_free_quota(self, user_id: str) -> None:
        """Check if user has exceeded free session quota"""
        # Get user's free sessions this month
        current_month = datetime.utcnow().replace(day=1)
        
        response = supabase_client.client.table('internet_sessions')\
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
    
    async def _download_session_background(self, session_record_id: str) -> None:
        """Background process to simulate session download"""
        try:
            # Get session record
            response = supabase_client.client.table('internet_sessions')\
                .select('*')\
                .eq('id', session_record_id)\
                .single()\
                .execute()
            
            session = response.data
            data_mb = session['data_mb']
            
            # Simulate download progress
            for progress in [10, 25, 40, 60, 75, 90, 100]:
                await asyncio.sleep(1)  # Simulate download time
                
                # Update progress
                await self._update_session_progress(session_record_id, progress)
                
                if progress == 50:
                    # Start eSIM provisioning/transfer
                    await self._update_session_status(session_record_id, SessionStatus.TRANSFERRING)
                elif progress == 100:
                    # Complete download
                    await self._complete_session_download(session_record_id)
            
        except Exception as e:
            await self._update_session_status(session_record_id, SessionStatus.FAILED, str(e))
    
    async def _update_session_progress(self, session_id: str, progress: int) -> None:
        """Update session download progress"""
        supabase_client.client.table('internet_sessions')\
            .update({'progress_percent': progress})\
            .eq('id', session_id)\
            .execute()
    
    async def _update_session_status(self, session_id: str, status: SessionStatus, error: str = None) -> None:
        """Update session status"""
        update_data = {'status': status.value}
        if error:
            update_data['error_message'] = error
        
        supabase_client.client.table('internet_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
    
    async def _complete_session_download(self, session_record_id: str) -> None:
        """Complete the session download process"""
        try:
            # Get session record
            response = supabase_client.client.table('internet_sessions')\
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
            
            # Update session record with completion
            update_data = {
                'status': SessionStatus.STORED.value,
                'progress_percent': 100,
                'download_completed_at': datetime.utcnow().isoformat(),
                'esim_id': esim_id,
                'expires_at': (datetime.utcnow() + timedelta(days=session['validity_days'])).isoformat()
            }
            
            supabase_client.client.table('internet_sessions')\
                .update(update_data)\
                .eq('id', session_record_id)\
                .execute()
            
        except Exception as e:
            await self._update_session_status(session_record_id, SessionStatus.FAILED, str(e))
    
    async def activate_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Activate a downloaded session for use"""
        try:
            # Get session record
            response = supabase_client.client.table('internet_sessions')\
                .select('*')\
                .eq('id', session_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            session = response.data
            
            if session['status'] != SessionStatus.STORED.value:
                raise ValueError("Session must be downloaded before activation")
            
            # Check if session has expired
            if datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00')) < datetime.utcnow():
                raise ValueError("Session has expired")
            
            # Activate eSIM
            esim_activation = await self.esim_service.activate_esim(
                esim_id=session['esim_id'],
                user_id=user_id
            )
            
            # Update session status
            supabase_client.client.table('internet_sessions')\
                .update({
                    'status': SessionStatus.ACTIVE.value,
                    'activated_at': datetime.utcnow().isoformat(),
                    'used_data_mb': 0
                })\
                .eq('id', session_id)\
                .execute()
            
            return {
                'status': 'success',
                'message': 'Session activated successfully',
                'session_id': session_id,
                'esim_activation': esim_activation,
                'data_remaining_mb': session['data_mb'] if session['data_mb'] > 0 else 999999
            }
            
        except Exception as e:
            raise Exception(f"Failed to activate session: {str(e)}")
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        response = supabase_client.client.table('internet_sessions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('download_started_at', desc=True)\
            .execute()
        
        sessions = []
        for session in response.data:
            session_info = {
                'id': session['id'],
                'name': session['session_name'],
                'size': f"{session['data_mb'] / 1024:.0f}GB" if session['data_mb'] > 0 else "Unlimited",
                'status': session['status'],
                'progress_percent': session.get('progress_percent', 0),
                'download_started_at': session['download_started_at'],
                'expires_at': session.get('expires_at'),
                'is_active': session['status'] == SessionStatus.ACTIVE.value,
                'can_activate': session['status'] == SessionStatus.STORED.value,
                'data_remaining_mb': session['data_mb'] - session.get('used_data_mb', 0) if session['data_mb'] > 0 else 999999
            }
            sessions.append(session_info)
        
        return sessions
    
    async def track_session_usage(self, session_id: str, data_used_mb: int) -> Dict[str, Any]:
        """Track data usage for an active session"""
        try:
            # Get current session
            response = supabase_client.client.table('internet_sessions')\
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
            supabase_client.client.table('internet_sessions')\
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