#!/usr/bin/env python3
"""
MarketPulse Pro - Main Entry Point
"""

import asyncio
import logging
from pathlib import Path

from src.core.bot import MarketPulseBot
from src.core.config import Config, setup_logging


async def main():
    """Main entry point for the bot"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    config = Config()
    
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_bot_token_here":
        logger.error("❌ Please set BOT_TOKEN in .env file")
        return
    
    bot = MarketPulseBot(config)
    
    try:
        logger.info("🚀 Starting MarketPulse Pro Bot...")
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        await bot.start()
        logger.info("✅ Bot started successfully!")
        
        await bot.run_forever()
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())