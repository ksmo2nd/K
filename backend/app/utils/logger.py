"""
Logging configuration for KSWiFi Backend Service
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from config import settings

def setup_logging():
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "kswifi.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "kswifi_error.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Admin actions log handler
    admin_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "admin_actions.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    admin_handler.setLevel(logging.INFO)
    admin_handler.setFormatter(formatter)
    
    # Create separate logger for admin actions
    admin_logger = logging.getLogger("admin")
    admin_logger.setLevel(logging.INFO)
    admin_logger.addHandler(admin_handler)
    admin_logger.propagate = False
    
    # Set third-party loggers to WARNING level to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    logger.info("Logging configuration initialized")

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

def log_admin_action(admin_email: str, action: str, details: str = None):
    """Log admin action to separate file"""
    admin_logger = logging.getLogger("admin")
    message = f"Admin: {admin_email} | Action: {action}"
    if details:
        message += f" | Details: {details}"
    admin_logger.info(message)
