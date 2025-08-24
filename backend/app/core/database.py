"""
Database configuration and Supabase integration
"""

import asyncpg
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import settings


class Base(DeclarativeBase):
    """Base model for SQLAlchemy"""
    pass


# Initialize database connections safely
supabase: Client = None
engine = None

def init_connections():
    """Initialize database connections when settings are available"""
    global supabase, engine
    
    try:
        # Supabase client for auth and real-time features
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Async SQLAlchemy engine for direct database operations
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    except Exception as e:
        # Use mock connections for development
        print(f"Database connection failed: {e}")
        supabase = None
        engine = None

# Async session factory (will be initialized when engine is ready)
AsyncSessionLocal = None

def init_session_factory():
    """Initialize session factory when engine is ready"""
    global AsyncSessionLocal
    if engine:
        AsyncSessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=AsyncSession,
        )


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session
    """
    if not AsyncSessionLocal:
        raise Exception("Database not initialized. Call init_connections() first.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (if needed)"""
    if not engine:
        print("Database engine not available. Skipping table creation.")
        return
        
    # Note: We'll primarily use Supabase migrations
    # This is just for any additional tables if needed
    async with engine.begin() as conn:
        # Import models here to ensure they're registered
        from ..models import *  # noqa
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    if engine:
        await engine.dispose()


# Direct Supabase operations for convenience
class SupabaseClient:
    """Wrapper for common Supabase operations"""
    
    def __init__(self):
        self.client = supabase
    
    def _ensure_client(self):
        """Ensure Supabase client is available"""
        if not self.client:
            raise Exception("Supabase client not initialized. Set up environment variables first.")
    
    async def get_user_by_id(self, user_id: str):
        """Get user profile from Supabase"""
        self._ensure_client()
        response = self.client.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    async def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        self._ensure_client()
        from datetime import datetime
        self.client.table('users').update({
            'last_login': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()
    
    async def get_user_data_packs(self, user_id: str, status: str = None):
        """Get user's data packs"""
        self._ensure_client()
        query = self.client.table('data_packs').select('*').eq('user_id', user_id)
        if status:
            query = query.eq('status', status)
        response = query.execute()
        return response.data
    
    async def update_data_pack_usage(self, pack_id: str, used_mb: float, remaining_mb: float, status: str = None):
        """Update data pack usage"""
        self._ensure_client()
        update_data = {
            'used_data_mb': used_mb,
            'remaining_data_mb': remaining_mb
        }
        if status:
            update_data['status'] = status
            
        self.client.table('data_packs').update(update_data).eq('id', pack_id).execute()
    
    async def log_data_usage(self, user_id: str, pack_id: str, data_used_mb: float, **kwargs):
        """Log data usage"""
        self._ensure_client()
        log_data = {
            'user_id': user_id,
            'data_pack_id': pack_id,
            'data_used_mb': data_used_mb,
            **kwargs
        }
        self.client.table('usage_logs').insert(log_data).execute()
    
    async def get_user_esims(self, user_id: str):
        """Get user's eSIMs"""
        self._ensure_client()
        response = self.client.table('esims').select('*').eq('user_id', user_id).execute()
        return response.data
    
    async def update_esim_status(self, esim_id: str, status: str, **kwargs):
        """Update eSIM status"""
        self._ensure_client()
        update_data = {'status': status, **kwargs}
        self.client.table('esims').update(update_data).eq('id', esim_id).execute()


# Global Supabase client instance
supabase_client = SupabaseClient()