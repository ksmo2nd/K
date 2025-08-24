"""
Data pack activation routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import structlog

from ..services.bundle_service import BundleService
from ..services.esim_service import ESIMService
from ..core.auth import get_current_user_id

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/activation", tags=["activation"])

# Initialize services
bundle_service = BundleService()
esim_service = ESIMService()


@router.get("/packs/available")
async def get_activatable_packs(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get data packs that can be activated"""
    try:
        packs = await bundle_service.get_activatable_packs(user_id)
        return {
            "packs": packs,
            "count": len(packs)
        }
    except Exception as e:
        logger.error(f"Error getting activatable packs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packs/active")
async def get_active_pack(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get currently active data pack"""
    try:
        active_pack = await bundle_service.get_active_pack(user_id)
        return {
            "active_pack": active_pack,
            "has_active_pack": active_pack is not None
        }
    except Exception as e:
        logger.error(f"Error getting active pack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/packs/{pack_id}/activate")
async def activate_data_pack(
    pack_id: str,
    esim_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Activate a purchased data pack"""
    try:
        result = await bundle_service.activate_data_pack(user_id, pack_id, esim_id)
        
        # If eSIM is linked, also activate it with the provider
        if esim_id:
            try:
                await esim_service.activate_esim(esim_id)
                result['esim_activated'] = True
            except Exception as esim_error:
                logger.warning(f"Failed to activate eSIM with provider: {esim_error}")
                result['esim_activated'] = False
                result['esim_error'] = str(esim_error)
        
        return result
    except Exception as e:
        logger.error(f"Error activating data pack: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/packs/{pack_id}/deactivate")
async def deactivate_data_pack(
    pack_id: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Deactivate a data pack"""
    try:
        result = await bundle_service.deactivate_data_pack(user_id, pack_id)
        return result
    except Exception as e:
        logger.error(f"Error deactivating data pack: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/esims/available")
async def get_user_esims(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get user's eSIMs for activation"""
    try:
        # This would need to be implemented in esim_service
        # For now, return a placeholder
        return {
            "esims": [],
            "count": 0,
            "message": "eSIM management coming soon"
        }
    except Exception as e:
        logger.error(f"Error getting user eSIMs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/esims/provision")
async def provision_new_esim(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Provision a new eSIM for the user"""
    try:
        # Provision eSIM with default bundle size (will be linked to data pack later)
        result = await esim_service.provision_esim(user_id, 1024)  # 1GB default
        return result
    except Exception as e:
        logger.error(f"Error provisioning eSIM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_activation_status(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get overall activation status for user"""
    try:
        active_pack = await bundle_service.get_active_pack(user_id)
        activatable_packs = await bundle_service.get_activatable_packs(user_id)
        
        return {
            "has_active_pack": active_pack is not None,
            "active_pack": active_pack,
            "available_packs_count": len(activatable_packs),
            "available_packs": activatable_packs,
            "can_activate": len(activatable_packs) > 0,
            "requires_wifi_for_purchase": True,
            "activation_available_offline": True
        }
    except Exception as e:
        logger.error(f"Error getting activation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))