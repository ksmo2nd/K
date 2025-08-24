"""
API routes for KSWiFi Backend
"""

from .auth import router as auth_router
from .bundles import router as bundles_router
from .esim import router as esim_router
from .monitoring import router as monitoring_router
from .notifications import router as notifications_router

__all__ = [
    "auth_router",
    "bundles_router",
    "esim_router", 
    "monitoring_router",
    "notifications_router"
]