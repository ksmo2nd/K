"""
Enum definitions for the application
"""

from enum import Enum


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended" 
    DELETED = "deleted"


class DataPackStatus(str, Enum):
    """Data pack status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"


class ESIMStatus(str, Enum):
    """eSIM status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class UsageLogType(str, Enum):
    """Usage log type enumeration"""
    DATA_USAGE = "data_usage"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    BALANCE_CHECK = "balance_check"