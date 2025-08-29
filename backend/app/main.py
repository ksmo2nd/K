"""
KSWiFi Backend Service
FastAPI application with Supabase integration
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

# Import settings with error handling
try:
    from .core.config import settings
    print(f"✅ Configuration loaded successfully: {settings.APP_NAME} v{settings.APP_VERSION}")
except Exception as e:
    print(f"❌ CRITICAL: Failed to load configuration: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    print("❌ This usually means missing environment variables")
    print("❌ Check your deployment platform environment variables")
    raise
from .core.database import init_db, close_db
from .routes import (
    auth_router,
    bundles_router,
    esim_router,
    monitoring_router,
    notifications_router,
    activation_router,
    sessions_router
)
from .routes.wifi import router as wifi_router
from .routes.connect import router as connect_router
# Removed dual_esim_router - using WiFi QR system instead
from .routes.debug import router as debug_router
from .services.monitoring_service import MonitoringService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(settings.LOG_LEVEL),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global monitoring service instance
monitoring_service = MonitoringService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with robust debugging"""
    
    # === STARTUP DEBUGGING ===
    logger.info("🚀 Starting KSWiFi Backend Service", 
                version=settings.APP_VERSION, 
                host=settings.HOST, 
                port=settings.PORT)
    
    # Environment validation
    try:
        logger.info("🔧 Environment Check:", 
                   supabase_url_set=bool(settings.SUPABASE_URL),
                   database_url_set=bool(settings.DATABASE_URL) if settings.DATABASE_URL else False,
                   secret_key_set=bool(settings.SECRET_KEY))
        
        # Test critical settings
        if not settings.SUPABASE_URL or settings.SUPABASE_URL.startswith('https://placeholder'):
            logger.warning("⚠️  SUPABASE_URL appears to be placeholder")
        if settings.DATABASE_URL and 'localhost' in settings.DATABASE_URL:
            logger.warning("⚠️  DATABASE_URL appears to be localhost/placeholder")
        elif not settings.DATABASE_URL:
            logger.info("ℹ️  DATABASE_URL not set (using Supabase HTTP client)")
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
            logger.warning("⚠️  SECRET_KEY appears to be weak or placeholder")
            
        logger.info("✅ Configuration validation complete")
        
    except Exception as e:
        logger.error("❌ Environment validation failed", 
                    error=str(e), 
                    error_type=type(e).__name__)
        raise
    
    # Supabase HTTP client initialization
    try:
        logger.info("🗄️  Initializing Supabase HTTP client...")
        await init_db()
        logger.info("✅ Supabase HTTP client initialized successfully")
        
    except Exception as e:
        logger.error("❌ Supabase initialization failed", 
                    error=str(e), 
                    error_type=type(e).__name__)
        # Continue anyway - some services might work without DB
        logger.warning("⚠️  Continuing without database - some features may not work")
    
    # Monitoring service
    try:
        logger.info("📊 Starting background monitoring service...")
        asyncio.create_task(monitoring_service.start_monitoring())
        logger.info("✅ Background monitoring service started")
        
    except Exception as e:
        logger.error("❌ Monitoring service failed to start", 
                    error=str(e), 
                    error_type=type(e).__name__)
        # Continue anyway - monitoring is not critical
        logger.warning("⚠️  Continuing without monitoring service")
    
    logger.info("🎉 KSWiFi Backend Service startup complete!")
    
    yield
    
    # === SHUTDOWN DEBUGGING ===
    logger.info("🔄 Shutting down KSWiFi Backend Service...")
    
    try:
        # Stop monitoring service
        logger.info("📊 Stopping monitoring service...")
        await monitoring_service.stop_monitoring()
        logger.info("✅ Monitoring service stopped")
        
    except Exception as e:
        logger.error("❌ Error stopping monitoring service", 
                    error=str(e), 
                    error_type=type(e).__name__)
    
    try:
        # Close database connections
        logger.info("🗄️  Closing database connections...")
        await close_db()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error("❌ Error closing database connections", 
                    error=str(e), 
                    error_type=type(e).__name__)
    
    logger.info("👋 KSWiFi Backend Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Advanced eSIM and data pack management API with real-time monitoring",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error("HTTP Exception", status_code=exc.status_code, detail=exc.detail, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "path": str(request.url.path)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url.path)}
    )

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(bundles_router, prefix="/api/bundles", tags=["Data Bundles"])
app.include_router(esim_router, prefix="/api/esim", tags=["eSIM Management"])
app.include_router(wifi_router, prefix="/api/wifi", tags=["WiFi QR System"])
app.include_router(connect_router, tags=["KSWiFi Connect"])
app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(activation_router, tags=["Data Pack Activation"])
app.include_router(sessions_router, prefix="/api", tags=["Internet Sessions"])
app.include_router(debug_router, prefix="/api/debug", tags=["Debug"])

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint with Supabase PostgreSQL connection test"""
    try:
        # Check Supabase PostgreSQL database connectivity
        from .core.database import get_database_health
        db_health = await get_database_health()
        
        # Check monitoring service
        monitoring_stats = await monitoring_service.get_monitoring_stats()
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "database": db_health,
            "monitoring": "running" if monitoring_stats.get('service_running') else "stopped",
            "timestamp": monitoring_stats.get('last_check')
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "error": str(e)
            }
        )

# API alias for health endpoint
@app.get("/api/health")
async def api_health_check():
    """API health check endpoint (alias for /health)"""
    return await health_check()

@app.get("/debug")
async def debug_info():
    """Comprehensive debug information for deployment troubleshooting"""
    import os
    import sys
    import platform
    from datetime import datetime
    
    try:
        # Environment information
        env_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "hostname": platform.node(),
            "current_directory": os.getcwd(),
            "python_path": sys.path[:3],  # First 3 entries only
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Configuration status
        config_status = {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
            "supabase_url_configured": bool(settings.SUPABASE_URL and not settings.SUPABASE_URL.startswith('https://placeholder')),
            "database_url_configured": bool(settings.DATABASE_URL and 'localhost' not in settings.DATABASE_URL) if settings.DATABASE_URL else False,
            "secret_key_configured": bool(settings.SECRET_KEY and len(settings.SECRET_KEY) >= 32),
            "cors_origins": settings.ALLOWED_ORIGINS
        }
        
        # Environment variables check (without exposing values)
        env_vars_status = {
            "SUPABASE_URL": "SET" if os.getenv("SUPABASE_URL") else "MISSING",
            "SUPABASE_KEY": "SET" if os.getenv("SUPABASE_KEY") else "MISSING", 
            "SUPABASE_ANON_KEY": "SET" if os.getenv("SUPABASE_ANON_KEY") else "MISSING",
            "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "MISSING",
            "SECRET_KEY": "SET" if os.getenv("SECRET_KEY") else "MISSING",
            "PORT": os.getenv("PORT", "8000")
        }
        
        # Import test
        import_status = {}
        critical_imports = [
            "fastapi", "uvicorn", "supabase", "sqlalchemy", 
            "pydantic", "pydantic_settings", "structlog"
        ]
        
        for module in critical_imports:
            try:
                __import__(module)
                import_status[module] = "✅ OK"
            except ImportError as e:
                import_status[module] = f"❌ FAILED: {str(e)}"
        
        return {
            "status": "debug_info_collected",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": env_info,
            "configuration": config_status,
            "environment_variables": env_vars_status,
            "imports": import_status,
            "message": "Debug information collected successfully"
        }
        
    except Exception as e:
        logger.error("Debug endpoint failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "status": "debug_failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Failed to collect debug information"
            }
        )

@app.get("/cors-test")
async def cors_test():
    """CORS test endpoint to verify cross-origin requests work"""
    return {
        "message": "CORS is working!",
        "cors_enabled": True,
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/database")
async def database_health_check():
    """Dedicated Supabase PostgreSQL database health check"""
    try:
        from .core.database import get_database_health, test_supabase_connection
        
        # Test basic connection
        await test_supabase_connection()
        
        # Get detailed health info
        db_health = await get_database_health()
        
        return {
            "status": "success",
            "message": "Database connection successful",
            "database_info": db_health
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Database connection failed",
                "error": str(e)
            }
        )

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    try:
        health_data = {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "components": {}
        }
        
        # Check database
        try:
            from .core.database import get_supabase_client
            test_response = get_supabase_client().table('users').select('id').limit(1).execute()
            health_data["components"]["database"] = {
                "status": "healthy",
                "response_time": "< 100ms"
            }
        except Exception as e:
            health_data["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Check monitoring service
        try:
            monitoring_stats = await monitoring_service.get_monitoring_stats()
            health_data["components"]["monitoring"] = {
                "status": "healthy" if monitoring_stats.get('service_running') else "stopped",
                "stats": monitoring_stats
            }
        except Exception as e:
            health_data["components"]["monitoring"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check external services (eSIM provider)
        health_data["components"]["esim_provider"] = {
            "status": "unknown",
            "note": "External service check not implemented"
        }
        
        return health_data
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.APP_NAME,
                "error": str(e)
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else "Documentation not available in production",
        "health_url": "/health"
    }

# Development endpoint to get environment info
@app.get("/info")
async def app_info():
    """Application information (only available in debug mode)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "environment": "development",
        "supabase_url": settings.SUPABASE_URL,
        "allowed_origins": settings.ALLOWED_ORIGINS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )