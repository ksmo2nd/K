"""
Bundle management routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..services.bundle_service import BundleService

router = APIRouter()
bundle_service = BundleService()


class CreateBundleRequest(BaseModel):
    user_id: str
    bundle_name: Optional[str] = None
    custom_mb: Optional[int] = None
    validity_days: int = 30


class UpdateUsageRequest(BaseModel):
    user_id: str
    data_used_mb: float
    session_duration: Optional[int] = None
    location: Optional[str] = None
    device_info: Optional[str] = None


@router.get("/available")
async def get_available_bundles():
    """Get all available bundle options with pricing"""
    try:
        bundles = bundle_service.get_available_bundles()
        return {
            "bundles": bundles,
            "currency": "USD"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bundles: {str(e)}")


@router.post("/calculate-price")
async def calculate_bundle_price(data_mb: int, validity_days: int = 30):
    """Calculate price for a custom bundle"""
    try:
        pricing = await bundle_service.calculate_bundle_price(data_mb, validity_days)
        return pricing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating price: {str(e)}")


@router.post("/create")
async def create_bundle(request: CreateBundleRequest):
    """Create a new data bundle for user"""
    try:
        result = await bundle_service.create_data_pack(
            user_id=request.user_id,
            bundle_name=request.bundle_name,
            custom_mb=request.custom_mb,
            validity_days=request.validity_days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating bundle: {str(e)}")


@router.post("/usage/update")
async def update_usage(request: UpdateUsageRequest):
    """Update data usage for user's active packs"""
    try:
        session_info = {
            'session_duration': request.session_duration,
            'location': request.location,
            'device_info': request.device_info
        }
        
        result = await bundle_service.update_pack_usage(
            user_id=request.user_id,
            data_used_mb=request.data_used_mb,
            session_info=session_info
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating usage: {str(e)}")


@router.post("/usage/calculate-cost")
async def calculate_usage_cost(user_id: str, data_used_mb: float):
    """Calculate cost of data usage across user's packs"""
    try:
        cost_breakdown = await bundle_service.calculate_usage_cost(user_id, data_used_mb)
        return cost_breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating cost: {str(e)}")


@router.get("/user/{user_id}/summary")
async def get_user_bundle_summary(user_id: str):
    """Get comprehensive bundle summary for user"""
    try:
        summary = await bundle_service.get_user_bundle_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")


@router.get("/user/{user_id}/packs")
async def get_user_packs(user_id: str, status: Optional[str] = None):
    """Get user's data packs"""
    try:
        from ..core.database import get_supabase_client
        supabase = get_supabase_client()
        query = supabase.table('data_packs').select('*').eq('user_id', user_id)
        if status:
            query = query.eq('status', status)
        response = query.execute()
        packs = response.data if response.data else []
        return {
            "packs": packs,
            "count": len(packs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user packs: {str(e)}")


@router.get("/user/{user_id}/usage-history")
async def get_usage_history(user_id: str, limit: int = 50):
    """Get user's data usage history"""
    try:
        from ..core.database import get_supabase_client
        
        response = get_supabase_client().table('usage_logs').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        usage_history = response.data
        
        return {
            "usage_history": usage_history,
            "count": len(usage_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting usage history: {str(e)}")