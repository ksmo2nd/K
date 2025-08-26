"""
Base model definitions for Supabase HTTP client
No SQLAlchemy needed - using Supabase's schema directly
"""

from datetime import datetime
from typing import Optional
import uuid


class BaseModel:
    """
    Simple base model for common fields
    Used for type hints and documentation only
    Actual database operations use Supabase HTTP client
    """
    
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase operations"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# For backward compatibility
Base = BaseModel