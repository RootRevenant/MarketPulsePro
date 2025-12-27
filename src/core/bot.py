import logging
from telegram.ext import Application

from src.core.config import Config
from src.handlers import user_handlers, admin_handlers
from src.services.scheduler import SchedulerService

logger = logging.getLogger(__name__)

class MarketPulseBot:
    def __init__(self, config: Config):
        self.config = config
        self.app = None
        self.scheduler = None
    
    async def start(self):
        self.app = Application.builder().token(self.config.BOT_TOKEN).build()
        self._setup_handlers()
        self.scheduler = SchedulerService(self.app, self.config)
        await self.scheduler.start()
        logger.info("✅ Bot initialized successfully")
    
    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", user_handlers.start_command))
        self.app.add_handler(CommandHandler("help", user_handlers.help_command))
        self.app.add_handler(CommandHandler("prices", user_handlers.prices_command))
        self.app.add_handler(CommandHandler("admin", admin_handlers.admin_command))
        # ... سایر هندلرها
    
    async def run_forever(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)
    
    async def stop(self):
        if self.scheduler:
            await self.scheduler.stop()
        if self.app:
            await self.app.stop()
            await self.app.shutdown()