"""
Main Bot Class
"""

import asyncio
import logging
from typing import Dict, Any
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from src.core.config import Config
from src.handlers import (
    user_handlers,
    admin_handlers,
    price_handlers,
    news_handlers,
    callback_handlers
)
from src.services.scheduler import SchedulerService
from src.utils.keyboards import KeyboardManager
from src.utils.logger import get_logger


class MarketPulseBot:
    """Main bot class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.app: Optional[Application] = None
        self.scheduler: Optional[SchedulerService] = None
        self.keyboard_manager = KeyboardManager()
        
        # Statistics
        self.stats = {
            "users": 0,
            "active_users": 0,
            "messages_processed": 0
        }
    
    async def start(self):
        """Start the bot"""
        self.logger.info("Initializing bot...")
        
        # Create application
        self.app = Application.builder() \
            .token(self.config.BOT_TOKEN) \
            .post_init(self._post_init) \
            .post_shutdown(self._post_shutdown) \
            .build()
        
        # Setup handlers
        await self._setup_handlers()
        
        # Initialize scheduler
        self.scheduler = SchedulerService(self.app, self.config)
        await self.scheduler.start()
        
        # Initialize database
        await self._init_database()
        
        self.logger.info("✅ Bot initialized successfully")
    
    async def _setup_handlers(self):
        """Setup all command handlers"""
        
        # User commands
        self.app.add_handler(CommandHandler("start", user_handlers.start))
        self.app.add_handler(CommandHandler("help", user_handlers.help_command))
        self.app.add_handler(CommandHandler("prices", price_handlers.show_prices))
        self.app.add_handler(CommandHandler("gold", price_handlers.show_gold))
        self.app.add_handler(CommandHandler("crypto", price_handlers.show_crypto))
        self.app.add_handler(CommandHandler("news", news_handlers.show_news))
        self.app.add_handler(CommandHandler("chart", price_handlers.show_chart))
        self.app.add_handler(CommandHandler("alert", user_handlers.set_alert))
        self.app.add_handler(CommandHandler("profile", user_handlers.show_profile))
        self.app.add_handler(CommandHandler("vip", user_handlers.vip_info))
        
        # Admin commands
        self.app.add_handler(CommandHandler("admin", admin_handlers.admin_panel))
        self.app.add_handler(CommandHandler("stats", admin_handlers.show_stats))
        self.app.add_handler(CommandHandler("broadcast", admin_handlers.broadcast))
        self.app.add_handler(CommandHandler("addchannel", admin_handlers.add_channel))
        self.app.add_handler(CommandHandler("users", admin_handlers.list_users))
        
        # Callback queries
        self.app.add_handler(CallbackQueryHandler(callback_handlers.handle_callback))
        
        # Messages
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            user_handlers.handle_message
        ))
        
        # Error handler
        self.app.add_error_handler(self._error_handler)
    
    async def _init_database(self):
        """Initialize database"""
        from src.core.database import init_db
        await init_db()
        self.logger.info("✅ Database initialized")
    
    async def _post_init(self, application: Application):
        """Post initialization"""
        self.logger.info("🤖 MarketPulse Pro is running!")
        
        # Set bot commands
        commands = [
            ("start", "راه‌اندازی ربات"),
            ("prices", "قیمت‌های لحظه‌ای"),
            ("gold", "قیمت طلا و سکه"),
            ("crypto", "ارزهای دیجیتال"),
            ("news", "اخبار اقتصادی"),
            ("chart", "نمودار قیمت"),
            ("profile", "پروفایل کاربری"),
            ("vip", "اشتراک ویژه"),
            ("help", "راهنما")
        ]
        
        await application.bot.set_my_commands(commands)
    
    async def _post_shutdown(self, application: Application):
        """Post shutdown cleanup"""
        if self.scheduler:
            await self.scheduler.stop()
        self.logger.info("👋 Bot shutdown complete")
    
    async def _error_handler(self, update, context):
        """Global error handler"""
        self.logger.error(
            f"Exception while handling an update: {context.error}",
            exc_info=context.error
        )
    
    async def run_forever(self):
        """Run bot forever"""
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
    
    async def stop(self):
        """Stop the bot"""
        if self.app:
            await self.app.stop()
            await self.app.shutdown()