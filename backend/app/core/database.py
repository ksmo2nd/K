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


# Production database connections - PUT YOUR REAL CREDENTIALS IN .env FILE
# Supabase client for auth and real-time features
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Async SQLAlchemy engine for direct database operations
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Async session factory
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
    # Note: We'll primarily use Supabase migrations
    # This is just for any additional tables if needed
    async with engine.begin() as conn:
        # Import models here to ensure they're registered
        from ..models import *  # noqa
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()


# Direct Supabase operations for convenience
class SupabaseClient:
    """Wrapper for common Supabase operations"""
    
    def __init__(self):
        self.client = supabase
    
    async def get_user_by_id(self, user_id: str):
        """Get user profile from Supabase"""
        response = self.client.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    async def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        from datetime import datetime
        self.client.table('users').update({
            'last_login': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()
    
    async def get_user_data_packs(self, user_id: str, status: str = None):
        """Get user's data packs"""
        query = self.client.table('data_packs').select('*').eq('user_id', user_id)
        if status:
            query = query.eq('status', status)
        response = query.execute()
        return response.data
    
    async def update_data_pack_usage(self, pack_id: str, used_mb: float, remaining_mb: float, status: str = None):
        """Update data pack usage"""
        update_data = {
            'used_data_mb': used_mb,
            'remaining_data_mb': remaining_mb
        }
        if status:
            update_data['status'] = status
            
        self.client.table('data_packs').update(update_data).eq('id', pack_id).execute()
    
    async def log_data_usage(self, user_id: str, pack_id: str, data_used_mb: float, **kwargs):
        """Log data usage"""
        log_data = {
            'user_id': user_id,
            'data_pack_id': pack_id,
            'data_used_mb': data_used_mb,
            **kwargs
        }
        self.client.table('usage_logs').insert(log_data).execute()
    
    async def get_user_esims(self, user_id: str):
        """Get user's eSIMs"""
        response = self.client.table('esims').select('*').eq('user_id', user_id).execute()
        return response.data
    
    async def update_esim_status(self, esim_id: str, status: str, **kwargs):
        """Update eSIM status"""
        update_data = {'status': status, **kwargs}
        self.client.table('esims').update(update_data).eq('id', esim_id).execute()


# Global Supabase client instance
supabase_client = SupabaseClient()