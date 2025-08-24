"""
Authentication routes for user management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from database import get_db
from models import User, UserStatus
from auth import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, validate_password_strength
)

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError('Password must be at least 8 characters long and contain both letters and numbers')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    status: str
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError('Password must be at least 8 characters long and contain both letters and numbers')
        return v

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Authentication routes
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create new user account"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number,
            status=UserStatus.ACTIVE.value
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(db_user.id)})
        
        logger.info(f"User created successfully: {user_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours in seconds
            user=UserResponse.from_orm(db_user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_credentials.email).first()
        
        if not user or not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is suspended or deleted"
            )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"User logged in successfully: {user_credentials.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours in seconds
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse.from_orm(current_user)

@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"detail": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    logger.info(f"User logged out: {current_user.email}")
    return {"detail": "Successfully logged out"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    try:
        # Create new access token
        access_token = create_access_token(data={"sub": str(current_user.id)})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours in seconds
            user=UserResponse.from_orm(current_user)
        )
        
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )
