"""
Database setup and models
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text
from datetime import datetime
from typing import Optional

from src.core.config import config

# Create async engine
engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="fa")
    
    # Subscription info
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
    
    # Channel membership
    joined_channels = Column(JSON, default=dict)
    has_joined_required_channels = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"


class Channel(Base):
    """Channel model for required channels"""
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    title = Column(String(200))
    monthly_price = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(Integer, nullable=True)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
