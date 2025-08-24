"""
eSIM management routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.esim_service import ESIMService

router = APIRouter()
esim_service = ESIMService()


class ProvisionESIMRequest(BaseModel):
    user_id: str
    bundle_size_mb: int


class ESIMConfigRequest(BaseModel):
    apn: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


@router.post("/provision")
async def provision_esim(request: ProvisionESIMRequest):
    """Provision a new eSIM from the provider"""
    try:
        result = await esim_service.provision_esim(
            user_id=request.user_id,
            bundle_size_mb=request.bundle_size_mb
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error provisioning eSIM: {str(e)}")


@router.post("/{esim_id}/activate")
async def activate_esim(esim_id: str):
    """Activate an eSIM with the provider"""
    try:
        result = await esim_service.activate_esim(esim_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activating eSIM: {str(e)}")


@router.post("/{esim_id}/suspend")
async def suspend_esim(esim_id: str):
    """Suspend an eSIM with the provider"""
    try:
        result = await esim_service.suspend_esim(esim_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suspending eSIM: {str(e)}")


@router.get("/{esim_id}/usage")
async def get_esim_usage(esim_id: str):
    """Get current data usage for an eSIM"""
    try:
        usage_data = await esim_service.get_esim_usage(esim_id)
        return usage_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting eSIM usage: {str(e)}")


@router.get("/{esim_id}/qr-code")
async def get_esim_qr_code(esim_id: str):
    """Get QR code and setup information for an eSIM"""
    try:
        from ..core.database import supabase_client
        
        # Get eSIM details
        esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
        if not esim_response.data:
            raise HTTPException(status_code=404, detail="eSIM not found")
        
        esim = esim_response.data[0]
        
        # Generate QR code using the service
        qr_image = esim_service._generate_qr_code(esim['qr_code_data'])
        
        return {
            'esim_id': esim_id,
            'qr_code_data': esim['qr_code_data'],
            'qr_code_image': qr_image,
            'activation_code': esim['activation_code'],
            'manual_setup': {
                'sm_dp_address': 'sm-dp.kswifi.com',
                'activation_code': esim['activation_code'],
                'apn': esim['apn'],
                'username': esim['username'],
                'password': esim['password'],
                'instructions': [
                    'Open Settings on your device',
                    'Go to Cellular/Mobile Data',
                    'Add eSIM or Cellular Plan',
                    'Scan QR code or enter details manually',
                    'Follow the activation prompts',
                    'Your eSIM will be activated automatically'
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting QR code: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_esims(user_id: str):
    """Get all eSIMs for a user"""
    try:
        from ..core.database import supabase_client
        esims = await supabase_client.get_user_esims(user_id)
        return {
            "esims": esims,
            "count": len(esims)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user eSIMs: {str(e)}")


@router.put("/{esim_id}/config")
async def update_esim_config(esim_id: str, config: ESIMConfigRequest):
    """Update eSIM configuration"""
    try:
        from ..core.database import supabase_client
        
        update_data = {}
        if config.apn:
            update_data['apn'] = config.apn
        if config.username:
            update_data['username'] = config.username
        if config.password:
            update_data['password'] = config.password
        
        if update_data:
            supabase_client.client.table('esims').update(update_data).eq('id', esim_id).execute()
        
        return {"status": "success", "message": "eSIM configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating eSIM config: {str(e)}")


@router.get("/{esim_id}/status")
async def get_esim_status(esim_id: str):
    """Get detailed status of an eSIM"""
    try:
        from ..core.database import supabase_client
        
        # Get eSIM details
        esim_response = supabase_client.client.table('esims').select('*').eq('id', esim_id).execute()
        if not esim_response.data:
            raise HTTPException(status_code=404, detail="eSIM not found")
        
        esim = esim_response.data[0]
        
        # Get latest usage if available
        try:
            usage_data = await esim_service.get_esim_usage(esim_id)
        except:
            usage_data = None
        
        return {
            'esim_id': esim_id,
            'iccid': esim['iccid'],
            'status': esim['status'],
            'activated_at': esim.get('activated_at'),
            'created_at': esim['created_at'],
            'usage_data': usage_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting eSIM status: {str(e)}")