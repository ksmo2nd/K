"""
Database models for KSWiFi Backend Service
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class UserStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class DataPackStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"

class ESIMStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    status = Column(String(20), default=UserStatus.ACTIVE.value)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    data_packs = relationship("DataPack", back_populates="user")
    esims = relationship("ESIM", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")

class DataPack(Base):
    """Data pack model for managing user data allowances"""
    __tablename__ = "data_packs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    total_data_mb = Column(Float, nullable=False)  # Total data in MB
    used_data_mb = Column(Float, default=0.0)     # Used data in MB
    remaining_data_mb = Column(Float, nullable=False)  # Remaining data in MB
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default=DataPackStatus.ACTIVE.value)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="data_packs")
    usage_logs = relationship("UsageLog", back_populates="data_pack")

class ESIM(Base):
    """eSIM model for managing virtual SIM configurations"""
    __tablename__ = "esims"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    iccid = Column(String(20), unique=True, nullable=False)  # SIM card identifier
    imsi = Column(String(15), unique=True, nullable=False)   # International Mobile Subscriber Identity
    msisdn = Column(String(15), nullable=True)              # Mobile phone number
    activation_code = Column(String(50), unique=True, nullable=False)
    qr_code_data = Column(Text, nullable=False)             # QR code data for eSIM activation
    status = Column(String(20), default=ESIMStatus.PENDING.value)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Network settings
    apn = Column(String(100), default="internet")
    username = Column(String(50), nullable=True)
    password = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="esims")

class UsageLog(Base):
    """Usage log model for tracking data consumption"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data_pack_id = Column(Integer, ForeignKey("data_packs.id"), nullable=False)
    data_used_mb = Column(Float, nullable=False)
    session_duration = Column(Integer, nullable=True)  # Duration in seconds
    ip_address = Column(String(45), nullable=True)
    location = Column(String(100), nullable=True)
    device_info = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    data_pack = relationship("DataPack", back_populates="usage_logs")

class AdminLog(Base):
    """Admin log model for tracking administrative actions"""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)  # user, datapack, esim
    target_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    admin_user = relationship("User")
