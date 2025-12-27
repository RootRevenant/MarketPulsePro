#!/usr/bin/env python3
"""
Database setup script
"""

import asyncio
import logging
from pathlib import Path
from src.core.database import init_db
from src.core.config import setup_logging

async def setup_database():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        Path("data").mkdir(exist_ok=True)
        await init_db()
        logger.info("✅ Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database())