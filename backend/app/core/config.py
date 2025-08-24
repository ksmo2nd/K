"""
Configuration settings for KSWiFi Backend Service
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "KSWiFi Backend Service"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_KEY: str = Field(default="", description="Supabase service role key")
    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anon key")
    
    # Database (Supabase PostgreSQL)
    DATABASE_URL: str = Field(default="postgresql://localhost:5432/kswifi", description="PostgreSQL connection string from Supabase")
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", description="Secret key for JWT")
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
    
    # eSIM Provider Configuration
    ESIM_PROVIDER_API_URL: str = Field(default="https://api.example-provider.com", description="eSIM provider API URL")
    ESIM_PROVIDER_API_KEY: str = Field(default="", description="eSIM provider API key")
    ESIM_PROVIDER_USERNAME: str = Field(default="", description="eSIM provider username")
    ESIM_PROVIDER_PASSWORD: str = Field(default="", description="eSIM provider password")
    
    # Data monitoring
    DATA_CHECK_INTERVAL_MINUTES: int = Field(default=5, description="Data balance check interval")
    LOW_DATA_THRESHOLD_MB: float = Field(default=100.0, description="Low data warning threshold")
    
    # Bundle pricing - Nigerian Naira (NGN) pricing
    BUNDLE_PRICING: dict = Field(
        default={
            "1GB": {"data_mb": 1024, "price_ngn": 500, "price_usd": 1.20, "validity_days": 30, "plan_type": "standard"},
            "5GB": {"data_mb": 5120, "price_ngn": 2000, "price_usd": 4.80, "validity_days": 30, "plan_type": "standard"},
            "10GB": {"data_mb": 10240, "price_ngn": 3500, "price_usd": 8.40, "validity_days": 30, "plan_type": "standard"},
            "20GB": {"data_mb": 20480, "price_ngn": 6000, "price_usd": 14.40, "validity_days": 30, "plan_type": "standard"},
            "Unlimited": {"data_mb": -1, "price_ngn": 800, "price_usd": 1.92, "validity_days": 7, "plan_type": "unlimited"},
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