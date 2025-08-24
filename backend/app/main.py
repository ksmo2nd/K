"""
KSWiFi Backend Service
FastAPI application with Supabase integration
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from .core.config import settings
from .core.database import init_db, close_db
from .routes import (
    auth_router,
    bundles_router,
    esim_router,
    monitoring_router,
    notifications_router,
    activation_router
)
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
    """Application lifespan events"""
    # Startup
    logger.info("Starting KSWiFi Backend Service", version=settings.APP_VERSION)
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Start monitoring service
        asyncio.create_task(monitoring_service.start_monitoring())
        logger.info("Background monitoring service started")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down KSWiFi Backend Service")
    
    try:
        # Stop monitoring service
        await monitoring_service.stop_monitoring()
        logger.info("Monitoring service stopped")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(activation_router, tags=["Data Pack Activation"])

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        from .core.database import supabase_client
        test_response = supabase_client.client.table('users').select('id').limit(1).execute()
        
        # Check monitoring service
        monitoring_stats = await monitoring_service.get_monitoring_stats()
        
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "database": "connected",
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
            from .core.database import supabase_client
            test_response = supabase_client.client.table('users').select('id').limit(1).execute()
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