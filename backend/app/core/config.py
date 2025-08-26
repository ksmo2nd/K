"""
Configuration settings for KSWiFi Backend Service
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application Configuration
    APP_NAME: str = Field(default="KSWiFi Backend Service", description="Application name")
    APP_VERSION: str = Field(default="1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=int(os.getenv("PORT", 8000)), description="Server port (uses Render's $PORT env var)")
    
    # Backend URL for eSIM configuration
    BACKEND_URL: Optional[str] = Field(default=None, description="Backend URL for eSIM network configuration (e.g., https://kswifi.onrender.com)")
    
    # Supabase Configuration - PUT YOUR REAL SUPABASE CREDENTIALS HERE
    SUPABASE_URL: str = Field(..., description="Supabase project URL - Get from https://supabase.com/dashboard")
    SUPABASE_KEY: str = Field(..., description="Supabase service role key - Get from project settings")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anon key - Get from project settings")
    
    # Database - No longer needed (using Supabase HTTP client)
    DATABASE_URL: Optional[str] = Field(default=None, description="Not used - kept for backward compatibility")
    
    # Security - PUT YOUR REAL SECRET KEY HERE
    SECRET_KEY: str = Field(..., description="Secret key for JWT - Generate with: openssl rand -hex 32")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT expiration in hours")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5000",
            "https://your-app-domain.vercel.app"
        ],
        description="Allowed CORS origins"
    )
    
    # Redis for background tasks
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # eSIM Provider Configuration - NOW OPTIONAL (we have inbuilt eSIM generation)
    # These are only needed if you want to use external eSIM providers alongside our inbuilt system
    ESIM_PROVIDER_API_URL: Optional[str] = Field(default=None, description="External eSIM provider API URL (optional)")
    ESIM_PROVIDER_API_KEY: Optional[str] = Field(default=None, description="External eSIM provider API key (optional)")
    ESIM_PROVIDER_USERNAME: Optional[str] = Field(default=None, description="External eSIM provider username (optional)")
    ESIM_PROVIDER_PASSWORD: Optional[str] = Field(default=None, description="External eSIM provider password (optional)")
    
    # Data monitoring
    DATA_CHECK_INTERVAL_MINUTES: int = Field(default=5, description="Data balance check interval")
    LOW_DATA_THRESHOLD_MB: float = Field(default=100.0, description="Low data warning threshold")
    
    # Session download pricing - Free up to 5GB, then ₦800 for unlimited access
    BUNDLE_PRICING: dict = Field(
        default={
            "1GB": {"data_mb": 1024, "price_ngn": 0, "price_usd": 0, "validity_days": None, "plan_type": "free"},
            "2GB": {"data_mb": 2048, "price_ngn": 0, "price_usd": 0, "validity_days": None, "plan_type": "free"},
            "3GB": {"data_mb": 3072, "price_ngn": 0, "price_usd": 0, "validity_days": None, "plan_type": "free"},
            "4GB": {"data_mb": 4096, "price_ngn": 0, "price_usd": 0, "validity_days": None, "plan_type": "free"},
            "5GB": {"data_mb": 5120, "price_ngn": 0, "price_usd": 0, "validity_days": None, "plan_type": "free"},
            "Unlimited": {"data_mb": -1, "price_ngn": 800, "price_usd": 1.92, "validity_days": None, "plan_type": "unlimited", "description": "Download up to 100GB sessions"}
        }
    )
    
    # Monitoring and observability
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()