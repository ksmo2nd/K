"""
Bundle calculation and pricing service
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from ..core.config import settings
from ..core.database import get_supabase_client
from ..models.enums import DataPackStatus


class BundleService:
    """Service for bundle calculations and pricing"""
    
    def __init__(self):
        self.pricing = settings.BUNDLE_PRICING
    
    def get_available_bundles(self) -> List[Dict[str, Any]]:
        """Get all available bundle options with pricing"""
        bundles = []
        for bundle_name, details in self.pricing.items():
            bundle = {
                'name': bundle_name,
                'data_mb': details['data_mb'],
                'price_usd': details['price_usd'],
                'price_ngn': details.get('price_ngn', 0),
                'validity_days': details['validity_days'],
                'plan_type': details.get('plan_type', 'standard'),
                'is_unlimited': details['data_mb'] == -1
            }
            
            # Calculate price per MB for standard plans only
            if details['data_mb'] > 0:
                bundle['price_per_mb_usd'] = round(details['price_usd'] / details['data_mb'], 4)
                bundle['price_per_mb_ngn'] = round(details.get('price_ngn', 0) / details['data_mb'], 4)
            else:
                bundle['price_per_mb_usd'] = 0
                bundle['price_per_mb_ngn'] = 0
                
            bundles.append(bundle)
        return bundles
    
    async def calculate_bundle_price(self, data_mb: int, validity_days: int = 30) -> Dict[str, Any]:
        """Calculate price for custom bundle size"""
        # Find best matching standard bundle for pricing reference
        best_rate = float('inf')
        reference_bundle = None
        
        for bundle_name, details in self.pricing.items():
            rate = details['price_usd'] / details['data_mb']
            if rate < best_rate:
                best_rate = rate
                reference_bundle = details
        
        # Calculate price based on best rate with some markup for custom sizes
        base_price = data_mb * best_rate
        
        # Apply validity multiplier
        validity_multiplier = validity_days / 30  # Base is 30 days
        
        # Apply custom bundle markup (10% for non-standard sizes)
        if data_mb not in [bundle['data_mb'] for bundle in self.pricing.values()]:
            markup = 1.1  # 10% markup for custom bundles
        else:
            markup = 1.0
        
        final_price = base_price * validity_multiplier * markup
        
        return {
            'data_mb': data_mb,
            'validity_days': validity_days,
            'price_usd': round(final_price, 2),
            'price_per_mb': round(final_price / data_mb, 4),
            'is_custom': data_mb not in [bundle['data_mb'] for bundle in self.pricing.values()],
            'markup_applied': markup > 1.0
        }
    
    async def create_data_pack(self, user_id: str, bundle_name: str = None, custom_mb: int = None, validity_days: int = 30, currency: str = 'NGN') -> Dict[str, Any]:
        """Create a new data pack for user"""
        try:
            # Determine bundle details
            if bundle_name and bundle_name in self.pricing:
                bundle_info = self.pricing[bundle_name]
                data_mb = bundle_info['data_mb']
                price_usd = bundle_info['price_usd']
                price_ngn = bundle_info.get('price_ngn', 0)
                validity_days = bundle_info['validity_days']
                plan_type = bundle_info.get('plan_type', 'standard')
                pack_name = bundle_name
                is_unlimited = data_mb == -1
            elif custom_mb:
                pricing_info = await self.calculate_bundle_price(custom_mb, validity_days)
                data_mb = custom_mb
                price_usd = pricing_info['price_usd']
                price_ngn = pricing_info.get('price_ngn', price_usd * 416)  # Approximate NGN rate
                plan_type = 'standard'
                pack_name = f"Custom {data_mb}MB"
                is_unlimited = False
            else:
                raise ValueError("Either bundle_name or custom_mb must be provided")
            
            # Calculate expiry date
            expires_at = datetime.utcnow() + timedelta(days=validity_days)
            
            # For unlimited plans, set data_mb to a large number for tracking
            if is_unlimited:
                total_data_mb = 999999999  # Very large number for unlimited
                remaining_data_mb = 999999999
            else:
                total_data_mb = data_mb
                remaining_data_mb = data_mb
            
            # Create data pack in Supabase
            pack_data = {
                'user_id': user_id,
                'name': pack_name,
                'data_mb': total_data_mb,  # Use data_mb instead of total_data_mb
                'used_data_mb': 0,  # Matches schema
                # remaining_data_mb is GENERATED - don't include it
                'price_ngn': price_ngn,
                'price_usd': price_usd,
                'status': DataPackStatus.ACTIVE.value,
                'is_active': False,  # Purchased but not activated yet
                'expires_at': expires_at.isoformat()
            }
            
            response = get_supabase_client().table('data_packs').insert(pack_data).execute()
            pack_record = response.data[0] if response.data else None
            
            return {
                'pack_id': pack_record['id'],
                'name': pack_name,
                'data_mb': data_mb,
                'price_usd': price_usd,
                'price_ngn': price_ngn,
                'currency': currency,
                'plan_type': plan_type,
                'is_unlimited': is_unlimited,
                'expires_at': expires_at.isoformat(),
                'status': DataPackStatus.ACTIVE.value,
                'requires_activation': True
            }
            
        except Exception as e:
            raise Exception(f"Failed to create data pack: {str(e)}")
    
    async def calculate_usage_cost(self, user_id: str, data_used_mb: float) -> Dict[str, Any]:
        """Calculate cost of data usage across user's active packs"""
        try:
            # Get user's active data packs
            supabase = get_supabase_client()
            response = supabase.table('data_packs').select('*').eq('user_id', user_id).eq('status', DataPackStatus.ACTIVE.value).execute()
            packs = response.data if response.data else []
            
            if not packs:
                return {
                    'total_cost': 0,
                    'data_used_mb': data_used_mb,
                    'packs_affected': [],
                    'error': 'No active data packs found'
                }
            
            # Sort packs by expiry date (use oldest first)
            packs.sort(key=lambda x: x['expires_at'])
            
            remaining_usage = data_used_mb
            total_cost = 0
            packs_affected = []
            
            for pack in packs:
                if remaining_usage <= 0:
                    break
                
                available_mb = max(0, pack['data_mb'] - pack['used_data_mb'])  # Calculate dynamically
                if available_mb <= 0:
                    continue
                
                # Calculate how much to use from this pack
                usage_from_pack = min(remaining_usage, available_mb)
                
                # Calculate cost for this usage
                pack_rate = pack['price_ngn'] / pack['data_mb']
                usage_cost = usage_from_pack * pack_rate
                
                total_cost += usage_cost
                remaining_usage -= usage_from_pack
                
                packs_affected.append({
                    'pack_id': pack['id'],
                    'pack_name': pack['name'],
                    'usage_mb': usage_from_pack,
                    'cost_usd': round(usage_cost, 4),
                    'rate_per_mb': round(pack_rate, 4)
                })
            
            return {
                'total_cost': round(total_cost, 4),
                'data_used_mb': data_used_mb,
                'data_charged_mb': data_used_mb - remaining_usage,
                'data_not_charged_mb': remaining_usage,
                'packs_affected': packs_affected
            }
            
        except Exception as e:
            raise Exception(f"Failed to calculate usage cost: {str(e)}")
    
    async def update_pack_usage(self, user_id: str, data_used_mb: float, session_info: Dict = None) -> Dict[str, Any]:
        """Update data pack usage and return updated status"""
        try:
            # Get active packs sorted by expiry date
            supabase = get_supabase_client()
            response = supabase.table('data_packs').select('*').eq('user_id', user_id).eq('status', DataPackStatus.ACTIVE.value).execute()
            packs = response.data if response.data else []
            packs.sort(key=lambda x: x['expires_at'])
            
            remaining_usage = data_used_mb
            updated_packs = []
            
            for pack in packs:
                if remaining_usage <= 0:
                    break
                
                available_mb = max(0, pack['data_mb'] - pack['used_data_mb'])  # Calculate dynamically
                if available_mb <= 0:
                    continue
                
                # Calculate usage from this pack
                usage_from_pack = min(remaining_usage, available_mb)
                
                # Update pack usage
                new_used = pack['used_data_mb'] + usage_from_pack
                new_remaining = max(0, pack['data_mb'] - new_used)  # Calculate dynamically
                new_status = DataPackStatus.EXHAUSTED.value if new_remaining <= 0 else DataPackStatus.ACTIVE.value
                
                # Update in database
                update_data = {
                    'used_data_mb': new_used,  # Matches schema
                    # remaining_data_mb is GENERATED - don't update it
                    'status': new_status
                }
                supabase.table('data_packs').update(update_data).eq('id', pack['id']).execute()
                
                # Log the usage
                log_data = {
                    'user_id': user_id,
                    'data_pack_id': pack['id'],
                    'data_used_mb': usage_from_pack,
                    **(session_info or {})
                }
                supabase.table('usage_logs').insert(log_data).execute()
                
                updated_packs.append({
                    'pack_id': pack['id'],
                    'pack_name': pack['name'],
                    'usage_mb': usage_from_pack,
                    'new_used_mb': new_used,
                    'new_remaining_mb': new_remaining,
                    'status': new_status
                })
                
                remaining_usage -= usage_from_pack
            
            return {
                'success': True,
                'data_processed_mb': data_used_mb - remaining_usage,
                'data_not_processed_mb': remaining_usage,
                'updated_packs': updated_packs
            }
            
        except Exception as e:
            raise Exception(f"Failed to update pack usage: {str(e)}")
    
    async def get_user_bundle_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive bundle summary for user"""
        try:
            # Get all user's data packs
            supabase = get_supabase_client()
            response = supabase.table('data_packs').select('*').eq('user_id', user_id).execute()
            all_packs = response.data if response.data else []
            
            summary = {
                'total_packs': len(all_packs),
                'active_packs': len([p for p in all_packs if p['status'] == DataPackStatus.ACTIVE.value]),
                'total_data_mb': sum(p['data_mb'] for p in all_packs),
                'used_data_mb': sum(p['used_data_mb'] for p in all_packs),
                'remaining_data_mb': sum(max(0, p['data_mb'] - p['used_data_mb']) for p in all_packs if p['status'] == DataPackStatus.ACTIVE.value),
                'total_spent_ngn': sum(p['price_ngn'] for p in all_packs),
                'by_status': {}
            }
            
            # Group by status
            for status in DataPackStatus:
                status_packs = [p for p in all_packs if p['status'] == status.value]
                summary['by_status'][status.value] = {
                    'count': len(status_packs),
                    'total_data_mb': sum(p['data_mb'] for p in status_packs),
                    'total_spent_ngn': sum(p['price_ngn'] for p in status_packs)
                }
            
            return summary
            
        except Exception as e:
            raise Exception(f"Failed to get bundle summary: {str(e)}")
    
    async def activate_data_pack(self, user_id: str, pack_id: str, esim_id: str = None) -> Dict[str, Any]:
        """Activate a purchased data pack for use"""
        try:
            # Verify pack belongs to user
            pack_response = get_supabase_client().table('data_packs').select('*').eq('id', pack_id).eq('user_id', user_id).execute()
            if not pack_response.data:
                raise Exception("Data pack not found or doesn't belong to user")
            
            pack = pack_response.data[0]
            
            # Check if pack is still valid
            expires_at = datetime.fromisoformat(pack['expires_at'].replace('Z', '+00:00'))
            if expires_at <= datetime.now(expires_at.tzinfo):
                raise Exception("Data pack has expired")
            
            # Use database function to activate pack
            if esim_id:
                get_supabase_client().rpc('activate_data_pack', {'pack_id': pack_id, 'esim_id': esim_id}).execute()
            else:
                get_supabase_client().rpc('activate_data_pack', {'pack_id': pack_id}).execute()
            
            return {
                'success': True,
                'pack_id': pack_id,
                'pack_name': pack['name'],
                'plan_type': pack.get('plan_type', 'standard'),
                'activated_at': datetime.utcnow().isoformat(),
                'esim_linked': esim_id is not None
            }
            
        except Exception as e:
            raise Exception(f"Failed to activate data pack: {str(e)}")
    
    async def deactivate_data_pack(self, user_id: str, pack_id: str) -> Dict[str, Any]:
        """Deactivate a data pack"""
        try:
            # Verify pack belongs to user
            pack_response = get_supabase_client().table('data_packs').select('*').eq('id', pack_id).eq('user_id', user_id).execute()
            if not pack_response.data:
                raise Exception("Data pack not found or doesn't belong to user")
            
            # Use database function to deactivate pack
            get_supabase_client().rpc('deactivate_data_pack', {'pack_id': pack_id}).execute()
            
            return {
                'success': True,
                'pack_id': pack_id,
                'deactivated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to deactivate data pack: {str(e)}")
    
    async def get_activatable_packs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get data packs that can be activated"""
        try:
            # Get purchased but inactive packs that haven't expired
            current_time = datetime.utcnow().isoformat()
            response = get_supabase_client().table('data_packs').select('*').eq('user_id', user_id).eq('is_active', False).gt('expires_at', current_time).execute()
            
            activatable_packs = []
            for pack in response.data:
                activatable_packs.append({
                    'pack_id': pack['id'],
                    'name': pack['name'],
                    'plan_type': pack.get('plan_type', 'standard'),
                    'data_mb': pack['data_mb'],
                    'is_unlimited': pack.get('plan_type') == 'unlimited',
                    'price': pack['price'],
                    'currency': pack['currency'],
                    'expires_at': pack['expires_at'],
                    'validity_days': (datetime.fromisoformat(pack['expires_at'].replace('Z', '+00:00')) - datetime.now(datetime.fromisoformat(pack['expires_at'].replace('Z', '+00:00')).tzinfo)).days
                })
            
            return activatable_packs
            
        except Exception as e:
            raise Exception(f"Failed to get activatable packs: {str(e)}")
    
    async def get_active_pack(self, user_id: str) -> Dict[str, Any]:
        """Get currently active data pack for user"""
        try:
            response = get_supabase_client().table('data_packs').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            if not response.data:
                return None
            
            pack = response.data[0]
            return {
                'pack_id': pack['id'],
                'name': pack['name'],
                'plan_type': pack.get('plan_type', 'standard'),
                'data_mb': pack['data_mb'],
                'used_mb': pack['used_data_mb'],
                'remaining_mb': max(0, pack['data_mb'] - pack['used_data_mb']),
                'is_unlimited': pack.get('plan_type') == 'unlimited',
                'activated_at': pack.get('activated_at'),
                'expires_at': pack['expires_at']
            }
            
        except Exception as e:
            raise Exception(f"Failed to get active pack: {str(e)}")