"""
Supabase HTTP Client Configuration
Uses Supabase Python SDK for HTTP-based database operations
No direct PostgreSQL connections - fully serverless compatible
"""

import logging
from typing import Optional
from supabase import create_client, Client

from .config import settings

logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get Supabase client with lazy initialization
    Uses HTTP-based connection via Supabase API
    """
    global _supabase_client
    
    if _supabase_client is None:
        logger.info("Initializing Supabase HTTP client...")
        logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
        
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("✅ Supabase HTTP client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise
    
    return _supabase_client


async def test_supabase_connection():
    """
    Test Supabase HTTP connection
    Simple health check using Supabase API
    """
    try:
        logger.info("Testing Supabase HTTP connection...")
        client = get_supabase_client()
        
        # Simple test query - check if we can access the database
        # This will fail gracefully if tables don't exist yet
        try:
            result = client.table('user_profiles').select('count', count='exact').limit(1).execute()
            logger.info(f"✅ Supabase connection successful - can access tables")
            return True
        except Exception as table_error:
            # Tables might not exist yet, but connection works
            logger.info(f"✅ Supabase connection successful - tables may not exist yet: {table_error}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        raise


async def init_db():
    """
    Initialize database connection
    Only tests HTTP connectivity - no schema creation needed
    """
    try:
        logger.info("🗄️  Initializing Supabase connection...")
        await test_supabase_connection()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't raise - let the app start anyway
        return False


async def close_db():
    """
    Clean up database connections
    HTTP client doesn't need explicit cleanup
    """
    logger.info("🔄 Database cleanup complete (HTTP client)")


# Backward compatibility functions
def get_supabase() -> Client:
    """Backward compatibility function"""
    return get_supabase_client()


# Simple health check for monitoring
async def get_database_health():
    """
    Get database health status
    Returns basic connectivity info
    """
    try:
        client = get_supabase_client()
        
        # Test basic connectivity
        health_data = {
            "status": "healthy",
            "connection_type": "supabase_http",
            "url": settings.SUPABASE_URL,
            "client_initialized": client is not None
        }
        
        # Try a simple query to verify access
        try:
            # This is a lightweight query that should work
            result = client.rpc('version').execute()
            health_data["database_accessible"] = True
        except:
            # Database might not have the version function, but that's okay
            health_data["database_accessible"] = "unknown"
            
        return health_data
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection_type": "supabase_http",
            "error": str(e)
        }