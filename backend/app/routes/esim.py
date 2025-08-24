"""
eSIM management routes
"""

import logging
import secrets
import string
import qrcode
import io
import base64
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, ESIM, ESIMStatus
from routes.auth import get_current_user
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class ESIMCreate(BaseModel):
    apn: str = "internet"
    username: Optional[str] = None
    password: Optional[str] = None

class ESIMResponse(BaseModel):
    id: int
    iccid: str
    imsi: str
    msisdn: Optional[str]
    activation_code: str
    status: str
    activated_at: Optional[datetime]
    created_at: datetime
    apn: str
    username: Optional[str]
    
    class Config:
        from_attributes = True

class ESIMQRCode(BaseModel):
    qr_code_data: str
    qr_code_image: str  # Base64 encoded PNG image
    activation_code: str
    manual_config: dict

class ESIMActivation(BaseModel):
    activation_code: str

# Helper functions
def generate_iccid() -> str:
    """Generate a random ICCID (SIM card identifier)"""
    # ICCID format: 89 + country code (2) + issuer identifier (2-4) + account identification (11-12) + check digit
    return "89" + "".join(secrets.choice(string.digits) for _ in range(18))

def generate_imsi() -> str:
    """Generate a random IMSI (International Mobile Subscriber Identity)"""
    # IMSI format: MCC (3) + MNC (2-3) + MSIN (9-10)
    return "310" + "".join(secrets.choice(string.digits) for _ in range(12))

def generate_msisdn() -> str:
    """Generate a random MSISDN (Mobile phone number)"""
    # US format: +1 + 10 digits
    return "+1" + "".join(secrets.choice(string.digits) for _ in range(10))

def generate_activation_code() -> str:
    """Generate activation code"""
    return "KSWIFI" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))

def generate_qr_code_data(esim: ESIM) -> str:
    """Generate QR code data for eSIM activation"""
    # LPA:1$ format for eSIM activation
    return f"LPA:1$rsp-prod.kswifi.com${esim.activation_code}$kswifi.com"

def create_qr_code_image(qr_data: str) -> str:
    """Create QR code image and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=settings.ESIM_QR_CODE_SIZE,
        border=settings.ESIM_QR_CODE_BORDER,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

# eSIM routes
@router.get("/", response_model=List[ESIMResponse])
async def get_user_esims(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all eSIMs for current user"""
    try:
        esims = db.query(ESIM).filter(
            ESIM.user_id == current_user.id
        ).order_by(ESIM.created_at.desc()).all()
        
        return [ESIMResponse.from_orm(esim) for esim in esims]
        
    except Exception as e:
        logger.error(f"Failed to get eSIMs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve eSIMs"
        )

@router.post("/", response_model=ESIMResponse, status_code=status.HTTP_201_CREATED)
async def create_esim(
    esim_data: ESIMCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new eSIM for user"""
    try:
        # Generate eSIM identifiers
        iccid = generate_iccid()
        imsi = generate_imsi()
        msisdn = generate_msisdn()
        activation_code = generate_activation_code()
        
        # Ensure uniqueness
        while db.query(ESIM).filter(ESIM.iccid == iccid).first():
            iccid = generate_iccid()
        
        while db.query(ESIM).filter(ESIM.imsi == imsi).first():
            imsi = generate_imsi()
        
        while db.query(ESIM).filter(ESIM.activation_code == activation_code).first():
            activation_code = generate_activation_code()
        
        # Create eSIM
        esim = ESIM(
            user_id=current_user.id,
            iccid=iccid,
            imsi=imsi,
            msisdn=msisdn,
            activation_code=activation_code,
            qr_code_data=generate_qr_code_data_placeholder(activation_code),
            status=ESIMStatus.PENDING.value,
            apn=esim_data.apn,
            username=esim_data.username,
            password=esim_data.password
        )
        
        # Generate QR code data
        esim.qr_code_data = generate_qr_code_data(esim)
        
        db.add(esim)
        db.commit()
        db.refresh(esim)
        
        logger.info(f"eSIM created for user {current_user.id}: {esim.iccid}")
        
        return ESIMResponse.from_orm(esim)
        
    except Exception as e:
        logger.error(f"Failed to create eSIM: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create eSIM"
        )

def generate_qr_code_data_placeholder(activation_code: str) -> str:
    """Generate placeholder QR code data"""
    return f"LPA:1$rsp-prod.kswifi.com${activation_code}$kswifi.com"

@router.get("/{esim_id}", response_model=ESIMResponse)
async def get_esim(
    esim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific eSIM by ID"""
    try:
        esim = db.query(ESIM).filter(
            ESIM.id == esim_id,
            ESIM.user_id == current_user.id
        ).first()
        
        if not esim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eSIM not found"
            )
        
        return ESIMResponse.from_orm(esim)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get eSIM: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve eSIM"
        )

@router.get("/{esim_id}/qr-code", response_model=ESIMQRCode)
async def get_esim_qr_code(
    esim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get eSIM QR code for activation"""
    try:
        esim = db.query(ESIM).filter(
            ESIM.id == esim_id,
            ESIM.user_id == current_user.id
        ).first()
        
        if not esim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eSIM not found"
            )
        
        # Generate QR code image
        qr_image = create_qr_code_image(esim.qr_code_data)
        
        # Prepare manual configuration
        manual_config = {
            "activation_code": esim.activation_code,
            "sm_dp_address": "rsp-prod.kswifi.com",
            "apn": esim.apn,
            "username": esim.username,
            "password": esim.password,
            "instructions": [
                "1. Go to Settings > Cellular/Mobile Data",
                "2. Tap 'Add Cellular Plan'",
                "3. Enter the activation code manually",
                "4. Follow the prompts to complete setup"
            ]
        }
        
        return ESIMQRCode(
            qr_code_data=esim.qr_code_data,
            qr_code_image=qr_image,
            activation_code=esim.activation_code,
            manual_config=manual_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate QR code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code"
        )

@router.post("/{esim_id}/activate", response_model=ESIMResponse)
async def activate_esim(
    esim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate an eSIM"""
    try:
        esim = db.query(ESIM).filter(
            ESIM.id == esim_id,
            ESIM.user_id == current_user.id
        ).first()
        
        if not esim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eSIM not found"
            )
        
        if esim.status == ESIMStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eSIM is already active"
            )
        
        if esim.status == ESIMStatus.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eSIM has been cancelled"
            )
        
        # Activate eSIM
        esim.status = ESIMStatus.ACTIVE.value
        esim.activated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(esim)
        
        logger.info(f"eSIM activated: {esim.iccid}")
        
        return ESIMResponse.from_orm(esim)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate eSIM: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate eSIM"
        )

@router.post("/{esim_id}/suspend")
async def suspend_esim(
    esim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suspend an eSIM"""
    try:
        esim = db.query(ESIM).filter(
            ESIM.id == esim_id,
            ESIM.user_id == current_user.id
        ).first()
        
        if not esim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eSIM not found"
            )
        
        if esim.status != ESIMStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active eSIMs can be suspended"
            )
        
        # Suspend eSIM
        esim.status = ESIMStatus.SUSPENDED.value
        db.commit()
        
        logger.info(f"eSIM suspended: {esim.iccid}")
        
        return {"detail": "eSIM suspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend eSIM: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend eSIM"
        )

@router.delete("/{esim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_esim(
    esim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an eSIM (soft delete)"""
    try:
        esim = db.query(ESIM).filter(
            ESIM.id == esim_id,
            ESIM.user_id == current_user.id
        ).first()
        
        if not esim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eSIM not found"
            )
        
        # Cancel eSIM
        esim.status = ESIMStatus.CANCELLED.value
        db.commit()
        
        logger.info(f"eSIM cancelled: {esim.iccid}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel eSIM: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel eSIM"
        )
