#!/usr/bin/env python3
"""
Database setup script
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import engine, Base
from src.models.user import User
from src.models.channel import Channel
from src.models.price import Price
from src.models.subscription import Subscription


async def setup_database():
    """Create all database tables"""
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    print(f"📁 Data directory: {data_dir.absolute()}")


if __name__ == "__main__":
    asyncio.run(setup_database())