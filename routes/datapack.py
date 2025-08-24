"""
Data pack management routes
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from database import get_db
from models import User, DataPack, DataPackStatus, UsageLog
from routes.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class DataPackCreate(BaseModel):
    name: str
    total_data_mb: float
    price: float
    currency: str = "USD"
    expires_at: datetime
    
    @validator('total_data_mb')
    def validate_data_amount(cls, v):
        if v <= 0:
            raise ValueError('Data amount must be positive')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

class DataPackResponse(BaseModel):
    id: int
    name: str
    total_data_mb: float
    used_data_mb: float
    remaining_data_mb: float
    price: float
    currency: str
    status: str
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class DataUsage(BaseModel):
    data_used_mb: float
    session_duration: Optional[int] = None
    location: Optional[str] = None
    device_info: Optional[str] = None
    
    @validator('data_used_mb')
    def validate_data_used(cls, v):
        if v <= 0:
            raise ValueError('Data used must be positive')
        return v

class UsageLogResponse(BaseModel):
    id: int
    data_pack_id: int
    data_used_mb: float
    session_duration: Optional[int]
    ip_address: Optional[str]
    location: Optional[str]
    device_info: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class DataPackStats(BaseModel):
    total_packs: int
    active_packs: int
    total_data_mb: float
    used_data_mb: float
    remaining_data_mb: float
    total_spent: float

# Data pack routes
@router.get("/", response_model=List[DataPackResponse])
async def get_user_data_packs(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all data packs for current user"""
    try:
        query = db.query(DataPack).filter(DataPack.user_id == current_user.id)
        
        if status_filter:
            query = query.filter(DataPack.status == status_filter)
        
        data_packs = query.order_by(DataPack.created_at.desc()).all()
        
        return [DataPackResponse.from_orm(pack) for pack in data_packs]
        
    except Exception as e:
        logger.error(f"Failed to get data packs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data packs"
        )

@router.post("/", response_model=DataPackResponse, status_code=status.HTTP_201_CREATED)
async def create_data_pack(
    pack_data: DataPackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new data pack for user"""
    try:
        # Create new data pack
        data_pack = DataPack(
            user_id=current_user.id,
            name=pack_data.name,
            total_data_mb=pack_data.total_data_mb,
            remaining_data_mb=pack_data.total_data_mb,
            price=pack_data.price,
            currency=pack_data.currency,
            expires_at=pack_data.expires_at,
            status=DataPackStatus.ACTIVE.value
        )
        
        db.add(data_pack)
        db.commit()
        db.refresh(data_pack)
        
        logger.info(f"Data pack created for user {current_user.id}: {pack_data.name}")
        
        return DataPackResponse.from_orm(data_pack)
        
    except Exception as e:
        logger.error(f"Failed to create data pack: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create data pack"
        )

@router.get("/{pack_id}", response_model=DataPackResponse)
async def get_data_pack(
    pack_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific data pack by ID"""
    try:
        data_pack = db.query(DataPack).filter(
            DataPack.id == pack_id,
            DataPack.user_id == current_user.id
        ).first()
        
        if not data_pack:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data pack not found"
            )
        
        return DataPackResponse.from_orm(data_pack)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get data pack: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data pack"
        )

@router.post("/{pack_id}/usage", status_code=status.HTTP_201_CREATED)
async def record_data_usage(
    pack_id: int,
    usage_data: DataUsage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record data usage for a specific data pack"""
    try:
        # Find the data pack
        data_pack = db.query(DataPack).filter(
            DataPack.id == pack_id,
            DataPack.user_id == current_user.id,
            DataPack.status == DataPackStatus.ACTIVE.value
        ).first()
        
        if not data_pack:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active data pack not found"
            )
        
        # Check if pack has expired
        if data_pack.expires_at < datetime.now(timezone.utc):
            data_pack.status = DataPackStatus.EXPIRED.value
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data pack has expired"
            )
        
        # Check if there's enough data remaining
        if usage_data.data_used_mb > data_pack.remaining_data_mb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough data remaining in pack"
            )
        
        # Update data pack usage
        data_pack.used_data_mb += usage_data.data_used_mb
        data_pack.remaining_data_mb -= usage_data.data_used_mb
        
        # Check if pack is exhausted
        if data_pack.remaining_data_mb <= 0:
            data_pack.status = DataPackStatus.EXHAUSTED.value
        
        # Create usage log
        usage_log = UsageLog(
            user_id=current_user.id,
            data_pack_id=pack_id,
            data_used_mb=usage_data.data_used_mb,
            session_duration=usage_data.session_duration,
            location=usage_data.location,
            device_info=usage_data.device_info
        )
        
        db.add(usage_log)
        db.commit()
        
        logger.info(f"Data usage recorded for pack {pack_id}: {usage_data.data_used_mb}MB")
        
        return {
            "detail": "Usage recorded successfully",
            "remaining_data_mb": data_pack.remaining_data_mb,
            "status": data_pack.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record data usage: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record data usage"
        )

@router.get("/{pack_id}/usage", response_model=List[UsageLogResponse])
async def get_data_pack_usage(
    pack_id: int,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage history for a specific data pack"""
    try:
        # Verify pack ownership
        data_pack = db.query(DataPack).filter(
            DataPack.id == pack_id,
            DataPack.user_id == current_user.id
        ).first()
        
        if not data_pack:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data pack not found"
            )
        
        # Get usage logs
        usage_logs = db.query(UsageLog).filter(
            UsageLog.data_pack_id == pack_id
        ).order_by(UsageLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return [UsageLogResponse.from_orm(log) for log in usage_logs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage history"
        )

@router.get("/stats/summary", response_model=DataPackStats)
async def get_data_pack_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data pack statistics for current user"""
    try:
        # Get all data packs for user
        data_packs = db.query(DataPack).filter(DataPack.user_id == current_user.id).all()
        
        if not data_packs:
            return DataPackStats(
                total_packs=0,
                active_packs=0,
                total_data_mb=0.0,
                used_data_mb=0.0,
                remaining_data_mb=0.0,
                total_spent=0.0
            )
        
        # Calculate statistics
        total_packs = len(data_packs)
        active_packs = len([p for p in data_packs if p.status == DataPackStatus.ACTIVE.value])
        total_data_mb = sum(p.total_data_mb for p in data_packs)
        used_data_mb = sum(p.used_data_mb for p in data_packs)
        remaining_data_mb = sum(p.remaining_data_mb for p in data_packs)
        total_spent = sum(p.price for p in data_packs)
        
        return DataPackStats(
            total_packs=total_packs,
            active_packs=active_packs,
            total_data_mb=total_data_mb,
            used_data_mb=used_data_mb,
            remaining_data_mb=remaining_data_mb,
            total_spent=total_spent
        )
        
    except Exception as e:
        logger.error(f"Failed to get data pack statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_data_pack(
    pack_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a data pack (soft delete)"""
    try:
        data_pack = db.query(DataPack).filter(
            DataPack.id == pack_id,
            DataPack.user_id == current_user.id
        ).first()
        
        if not data_pack:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data pack not found"
            )
        
        # Update status instead of deleting
        data_pack.status = DataPackStatus.EXPIRED.value
        db.commit()
        
        logger.info(f"Data pack {pack_id} deactivated by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate data pack: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate data pack"
        )
