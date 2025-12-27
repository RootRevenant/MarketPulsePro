"""
User Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language_code = Column(String(10), default="fa")
    
    # Subscription
    is_vip = Column(Boolean, default=False)
    vip_until = Column(DateTime, nullable=True)
    free_trial_used = Column(Boolean, default=False)
    
    # Settings
    notifications_enabled = Column(Boolean, default=True)
    favorite_symbols = Column(JSON, default=list)
    
    # Statistics
    join_date = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    
    # Channel membership tracking
    joined_channels = Column(JSON, default=dict)  # {channel_id: joined_at}
    
    # Status
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or str(self.telegram_id)