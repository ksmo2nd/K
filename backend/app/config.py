"""
Configuration settings for KSWiFi Backend Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kswifi.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "kswifi-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    PASSWORD_MIN_LENGTH: int = 8
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    # eSIM Configuration
    ESIM_QR_CODE_SIZE: int = 10
    ESIM_QR_CODE_BORDER: int = 4
    
    # Admin
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@kswifi.com")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()
