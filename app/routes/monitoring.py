"""
Monitoring and background task routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.monitoring_service import MonitoringService

router = APIRouter()
monitoring_service = MonitoringService()


class ManualDataSyncRequest(BaseModel):
    user_id: str


@router.get("/stats")
async def get_monitoring_stats():
    """Get monitoring service statistics"""
    try:
        stats = await monitoring_service.get_monitoring_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitoring stats: {str(e)}")


@router.post("/start")
async def start_monitoring():
    """Start the background monitoring service"""
    try:
        if monitoring_service._running:
            return {"status": "already_running", "message": "Monitoring service is already running"}
        
        # Start monitoring in the background
        import asyncio
        asyncio.create_task(monitoring_service.start_monitoring())
        
        return {"status": "started", "message": "Monitoring service started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")


@router.post("/stop")
async def stop_monitoring():
    """Stop the background monitoring service"""
    try:
        await monitoring_service.stop_monitoring()
        return {"status": "stopped", "message": "Monitoring service stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping monitoring: {str(e)}")


@router.post("/sync/user")
async def manual_user_sync(request: ManualDataSyncRequest):
    """Manually trigger data sync for a specific user"""
    try:
        await monitoring_service._sync_user_provider_data(request.user_id)
        return {"status": "success", "message": f"Data sync completed for user {request.user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing user data: {str(e)}")


@router.post("/check/usage")
async def manual_usage_check():
    """Manually trigger usage check for all active packs"""
    try:
        from ..core.database import get_supabase_client
        from ..models.enums import DataPackStatus
        
        # Get all active packs
        response = get_supabase_client().table('data_packs').select('*').eq('status', DataPackStatus.ACTIVE.value).execute()
        active_packs = response.data
        
        checked_count = 0
        for pack in active_packs:
            await monitoring_service._check_pack_usage(pack)
            checked_count += 1
        
        return {
            "status": "success", 
            "message": f"Manual usage check completed for {checked_count} packs"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in manual usage check: {str(e)}")


@router.post("/cleanup/expired")
async def manual_cleanup_expired():
    """Manually trigger cleanup of expired packs"""
    try:
        from ..core.database import get_supabase_client
        from ..models.enums import DataPackStatus
        from datetime import datetime
        
        # Find expired packs
        current_time = datetime.utcnow().isoformat()
        response = get_supabase_client().table('data_packs').select('*').eq('status', DataPackStatus.ACTIVE.value).lt('expires_at', current_time).execute()
        expired_packs = response.data
        
        for pack in expired_packs:
            await monitoring_service._expire_data_pack(pack['id'])
        
        return {
            "status": "success",
            "message": f"Cleaned up {len(expired_packs)} expired packs"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in cleanup: {str(e)}")


@router.get("/health")
async def monitoring_health():
    """Health check for monitoring service"""
    try:
        stats = await monitoring_service.get_monitoring_stats()
        
        # Determine health status
        is_healthy = stats.get('service_running', False) and 'error' not in stats
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service_running": stats.get('service_running', False),
            "details": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }