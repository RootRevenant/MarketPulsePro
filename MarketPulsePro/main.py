#!/usr/bin/env python3
"""
MarketPulse Pro - Main Entry Point
"""

import asyncio
import logging
import os
from pathlib import Path

from src.core.bot import MarketPulseBot
from src.core.config import Config
from src.utils.logger import setup_logging


async def main():
    """Application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config()
    
    # Initialize bot
    bot = MarketPulseBot(config)
    
    try:
        logger.info("🚀 Starting MarketPulse Pro Bot...")
        
        # Start the bot
        await bot.start()
        
        # Keep alive for Render
        if os.getenv('RENDER'):
            logger.info("Running on Render.com - Keeping alive...")
            # Run forever
            while True:
                await asyncio.sleep(3600)
        else:
            await bot.run_forever()
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())