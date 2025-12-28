from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=True)
    monthly_price = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Channel {self.username}>"
