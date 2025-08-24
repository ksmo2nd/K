"""
Notification service for user alerts
"""

from typing import Dict, Any, Optional
import structlog
from datetime import datetime

from ..core.database import supabase_client

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for sending notifications to users"""
    
    async def send_low_data_alert(self, user_id: str, pack_id: str, remaining_mb: float, total_mb: float):
        """Send low data balance alert"""
        try:
            percentage_remaining = (remaining_mb / total_mb) * 100 if total_mb > 0 else 0
            
            notification_data = {
                'user_id': user_id,
                'type': 'low_data_alert',
                'title': 'Low Data Balance Warning',
                'message': f'Your data pack has only {remaining_mb:.1f}MB ({percentage_remaining:.1f}%) remaining.',
                'data': {
                    'pack_id': pack_id,
                    'remaining_mb': remaining_mb,
                    'total_mb': total_mb,
                    'percentage_remaining': percentage_remaining
                },
                'priority': 'high'
            }
            
            await self._store_notification(notification_data)
            await self._send_push_notification(user_id, notification_data)
            
            logger.info(f"Sent low data alert to user {user_id} for pack {pack_id}")
            
        except Exception as e:
            logger.error(f"Error sending low data alert: {e}")
    
    async def send_usage_threshold_alert(self, user_id: str, pack_id: str, threshold_percent: int):
        """Send data usage threshold alert"""
        try:
            notification_data = {
                'user_id': user_id,
                'type': 'usage_threshold_alert',
                'title': f'{threshold_percent}% Data Used',
                'message': f'You have used {threshold_percent}% of your data pack. Consider monitoring your usage.',
                'data': {
                    'pack_id': pack_id,
                    'threshold_percent': threshold_percent
                },
                'priority': 'medium'
            }
            
            await self._store_notification(notification_data)
            await self._send_push_notification(user_id, notification_data)
            
            logger.info(f"Sent {threshold_percent}% usage alert to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending usage threshold alert: {e}")
    
    async def send_pack_expired_notification(self, user_id: str, pack_id: str):
        """Send data pack expired notification"""
        try:
            notification_data = {
                'user_id': user_id,
                'type': 'pack_expired',
                'title': 'Data Pack Expired',
                'message': 'One of your data packs has expired. Purchase a new pack to continue using data.',
                'data': {
                    'pack_id': pack_id
                },
                'priority': 'high'
            }
            
            await self._store_notification(notification_data)
            await self._send_push_notification(user_id, notification_data)
            
            logger.info(f"Sent pack expired notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending pack expired notification: {e}")
    
    async def send_esim_activation_success(self, user_id: str, esim_id: str):
        """Send eSIM activation success notification"""
        try:
            notification_data = {
                'user_id': user_id,
                'type': 'esim_activated',
                'title': 'eSIM Activated Successfully',
                'message': 'Your eSIM has been activated and is ready to use.',
                'data': {
                    'esim_id': esim_id
                },
                'priority': 'medium'
            }
            
            await self._store_notification(notification_data)
            await self._send_push_notification(user_id, notification_data)
            
            logger.info(f"Sent eSIM activation success notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending eSIM activation notification: {e}")
    
    async def send_welcome_notification(self, user_id: str):
        """Send welcome notification to new users"""
        try:
            notification_data = {
                'user_id': user_id,
                'type': 'welcome',
                'title': 'Welcome to KSWiFi!',
                'message': 'Welcome to KSWiFi! You can now purchase data packs and manage your eSIMs.',
                'data': {},
                'priority': 'low'
            }
            
            await self._store_notification(notification_data)
            await self._send_push_notification(user_id, notification_data)
            
            logger.info(f"Sent welcome notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending welcome notification: {e}")
    
    async def _store_notification(self, notification_data: Dict[str, Any]):
        """Store notification in database"""
        try:
            # Add timestamp
            notification_data['created_at'] = datetime.utcnow().isoformat()
            notification_data['read'] = False
            
            # Store in notifications table
            supabase_client.client.table('notifications').insert(notification_data).execute()
            
        except Exception as e:
            logger.error(f"Error storing notification: {e}")
    
    async def _send_push_notification(self, user_id: str, notification_data: Dict[str, Any]):
        """Send push notification to user's devices"""
        try:
            # Get user's push tokens from database
            response = supabase_client.client.table('user_devices').select('push_token').eq('user_id', user_id).eq('active', True).execute()
            devices = response.data
            
            if not devices:
                logger.debug(f"No active devices found for user {user_id}")
                return
            
            # TODO: Implement actual push notification sending
            # This would integrate with services like:
            # - Firebase Cloud Messaging (FCM) for Android
            # - Apple Push Notification Service (APNs) for iOS
            # - Web Push for web browsers
            
            for device in devices:
                push_token = device.get('push_token')
                if push_token:
                    # Send push notification
                    logger.debug(f"Would send push notification to token {push_token[:10]}...")
                    # await self._send_fcm_notification(push_token, notification_data)
                    # await self._send_apns_notification(push_token, notification_data)
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> Dict[str, Any]:
        """Get notifications for a user"""
        try:
            query = supabase_client.client.table('notifications').select('*').eq('user_id', user_id)
            
            if unread_only:
                query = query.eq('read', False)
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            notifications = response.data
            
            # Get unread count
            unread_response = supabase_client.client.table('notifications').select('id', count='exact').eq('user_id', user_id).eq('read', False).execute()
            unread_count = unread_response.count
            
            return {
                'notifications': notifications,
                'unread_count': unread_count,
                'total_returned': len(notifications)
            }
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return {
                'notifications': [],
                'unread_count': 0,
                'total_returned': 0,
                'error': str(e)
            }
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            supabase_client.client.table('notifications').update({
                'read': True,
                'read_at': datetime.utcnow().isoformat()
            }).eq('id', notification_id).eq('user_id', user_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    async def mark_all_notifications_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user"""
        try:
            supabase_client.client.table('notifications').update({
                'read': True,
                'read_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('read', False).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False