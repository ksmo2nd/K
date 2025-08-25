"""
Database configuration and Supabase integration
Connects to Supabase PostgreSQL using DATABASE_URL environment variable
"""

import asyncpg
import logging
from urllib.parse import urlparse
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base model for SQLAlchemy"""
    pass


def create_database_url() -> str:
    """
    Create database URL compatible with asyncpg from Supabase DATABASE_URL
    Converts postgresql:// to postgresql+asyncpg:// for SQLAlchemy async support
    Removes sslmode query parameter (handled via connect_args instead)
    """
    db_url = settings.DATABASE_URL
    
    # Parse the URL to validate format
    parsed = urlparse(db_url)
    
    if not parsed.scheme.startswith('postgresql'):
        raise ValueError(f"Invalid DATABASE_URL scheme: {parsed.scheme}. Must start with 'postgresql'")
    
    # Convert to asyncpg driver for SQLAlchemy async support
    if not db_url.startswith('postgresql+asyncpg://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    # Handle Supabase-specific query parameters
    # Keep pgbouncer=true but remove sslmode (handled via connect_args)
    if '?' in db_url:
        base_url, query_string = db_url.split('?', 1)
        query_params = []
        
        # Parse existing query parameters
        for param in query_string.split('&'):
            if param.startswith('sslmode='):
                # Skip sslmode - handled via connect_args
                logger.info("SSL mode detected in DATABASE_URL - handling via connect_args")
                continue
            elif param.startswith('pgbouncer='):
                # Keep pgbouncer parameter for Supabase
                query_params.append(param)
                logger.info(f"Supabase parameter preserved: {param}")
            else:
                # Keep other parameters
                query_params.append(param)
        
        # Reconstruct URL with filtered parameters
        if query_params:
            db_url = base_url + '?' + '&'.join(query_params)
        else:
            db_url = base_url
    
    # Log connection details (without exposing password)
    ssl_info = " (SSL required)" if "sslmode=require" in settings.DATABASE_URL else ""
    pgbouncer_info = " (pgbouncer)" if "pgbouncer=true" in settings.DATABASE_URL else ""
    logger.info(f"Database connection: {parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}{ssl_info}{pgbouncer_info}")
    return db_url


# Global variables for lazy initialization (avoid import-time network access)
_supabase_client: Client = None
_database_engine = None
_session_factory = None


def get_supabase_client() -> Client:
    """Get Supabase client with lazy initialization"""
    global _supabase_client
    if _supabase_client is None:
        logger.info("Initializing Supabase client...")
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


def get_database_engine():
    """Get database engine with lazy initialization"""
    global _database_engine, _session_factory
    if _database_engine is None:
        logger.info("Creating database engine...")
        _database_engine = create_async_engine(
            create_database_url(),
            echo=settings.DEBUG,
            # Supabase connection settings
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            # Use NullPool for serverless environments
            poolclass=NullPool if settings.DEBUG else None,
            # Connection arguments for Supabase with SSL support
            connect_args={
                "server_settings": {
                    "application_name": "KSWiFi_FastAPI",
                },
                # SSL configuration for Supabase external connections
                "ssl": "require" if "sslmode=require" in settings.DATABASE_URL else None,
            }
        )
        
        # Create session factory
        _session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_database_engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Important for async usage
        )
    return _database_engine


def get_session_factory():
    """Get session factory (ensures engine is initialized)"""
    get_database_engine()  # Ensure engine is created
    return _session_factory


# Backward compatibility functions
def get_supabase() -> Client:
    """Backward compatibility function"""
    return get_supabase_client()

def get_engine():
    """Backward compatibility function"""
    return get_database_engine()


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


async def test_database_connection():
    """
    Test database connection to Supabase PostgreSQL
    """
    try:
        logger.info("Testing database connection...")
        db_engine = get_database_engine()  # Lazy initialization
        async with db_engine.begin() as conn:
            result = await conn.execute("SELECT version(), current_database(), current_user")
            row = result.fetchone()
            logger.info(f"Connected to PostgreSQL: {row[0]}")
            logger.info(f"Database: {row[1]}, User: {row[2]}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def init_db():
    """Initialize database tables and test connection"""
    try:
        # Test connection first
        await test_database_connection()
        
        # Note: We'll primarily use Supabase migrations for schema
        # This is just for any additional tables if needed
        db_engine = get_database_engine()  # Lazy initialization
        async with db_engine.begin() as conn:
            # Import models here to ensure they're registered
            from ..models.base import Base
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def get_database_health():
    """
    Get database health status for monitoring
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute("""
                SELECT 
                    version() as postgres_version,
                    current_database() as database_name,
                    current_user as connected_user,
                    now() as server_time,
                    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
            """)
            row = result.fetchone()
            
            return {
                "status": "healthy",
                "postgres_version": row[0],
                "database": row[1],
                "user": row[2],
                "server_time": row[3].isoformat(),
                "tables": row[4],
                "connection_pool": {
                    "size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                }
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def close_db():
    """Close database connections"""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


# Direct Supabase operations for convenience
class SupabaseClient:
    """Wrapper for common Supabase operations"""
    
    def __init__(self):
        self.client = get_supabase_client()  # Use lazy initialization
    
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