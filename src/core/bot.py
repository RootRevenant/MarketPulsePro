"""
Main Bot Class
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from src.core.config import config
from src.core.database import AsyncSessionLocal, User
from src.handlers import (
    user_handlers,
    admin_handlers,
    price_handlers,
    news_handlers,
    callback_handlers
)
from src.services.scheduler import SchedulerService
from src.utils.keyboards import KeyboardManager
from src.utils.decorators import require_subscription

logger = logging.getLogger(__name__)


class MarketPulseBot:
    """Main bot class"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logger
        self.app: Optional[Application] = None
        self.scheduler: Optional[SchedulerService] = None
        self.keyboard_manager = KeyboardManager()
        
        # Statistics
        self.stats = {
            "total_users": 0,
            "active_users": 0,
            "messages_processed": 0
        }
    
    async def start(self):
        """Start the bot"""
        self.logger.info("Initializing bot...")
        
        # Create application with persistence
        self.app = (
            Application.builder()
            .token(self.config.BOT_TOKEN)
            .post_init(self._post_init)
            .post_shutdown(self._post_shutdown)
            .build()
        )
        
        # Setup handlers
        self._setup_handlers()
        
        # Initialize scheduler
        self.scheduler = SchedulerService(self.app, self.config)
        await self.scheduler.start()
        
        # Initialize database
        await self._init_database()
        
        self.logger.info("✅ Bot initialized successfully")
    
    def _setup_handlers(self):
        """Setup all command handlers"""
        
        # ========== USER COMMANDS ==========
        self.app.add_handler(CommandHandler("start", user_handlers.start_command))
        self.app.add_handler(CommandHandler("help", user_handlers.help_command))
        self.app.add_handler(CommandHandler("prices", user_handlers.prices_command))
        self.app.add_handler(CommandHandler("gold", user_handlers.gold_command))
        self.app.add_handler(CommandHandler("crypto", user_handlers.crypto_command))
        self.app.add_handler(CommandHandler("news", user_handlers.news_command))
        self.app.add_handler(CommandHandler("profile", user_handlers.profile_command))
        self.app.add_handler(CommandHandler("vip", user_handlers.vip_command))
        self.app.add_handler(CommandHandler("settings", user_handlers.settings_command))
        
        # ========== ADMIN COMMANDS ==========
        self.app.add_handler(CommandHandler("admin", admin_handlers.admin_command))
        self.app.add_handler(CommandHandler("stats", admin_handlers.stats_command))
        self.app.add_handler(CommandHandler("broadcast", admin_handlers.broadcast_command))
        self.app.add_handler(CommandHandler("addchannel", admin_handlers.addchannel_command))
        self.app.add_handler(CommandHandler("listchannels", admin_handlers.listchannels_command))
        self.app.add_handler(CommandHandler("users", admin_handlers.users_command))
        
        # ========== CALLBACK QUERIES ==========
        self.app.add_handler(CallbackQueryHandler(callback_handlers.callback_handler))
        
        # ========== MESSAGE HANDLERS ==========
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            user_handlers.message_handler
        ))
        
        # ========== ERROR HANDLER ==========
        self.app.add_error_handler(self._error_handler)
    
    async def _init_database(self):
        """Initialize database"""
        from src.core.database import init_db
        await init_db()
        self.logger.info("✅ Database initialized")
        
        # Update stats
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func
            from src.core.database import User
            
            total_users = await session.scalar(func.count(User.id))
            active_users = await session.scalar(
                func.count(User.id).where(User.is_active == True)
            )
            
            self.stats["total_users"] = total_users or 0
            self.stats["active_users"] = active_users or 0
    
    async def _post_init(self, application: Application):
        """Post initialization"""
        self.logger.info("🤖 MarketPulse Pro is running!")
        
        # Set bot commands
        commands = [
            ("start", "شروع کار با ربات"),
            ("prices", "قیمت‌های لحظه‌ای"),
            ("gold", "قیمت طلا و سکه"),
            ("crypto", "ارزهای دیجیتال"),
            ("news", "اخبار اقتصادی"),
            ("profile", "پروفایل کاربری"),
            ("vip", "اشتراک ویژه"),
            ("help", "راهنمای ربات")
        ]
        
        await application.bot.set_my_commands(commands)
        
        # Send startup message to admins
        for admin_id in self.config.ADMIN_IDS:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text="✅ ربات MarketPulse Pro با موفقیت راه‌اندازی شد!"
                )
            except Exception as e:
                self.logger.error(f"Failed to send startup message to admin {admin_id}: {e}")
    
    async def _post_shutdown(self, application: Application):
        """Post shutdown cleanup"""
        if self.scheduler:
            await self.scheduler.stop()
        
        # Send shutdown message to admins
        for admin_id in self.config.ADMIN_IDS:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text="⚠️ ربات MarketPulse Pro خاموش شد."
                )
            except:
                pass
        
        self.logger.info("👋 Bot shutdown complete")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        self.logger.error(
            f"Exception while handling an update: {context.error}",
            exc_info=context.error
        )
        
        # Send error message to admins
        error_msg = f"❌ خطا در ربات:\n{context.error}"
        for admin_id in self.config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=error_msg[:4000]
                )
            except:
                pass
    
    async def run_forever(self):
        """Run bot forever"""
        await self.app.initialize()
        await self.app.start()
        
        # Start polling
        await self.app.updater.start_polling(
            poll_interval=0.5,
            timeout=10,
            drop_pending_updates=True
        )
        
        # Keep running
        self.logger.info("🔄 Bot is now running...")
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    
    async def stop(self):
        """Stop the bot"""
        if self.app:
            if self.app.updater:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
