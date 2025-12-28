from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="fa")
    
    # Subscription
    is_vip = Column(Boolean, default=False)
    vip_until = Column(DateTime, nullable=True)
    free_trial_used = Column(Boolean, default=False)
    
    # Settings
    notifications_enabled = Column(Boolean, default=True)
    favorite_symbols = Column(JSON, default=list)
    
    # Stats
    join_date = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    
    # Channels
    joined_channels = Column(JSON, default=dict)
    has_joined_required_channels = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User {self.telegram_id}>"
