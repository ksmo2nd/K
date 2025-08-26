"""
Authentication utilities for FastAPI backend
"""
import jwt
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings
from .database import get_supabase_client
import structlog

logger = structlog.get_logger(__name__)
security = HTTPBearer()

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token from Authorization header
    Returns the decoded token payload
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # For Supabase tokens, we can verify using Supabase client
        # or decode directly with the JWT secret
        try:
            # Try to get user from Supabase using the token
            supabase = get_supabase_client()
            user_response = supabase.auth.get_user(token)
            if user_response.user:
                return {
                    "user_id": user_response.user.id,
                    "email": user_response.user.email,
                    "token": token
                }
        except Exception as supabase_error:
            logger.warning(f"Supabase token verification failed: {supabase_error}")
            
        # Fallback to manual JWT verification
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(token_data: dict = Depends(verify_jwt_token)) -> str:
    """
    Extract user ID from verified token data
    """
    user_id = token_data.get("user_id") or token_data.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not extract user ID from token"
        )
    
    return user_id

async def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[str]:
    """
    Get user ID if token is provided, otherwise return None
    Used for endpoints that work with both authenticated and anonymous users
    """
    if not credentials:
        return None
    
    try:
        token_data = await verify_jwt_token(credentials)
        return await get_current_user_id(token_data)
    except HTTPException:
        return None

# PUT YOUR REAL JWT SECRET AND SUPABASE CONFIGURATION IN .env FILE
# This module handles authentication using Supabase JWT tokens
# Make sure your SUPABASE_KEY and SECRET_KEY are properly configured