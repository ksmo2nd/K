"""
Data monitoring and background task service
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
import structlog

from ..core.config import settings
from ..core.database import get_supabase_client
from ..models.enums import DataPackStatus, ESIMStatus
from .esim_service import ESIMService
from .notification_service import NotificationService

logger = structlog.get_logger(__name__)


class MonitoringService:
    """Service for monitoring data usage and running background tasks"""
    
    def __init__(self):
        self.esim_service = ESIMService()
        self.notification_service = NotificationService()
        self.check_interval = settings.DATA_CHECK_INTERVAL_MINUTES
        self.low_data_threshold = settings.LOW_DATA_THRESHOLD_MB
        self._running = False
    
    async def start_monitoring(self):
        """Start the background monitoring tasks"""
        self._running = True
        logger.info("Starting data monitoring service")
        
        # Start all monitoring tasks concurrently
        await asyncio.gather(
            self._monitor_data_usage(),
            self._monitor_esim_status(),
            self._cleanup_expired_packs(),
            self._sync_provider_data(),
            return_exceptions=True
        )
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self._running = False
        logger.info("Stopping data monitoring service")
    
    async def _monitor_data_usage(self):
        """Monitor data usage and send alerts for low balances"""
        logger.info("Starting data usage monitoring")
        
        while self._running:
            try:
                # Get all active data packs
                response = get_supabase_client().table('data_packs').select('*').eq('status', DataPackStatus.ACTIVE.value).execute()
                active_packs = response.data
                
                for pack in active_packs:
                    await self._check_pack_usage(pack)
                
                logger.debug(f"Checked {len(active_packs)} active data packs")
                
            except Exception as e:
                logger.error(f"Error in data usage monitoring: {e}")
            
            # Wait for next check
            await asyncio.sleep(self.check_interval * 60)
    
    async def _check_pack_usage(self, pack: Dict[str, Any]):
        """Check individual pack usage and send alerts"""
        try:
            remaining_mb = pack.get('remaining_data_mb', 0)
            total_mb = pack.get('data_mb', 0)
            user_id = pack.get('user_id')
            pack_id = pack.get('id')
            
            # Check if pack is low on data
            if remaining_mb <= self.low_data_threshold:
                await self.notification_service.send_low_data_alert(
                    user_id,
                    pack_id,
                    remaining_mb,
                    total_mb
                )
            
            # Check if pack has expired
            expires_at = datetime.fromisoformat(pack.get('expires_at').replace('Z', '+00:00'))
            if expires_at <= datetime.now(expires_at.tzinfo):
                await self._expire_data_pack(pack_id)
                await self.notification_service.send_pack_expired_notification(user_id, pack_id)
            
            # Check usage percentage thresholds
            usage_percent = ((total_mb - remaining_mb) / total_mb) * 100 if total_mb > 0 else 0
            
            if usage_percent >= 90 and not pack.get('alert_90_sent'):
                await self.notification_service.send_usage_threshold_alert(user_id, pack_id, 90)
                await self._mark_alert_sent(pack_id, 'alert_90_sent')
            elif usage_percent >= 75 and not pack.get('alert_75_sent'):
                await self.notification_service.send_usage_threshold_alert(user_id, pack_id, 75)
                await self._mark_alert_sent(pack_id, 'alert_75_sent')
                
        except Exception as e:
            logger.error(f"Error checking pack usage for pack {pack.get('id')}: {e}")
    
    async def _monitor_esim_status(self):
        """Monitor eSIM status and sync with provider"""
        logger.info("Starting eSIM status monitoring")
        
        while self._running:
            try:
                # Get all active eSIMs
                response = get_supabase_client().table('esims').select('id, user_id, iccid, status, apn, created_at').eq('status', ESIMStatus.ACTIVE.value).execute()
                active_esims = response.data
                
                for esim in active_esims:
                    await self._sync_esim_status(esim)
                
                logger.debug(f"Checked {len(active_esims)} active eSIMs")
                
            except Exception as e:
                logger.error(f"Error in eSIM status monitoring: {e}")
            
            # Check eSIMs less frequently (every 15 minutes)
            await asyncio.sleep(15 * 60)
    
    async def _sync_esim_status(self, esim: Dict[str, Any]):
        """Sync individual eSIM status with provider"""
        try:
            esim_id = esim.get('id')
            
            # Get current usage from provider
            usage_data = await self.esim_service.get_esim_usage(esim_id)
            
            # Update usage in data pack if linked
            if usage_data.get('data_used_mb', 0) > 0:
                await self._update_esim_data_usage(esim, usage_data)
                
        except Exception as e:
            logger.error(f"Error syncing eSIM status for {esim.get('id')}: {e}")
    
    async def _update_esim_data_usage(self, esim: Dict[str, Any], usage_data: Dict[str, Any]):
        """Update data pack usage based on eSIM usage"""
        try:
            user_id = esim.get('user_id')
            data_used_mb = usage_data.get('data_used_mb', 0)
            
            # Find active data packs for this user
            packs = await supabase_client.get_user_data_packs(user_id, DataPackStatus.ACTIVE.value)
            
            if packs:
                # Use the first active pack (you could implement more sophisticated logic)
                pack = packs[0]
                current_used = pack.get('used_data_mb', 0)
                
                # Only update if there's new usage
                if data_used_mb > current_used:
                    new_usage = data_used_mb - current_used
                    new_remaining = pack.get('remaining_data_mb', 0) - new_usage
                    
                    await supabase_client.update_data_pack_usage(
                        pack['id'],
                        data_used_mb,
                        max(0, new_remaining),
                        DataPackStatus.EXHAUSTED.value if new_remaining <= 0 else DataPackStatus.ACTIVE.value
                    )
                    
                    # Log the usage
                    await supabase_client.log_data_usage(
                        user_id,
                        pack['id'],
                        new_usage,
                        session_duration=usage_data.get('session_duration'),
                        location=usage_data.get('location'),
                        device_info=f"eSIM {esim.get('iccid')}"
                    )
                    
        except Exception as e:
            logger.error(f"Error updating eSIM data usage: {e}")
    
    async def _cleanup_expired_packs(self):
        """Clean up expired data packs"""
        logger.info("Starting expired packs cleanup")
        
        while self._running:
            try:
                # Find expired packs that are still marked as active
                current_time = datetime.utcnow().isoformat()
                response = get_supabase_client().table('data_packs').select('*').eq('status', DataPackStatus.ACTIVE.value).lt('expires_at', current_time).execute()
                expired_packs = response.data
                
                for pack in expired_packs:
                    await self._expire_data_pack(pack['id'])
                    logger.info(f"Expired data pack {pack['id']}")
                
                if expired_packs:
                    logger.info(f"Cleaned up {len(expired_packs)} expired data packs")
                
            except Exception as e:
                logger.error(f"Error in expired packs cleanup: {e}")
            
            # Run cleanup every hour
            await asyncio.sleep(60 * 60)
    
    async def _sync_provider_data(self):
        """Sync data usage with eSIM providers"""
        logger.info("Starting provider data sync")
        
        while self._running:
            try:
                # Get all users with active eSIMs
                response = get_supabase_client().table('esims').select('user_id').eq('status', ESIMStatus.ACTIVE.value).execute()
                active_users = list(set([esim['user_id'] for esim in response.data]))
                
                for user_id in active_users:
                    await self._sync_user_provider_data(user_id)
                
                logger.debug(f"Synced provider data for {len(active_users)} users")
                
            except Exception as e:
                logger.error(f"Error in provider data sync: {e}")
            
            # Sync with provider every 30 minutes
            await asyncio.sleep(30 * 60)
    
    async def _sync_user_provider_data(self, user_id: str):
        """Sync provider data for a specific user"""
        try:
            # Get user's active eSIMs
            user_esims = await supabase_client.get_user_esims(user_id)
            active_esims = [esim for esim in user_esims if esim['status'] == ESIMStatus.ACTIVE.value]
            
            for esim in active_esims:
                # Get latest usage from provider
                usage_data = await self.esim_service.get_esim_usage(esim['id'])
                
                # Update local records if needed
                await self._update_esim_data_usage(esim, usage_data)
                
        except Exception as e:
            logger.error(f"Error syncing provider data for user {user_id}: {e}")
    
    async def _expire_data_pack(self, pack_id: str):
        """Mark a data pack as expired"""
        get_supabase_client().table('data_packs').update({
            'status': DataPackStatus.EXPIRED.value
        }).eq('id', pack_id).execute()
    
    async def _mark_alert_sent(self, pack_id: str, alert_field: str):
        """Mark that an alert has been sent for a pack"""
        get_supabase_client().table('data_packs').update({
            alert_field: True
        }).eq('id', pack_id).execute()
    
    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring service statistics"""
        try:
            # Get counts of various items being monitored
            active_packs_response = get_supabase_client().table('data_packs').select('id', count='exact').eq('status', DataPackStatus.ACTIVE.value).execute()
            active_esims_response = get_supabase_client().table('esims').select('id', count='exact').eq('status', ESIMStatus.ACTIVE.value).execute()
            
            # Get recent usage logs
            recent_logs_response = get_supabase_client().table('usage_logs').select('id', count='exact').gte('created_at', (datetime.utcnow() - timedelta(hours=1)).isoformat()).execute()
            
            return {
                'service_running': self._running,
                'check_interval_minutes': self.check_interval,
                'low_data_threshold_mb': self.low_data_threshold,
                'active_data_packs': active_packs_response.count,
                'active_esims': active_esims_response.count,
                'recent_usage_logs': recent_logs_response.count,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring stats: {e}")
            return {
                'service_running': self._running,
                'error': str(e)
            }