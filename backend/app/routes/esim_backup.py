"""
eSIM management routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import secrets
import string
from datetime import datetime, timedelta

from ..services.esim_service import ESIMService
from ..core.auth import get_current_user_id
from ..core.database import get_supabase_client

router = APIRouter()
esim_service = ESIMService()


class ProvisionESIMRequest(BaseModel):
    user_id: str
    bundle_size_mb: int


class ESIMConfigRequest(BaseModel):
    apn: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class GenerateESIMRequest(BaseModel):
    session_id: Optional[str] = None
    data_pack_size_mb: Optional[int] = 1024  # Default 1GB
    carrier_name: str = "KSWiFi"
    carrier_plmn: str = "99999"  # Custom PLMN for KSWiFi


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
        from ..core.database import get_supabase_client
        
        # Get eSIM details
        esim_response = get_supabase_client().table('esims').select('id, user_id, iccid, status').eq('id', esim_id).execute()
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


@router.post("/generate")
async def generate_esim_qr_code(request: GenerateESIMRequest):
    """Generate eSIM QR code for a session or data pack"""
    try:
        print(f"🔍 GENERATE QR: Request received - session_id: {request.session_id}, size: {request.data_pack_size_mb}MB")
        
        # If session_id provided, get the session details
        if request.session_id:
            print(f"🔍 GENERATE QR: Looking up session {request.session_id}")
            supabase = get_supabase_client()
            
            # Get session record
            session_response = supabase.table('internet_sessions')\
                .select('*')\
                .eq('id', request.session_id)\
                .single()\
                .execute()
            
            if not session_response.data:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = session_response.data
            user_id = session['user_id']
            bundle_size_mb = session['data_mb']
            
            print(f"🔍 GENERATE QR: Session found - user: {user_id}, size: {bundle_size_mb}MB")
            
            # Check if eSIM already exists for this session
            if session.get('esim_id'):
                print(f"🔍 GENERATE QR: eSIM already exists, returning existing QR code")
                # Return existing eSIM QR code
                esim_response = supabase.table('esims')\
                    .select('*')\
                    .eq('id', session['esim_id'])\
                    .single()\
                    .execute()
                
                if esim_response.data:
                    esim = esim_response.data
                    qr_image = esim_service._generate_qr_code(esim['activation_code'])
                    
                    return {
                        'success': True,
                        'esim_id': esim['id'],
                        'session_id': request.session_id,
                        'qr_code_image': qr_image,
                        'activation_code': esim['activation_code'],
                        'bundle_size_mb': bundle_size_mb,
                        'status': 'ready_for_activation',
                        'manual_setup': {
                            'activation_code': esim['activation_code'],
                            'apn': esim['apn'],
                            'username': esim['username'],
                            'password': esim['password'],
                            'instructions': [
                                "1. Scan the QR code with your device camera",
                                "2. Follow the prompts to add the cellular plan", 
                                "3. Enable the new cellular plan for data",
                                "4. You can now browse the internet using your downloaded data"
                            ]
                        }
                    }
        else:
            # Generate for standalone data pack
            user_id = "anonymous_user"  # For demo purposes
            bundle_size_mb = request.data_pack_size_mb
            
        print(f"🔍 GENERATE QR: Provisioning new eSIM for user {user_id}")
        
        # Provision new eSIM
        esim_result = await esim_service.provision_esim(
            user_id=user_id,
            bundle_size_mb=bundle_size_mb
        )
        
        print(f"🔍 GENERATE QR: eSIM provisioned successfully - ID: {esim_result['esim_id']}")
        
        # Update session with eSIM ID if session_id provided
        if request.session_id:
            print(f"🔍 GENERATE QR: Linking eSIM to session {request.session_id}")
            supabase.table('internet_sessions')\
                .update({'esim_id': esim_result['esim_id']})\
                .eq('id', request.session_id)\
                .execute()
        
        return {
            'success': True,
            'esim_id': esim_result['esim_id'],
            'session_id': request.session_id,
            'qr_code_image': esim_result['qr_code_image'],
            'activation_code': esim_result['activation_code'],
            'bundle_size_mb': bundle_size_mb,
            'status': esim_result['status'],
            'manual_setup': esim_result['manual_setup'],
            'message': 'eSIM QR code generated successfully! Scan with your device to activate.'
        }
        
    except Exception as e:
        print(f"❌ GENERATE QR ERROR: {str(e)}")
        import traceback
        print(f"❌ GENERATE QR TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating eSIM QR code: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_esims(user_id: str):
    """Get all eSIMs for a user"""
    try:
        supabase = get_supabase_client()
        response = supabase.table('esims').select('id, iccid, status').eq('user_id', user_id).execute()
        esims = response.data if response.data else []
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
        from ..core.database import get_supabase_client
        
        update_data = {}
        if config.apn:
            update_data['apn'] = config.apn
        if config.username:
            update_data['username'] = config.username
        if config.password:
            update_data['password'] = config.password
        
        if update_data:
            get_supabase_client().table('esims').update(update_data).eq('id', esim_id).execute()
        
        return {"status": "success", "message": "eSIM configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating eSIM config: {str(e)}")


@router.get("/{esim_id}/status")
async def get_esim_status(esim_id: str):
    """Get detailed status of an eSIM"""
    try:
        from ..core.database import get_supabase_client
        
        # Get eSIM details
        esim_response = get_supabase_client().table('esims').select('id, user_id, iccid, status').eq('id', esim_id).execute()
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


@router.post("/generate-esim")
async def generate_esim(
    request: GenerateESIMRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Generate WiFi QR code for session access - redirected from old eSIM endpoint
    """
    try:
        print(f"🔍 ESIM->WIFI REDIRECT: Generating WiFi QR for session {request.session_id}")
        
        # Import WiFi service
        from ..services.wifi_captive_service import WiFiCaptiveService
        wifi_service = WiFiCaptiveService()
        
        # Generate WiFi QR code instead of eSIM
        result = await wifi_service.create_wifi_access_token(
            user_id=current_user_id,
            session_id=request.session_id,
            data_limit_mb=request.bundle_size_mb
        )
        
        if result["success"]:
            # Generate the actual QR code image
            qr_image = wifi_service.generate_wifi_qr_code(result["wifi_qr_data"])
            
            print(f"🔍 WIFI QR GENERATED: network={result['network_name']}, qr_length={len(qr_image)}")
            
            # Return in eSIM format for frontend compatibility
            return {
                "success": True,
                "data": {
                    "esim_id": result["token_id"],
                    "qr_code": qr_image,  # This is the actual WiFi QR code
                    "qr_data": result["wifi_qr_data"],
                    "network_name": result["network_name"],
                    "wifi_security": result["wifi_security"],
                    "activation_instructions": [
                        "1. Scan this QR code with your device camera",
                        "2. Your device will automatically connect to WiFi",
                        "3. Start browsing the internet immediately",
                        "4. No additional setup required"
                    ],
                    "session_id": request.session_id,
                    "data_limit_mb": request.bundle_size_mb,
                    "access_type": "wifi_qr"
                }
            }
        else:
            raise Exception("Failed to generate WiFi QR code")
            
    except Exception as e:
        print(f"❌ ESIM->WIFI QR ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Old eSIM code removed - now using WiFi QR system
        esim_id = str(uuid.uuid4())
        
        # Generate ICCID (Integrated Circuit Card Identifier) - 19-20 digits
        # Format: 89 (telecom) + 999 (KSWiFi country code) + 99 (issuer) + 12-digit serial + check digit
        iccid_base = f"89999991{secrets.randbelow(10**12):012d}"
        # Simple Luhn check digit calculation
        iccid = iccid_base + str(_calculate_luhn_check_digit(iccid_base))
        
        # Generate IMSI (International Mobile Subscriber Identity) - 15 digits
        # Format: MCC (999) + MNC (99) + MSIN (10 digits) for KSWiFi virtual network
        imsi = f"99999{secrets.randbelow(10**10):010d}"
        
        # Generate activation code (32-character unique identifier)
        activation_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(32))
        
        # Create eSIM profile data (LPA format for installable eSIM)
        # This is a simplified profile that mobile OS can recognize as a valid eSIM
        esim_profile_data = {
            "eid": f"89999{secrets.randbelow(10**27):027d}",  # eUICC Identifier
            "iccid": iccid,
            "imsi": imsi,
            "msisdn": None,  # NULL phone number as requested
            "carrier_name": request.carrier_name,
            "carrier_plmn": request.carrier_plmn,
            "apn": "kswifi.data",
            "authentication": "none",
            "profile_name": f"KSWiFi Data Pack",
            "profile_nickname": f"KSWiFi-{activation_code[:8]}",
            "activation_code": activation_code,
            "network_access_domain": "kswifi.network"
        }
        
        # Create LPA (Local Profile Assistant) format string for QR code
        # This follows eSIM specification format that mobile devices can install
        lpa_string = (
            f"LPA:1${request.carrier_plmn}.kswifi.co$"
            f"{activation_code}$"
            f"{request.carrier_name}"
        )
        
        # Generate QR code for eSIM installation
        qr_image_base64 = esim_service._generate_qr_code(lpa_string)
        
        # Store eSIM profile in Supabase
        esim_data = {
            "id": esim_id,
            "user_id": current_user_id,
            "iccid": iccid,
            "imsi": imsi,
            "msisdn": None,  # NULL phone number
            "activation_code": activation_code,
            "qr_code_data": lpa_string,
            "status": "pending",
            "apn": "kswifi.data",
            "username": None,
            "password": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert eSIM into database
        esim_response = get_supabase_client().table("esims").insert(esim_data).execute()
        
        if not esim_response.data:
            raise HTTPException(status_code=500, detail="Failed to store eSIM profile")
        
        # If session_id provided, link it to a data pack
        data_pack_id = None
        if request.session_id:
            # Create associated data pack for this eSIM
            data_pack_data = {
                "id": str(uuid.uuid4()),
                "user_id": current_user_id,
                "name": f"KSWiFi Data Pack - {request.data_pack_size_mb}MB",
                "data_mb": int(request.data_pack_size_mb),  # Use data_mb instead of total_data_mb
                "used_data_mb": 0,  # Matches schema
                # remaining_data_mb is GENERATED - don't include it
                "price_ngn": 0,  # Free for downloaded sessions
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            pack_response = get_supabase_client().table("data_packs").insert(data_pack_data).execute()
            if pack_response.data:
                data_pack_id = data_pack_data["id"]
        
        # Return eSIM profile and QR code for installation
        return {
            "success": True,
            "esim_id": esim_id,
            "iccid": iccid,
            "imsi": imsi,
            "carrier_name": request.carrier_name,
            "carrier_plmn": request.carrier_plmn,
            "activation_code": activation_code,
            "qr_code_data": lpa_string,
            "qr_code_image": qr_image_base64,
            "bundle_size_mb": int(request.data_pack_size_mb),
            "status": "provisioned",
            "data_pack_id": data_pack_id,
            "profile_data": esim_profile_data,
            "manual_setup": {
                "activation_code": activation_code,
                "apn": "kswifi.data",
                "username": "",
                "password": "",
                "instructions": [
                    "1. Open Settings on your device",
                    "2. Go to Cellular/Mobile Data",
                    "3. Tap 'Add eSIM'",
                    "4. Scan the QR code or enter activation code",
                    "5. Follow device prompts to install",
                    "6. KSWiFi network will appear in your carrier list"
                ]
            },
            "message": "eSIM profile generated successfully. Scan QR code to install on your device."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating eSIM: {str(e)}")


def _calculate_luhn_check_digit(number_string: str) -> int:
    """Calculate Luhn check digit for ICCID validation"""
    digits = [int(d) for d in number_string]
    for i in range(len(digits) - 1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return (10 - (sum(digits) % 10)) % 10