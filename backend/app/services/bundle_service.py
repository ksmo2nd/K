"""
Bundle calculation and pricing service
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from ..core.config import settings
from ..core.database import supabase_client
from ..models.enums import DataPackStatus


class BundleService:
    """Service for bundle calculations and pricing"""
    
    def __init__(self):
        self.pricing = settings.BUNDLE_PRICING
    
    def get_available_bundles(self) -> List[Dict[str, Any]]:
        """Get all available bundle options with pricing"""
        bundles = []
        for bundle_name, details in self.pricing.items():
            bundles.append({
                'name': bundle_name,
                'data_mb': details['data_mb'],
                'price_usd': details['price_usd'],
                'validity_days': details['validity_days'],
                'price_per_mb': round(details['price_usd'] / details['data_mb'], 4)
            })
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
    
    async def create_data_pack(self, user_id: str, bundle_name: str = None, custom_mb: int = None, validity_days: int = 30) -> Dict[str, Any]:
        """Create a new data pack for user"""
        try:
            # Determine bundle details
            if bundle_name and bundle_name in self.pricing:
                bundle_info = self.pricing[bundle_name]
                data_mb = bundle_info['data_mb']
                price = bundle_info['price_usd']
                validity_days = bundle_info['validity_days']
                pack_name = bundle_name
            elif custom_mb:
                pricing_info = await self.calculate_bundle_price(custom_mb, validity_days)
                data_mb = custom_mb
                price = pricing_info['price_usd']
                pack_name = f"Custom {data_mb}MB"
            else:
                raise ValueError("Either bundle_name or custom_mb must be provided")
            
            # Calculate expiry date
            expires_at = datetime.utcnow() + timedelta(days=validity_days)
            
            # Create data pack in Supabase
            pack_data = {
                'user_id': user_id,
                'name': pack_name,
                'total_data_mb': data_mb,
                'used_data_mb': 0,
                'remaining_data_mb': data_mb,
                'price': price,
                'currency': 'USD',
                'status': DataPackStatus.ACTIVE.value,
                'expires_at': expires_at.isoformat()
            }
            
            response = supabase_client.client.table('data_packs').insert(pack_data).execute()
            pack_record = response.data[0] if response.data else None
            
            return {
                'pack_id': pack_record['id'],
                'name': pack_name,
                'data_mb': data_mb,
                'price_usd': price,
                'expires_at': expires_at.isoformat(),
                'status': DataPackStatus.ACTIVE.value
            }
            
        except Exception as e:
            raise Exception(f"Failed to create data pack: {str(e)}")
    
    async def calculate_usage_cost(self, user_id: str, data_used_mb: float) -> Dict[str, Any]:
        """Calculate cost of data usage across user's active packs"""
        try:
            # Get user's active data packs
            packs = await supabase_client.get_user_data_packs(user_id, DataPackStatus.ACTIVE.value)
            
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
                
                available_mb = pack['remaining_data_mb']
                if available_mb <= 0:
                    continue
                
                # Calculate how much to use from this pack
                usage_from_pack = min(remaining_usage, available_mb)
                
                # Calculate cost for this usage
                pack_rate = pack['price'] / pack['total_data_mb']
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
            packs = await supabase_client.get_user_data_packs(user_id, DataPackStatus.ACTIVE.value)
            packs.sort(key=lambda x: x['expires_at'])
            
            remaining_usage = data_used_mb
            updated_packs = []
            
            for pack in packs:
                if remaining_usage <= 0:
                    break
                
                available_mb = pack['remaining_data_mb']
                if available_mb <= 0:
                    continue
                
                # Calculate usage from this pack
                usage_from_pack = min(remaining_usage, available_mb)
                
                # Update pack usage
                new_used = pack['used_data_mb'] + usage_from_pack
                new_remaining = pack['remaining_data_mb'] - usage_from_pack
                new_status = DataPackStatus.EXHAUSTED.value if new_remaining <= 0 else DataPackStatus.ACTIVE.value
                
                # Update in database
                await supabase_client.update_data_pack_usage(
                    pack['id'],
                    new_used,
                    new_remaining,
                    new_status
                )
                
                # Log the usage
                await supabase_client.log_data_usage(
                    user_id,
                    pack['id'],
                    usage_from_pack,
                    **(session_info or {})
                )
                
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
            all_packs = await supabase_client.get_user_data_packs(user_id)
            
            summary = {
                'total_packs': len(all_packs),
                'active_packs': len([p for p in all_packs if p['status'] == DataPackStatus.ACTIVE.value]),
                'total_data_mb': sum(p['total_data_mb'] for p in all_packs),
                'used_data_mb': sum(p['used_data_mb'] for p in all_packs),
                'remaining_data_mb': sum(p['remaining_data_mb'] for p in all_packs if p['status'] == DataPackStatus.ACTIVE.value),
                'total_spent_usd': sum(p['price'] for p in all_packs),
                'by_status': {}
            }
            
            # Group by status
            for status in DataPackStatus:
                status_packs = [p for p in all_packs if p['status'] == status.value]
                summary['by_status'][status.value] = {
                    'count': len(status_packs),
                    'total_data_mb': sum(p['total_data_mb'] for p in status_packs),
                    'total_spent_usd': sum(p['price'] for p in status_packs)
                }
            
            return summary
            
        except Exception as e:
            raise Exception(f"Failed to get bundle summary: {str(e)}")