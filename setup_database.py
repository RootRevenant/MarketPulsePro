#!/usr/bin/env python3
"""
Database setup script
"""

import asyncio
import logging
from pathlib import Path

from src.core.database import init_db, engine, Base
from src.core.config import setup_logging


async def setup_database():
    """Setup database tables"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create data directory if it doesn't exist
        Path("data").mkdir(exist_ok=True)
        
        # Initialize database
        await init_db()
        
        logger.info("✅ Database setup completed successfully!")
        logger.info(f"Database location: data/marketpulse.db")
        
        # Test connection
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
            logger.info("✅ Database connection test successful!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_database())
