"""
Admin dashboard routes for monitoring and management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, DataPack, ESIM, UsageLog, AdminLog, UserStatus, DataPackStatus, ESIMStatus
from routes.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Admin middleware
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Pydantic models
class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_data_packs: int
    active_data_packs: int
    total_esims: int
    active_esims: int
    total_data_consumed_mb: float
    total_revenue: float

class UserSummary(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    status: str
    created_at: datetime
    last_login: Optional[datetime]
    total_data_packs: int
    total_data_consumed_mb: float
    total_spent: float
    
    class Config:
        from_attributes = True

class DataPackSummary(BaseModel):
    id: int
    user_id: int
    user_email: str
    name: str
    total_data_mb: float
    used_data_mb: float
    remaining_data_mb: float
    price: float
    status: str
    created_at: datetime
    expires_at: datetime

class UsageAnalytics(BaseModel):
    date: str
    total_usage_mb: float
    unique_users: int
    sessions: int

class AdminAction(BaseModel):
    action: str
    target_type: str
    target_id: int
    details: Optional[str] = None

class AdminLogEntry(BaseModel):
    id: int
    admin_email: str
    action: str
    target_type: str
    target_id: int
    details: Optional[str]
    timestamp: datetime

# Helper function to log admin actions
def log_admin_action(
    db: Session,
    admin_user_id: int,
    action: str,
    target_type: str,
    target_id: int,
    details: Optional[str] = None
):
    """Log admin action"""
    admin_log = AdminLog(
        admin_user_id=admin_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(admin_log)
    db.commit()

# Admin dashboard routes
@router.get("/stats", response_model=AdminStats)
async def get_admin_statistics(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    try:
        # User statistics
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(
            User.status == UserStatus.ACTIVE.value
        ).scalar()
        
        # Data pack statistics
        total_data_packs = db.query(func.count(DataPack.id)).scalar()
        active_data_packs = db.query(func.count(DataPack.id)).filter(
            DataPack.status == DataPackStatus.ACTIVE.value
        ).scalar()
        
        # eSIM statistics
        total_esims = db.query(func.count(ESIM.id)).scalar()
        active_esims = db.query(func.count(ESIM.id)).filter(
            ESIM.status == ESIMStatus.ACTIVE.value
        ).scalar()
        
        # Usage statistics
        total_data_consumed = db.query(func.sum(DataPack.used_data_mb)).scalar() or 0.0
        total_revenue = db.query(func.sum(DataPack.price)).scalar() or 0.0
        
        return AdminStats(
            total_users=total_users,
            active_users=active_users,
            total_data_packs=total_data_packs,
            active_data_packs=active_data_packs,
            total_esims=total_esims,
            active_esims=active_esims,
            total_data_consumed_mb=total_data_consumed,
            total_revenue=total_revenue
        )
        
    except Exception as e:
        logger.error(f"Failed to get admin statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.get("/users", response_model=List[UserSummary])
async def get_users_summary(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by user status"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get users summary for admin dashboard"""
    try:
        query = db.query(User)
        
        if status_filter:
            query = query.filter(User.status == status_filter)
        
        users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        
        user_summaries = []
        for user in users:
            # Get user statistics
            data_packs = db.query(DataPack).filter(DataPack.user_id == user.id).all()
            total_data_packs = len(data_packs)
            total_data_consumed = sum(pack.used_data_mb for pack in data_packs)
            total_spent = sum(pack.price for pack in data_packs)
            
            user_summaries.append(UserSummary(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                status=user.status,
                created_at=user.created_at,
                last_login=user.last_login,
                total_data_packs=total_data_packs,
                total_data_consumed_mb=total_data_consumed,
                total_spent=total_spent
            ))
        
        return user_summaries
        
    except Exception as e:
        logger.error(f"Failed to get users summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users summary"
        )

@router.get("/data-packs", response_model=List[DataPackSummary])
async def get_data_packs_summary(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by pack status"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get data packs summary for admin dashboard"""
    try:
        query = db.query(DataPack).join(User)
        
        if status_filter:
            query = query.filter(DataPack.status == status_filter)
        
        data_packs = query.order_by(desc(DataPack.created_at)).offset(offset).limit(limit).all()
        
        pack_summaries = []
        for pack in data_packs:
            pack_summaries.append(DataPackSummary(
                id=pack.id,
                user_id=pack.user_id,
                user_email=pack.user.email,
                name=pack.name,
                total_data_mb=pack.total_data_mb,
                used_data_mb=pack.used_data_mb,
                remaining_data_mb=pack.remaining_data_mb,
                price=pack.price,
                status=pack.status,
                created_at=pack.created_at,
                expires_at=pack.expires_at
            ))
        
        return pack_summaries
        
    except Exception as e:
        logger.error(f"Failed to get data packs summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data packs summary"
        )

@router.get("/usage-analytics", response_model=List[UsageAnalytics])
async def get_usage_analytics(
    days: int = Query(30, le=90, description="Number of days to analyze"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get usage analytics for admin dashboard"""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Query usage logs grouped by date
        results = db.query(
            func.date(UsageLog.timestamp).label('date'),
            func.sum(UsageLog.data_used_mb).label('total_usage_mb'),
            func.count(func.distinct(UsageLog.user_id)).label('unique_users'),
            func.count(UsageLog.id).label('sessions')
        ).filter(
            UsageLog.timestamp >= start_date
        ).group_by(
            func.date(UsageLog.timestamp)
        ).order_by(
            func.date(UsageLog.timestamp)
        ).all()
        
        analytics = []
        for result in results:
            analytics.append(UsageAnalytics(
                date=result.date.strftime('%Y-%m-%d'),
                total_usage_mb=float(result.total_usage_mb or 0),
                unique_users=result.unique_users,
                sessions=result.sessions
            ))
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get usage analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Suspend a user account"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.status == UserStatus.SUSPENDED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already suspended"
            )
        
        # Suspend user
        user.status = UserStatus.SUSPENDED.value
        db.commit()
        
        # Log admin action
        log_admin_action(
            db, admin_user.id, "suspend_user", "user", user_id,
            f"User {user.email} suspended"
        )
        
        logger.info(f"User {user.email} suspended by admin {admin_user.email}")
        
        return {"detail": "User suspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )

@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Reactivate a suspended user account"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.status == UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        # Reactivate user
        user.status = UserStatus.ACTIVE.value
        db.commit()
        
        # Log admin action
        log_admin_action(
            db, admin_user.id, "reactivate_user", "user", user_id,
            f"User {user.email} reactivated"
        )
        
        logger.info(f"User {user.email} reactivated by admin {admin_user.email}")
        
        return {"detail": "User reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reactivate user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate user"
        )

@router.get("/logs", response_model=List[AdminLogEntry])
async def get_admin_logs(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin action logs"""
    try:
        logs = db.query(AdminLog).join(
            User, AdminLog.admin_user_id == User.id
        ).order_by(desc(AdminLog.timestamp)).offset(offset).limit(limit).all()
        
        log_entries = []
        for log in logs:
            log_entries.append(AdminLogEntry(
                id=log.id,
                admin_email=log.admin_user.email,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                details=log.details,
                timestamp=log.timestamp
            ))
        
        return log_entries
        
    except Exception as e:
        logger.error(f"Failed to get admin logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin logs"
        )
