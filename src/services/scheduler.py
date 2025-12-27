"""
Scheduler Service - Background tasks
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.core.config import config
from src.services.price_service import PriceService
from src.services.news_service import NewsService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling background tasks"""
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.price_service = PriceService()
        self.news_service = NewsService()
        
        # Statistics
        self.stats = {
            'price_updates': 0,
            'news_updates': 0,
            'last_price_update': None,
            'last_news_update': None
        }
    
    async def start(self):
        """Start the scheduler"""
        logger.info("Starting scheduler...")
        
        # Schedule price updates
        price_trigger = IntervalTrigger(seconds=config.PRICE_UPDATE_INTERVAL)
        self.scheduler.add_job(
            self.update_prices,
            trigger=price_trigger,
            id='price_update',
            name='Update prices',
            max_instances=1
        )
        
        # Schedule news updates
        news_trigger = IntervalTrigger(seconds=config.NEWS_UPDATE_INTERVAL)
        self.scheduler.add_job(
            self.update_news,
            trigger=news_trigger,
            id='news_update',
            name='Update news',
            max_instances=1
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info(f"Scheduler started with {len(self.scheduler.get_jobs())} jobs")
    
    async def update_prices(self):
        """Update prices periodically"""
        try:
            logger.debug("Updating prices...")
            
            # Fetch new prices
            prices = await self.price_service.get_all_prices()
            
            # Update statistics
            self.stats['price_updates'] += 1
            self.stats['last_price_update'] = datetime.now()
            
            logger.debug(f"Prices updated ({self.stats['price_updates']})")
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    async def update_news(self):
        """Update news periodically"""
        try:
            logger.debug("Updating news...")
            
            # Fetch new news
            news = await self.news_service.get_latest_news(limit=5)
            
            # Update statistics
            self.stats['news_updates'] += 1
            self.stats['last_news_update'] = datetime.now()
            
            logger.debug(f"News updated ({self.stats['news_updates']})")
            
        except Exception as e:
            logger.error(f"Error updating news: {e}")
    
    async def send_price_alerts(self):
        """Send price alerts to users (placeholder)"""
        # This would need to check user alerts and send notifications
        pass
    
    async def check_channel_memberships(self):
        """Check if users are still members of required channels"""
        # This would need to periodically verify memberships
        pass
    
    async def cleanup_old_data(self):
        """Cleanup old data from database"""
        # This would remove old price history, etc.
        pass
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            **self.stats,
            'running': self.scheduler.running,
            'jobs': len(self.scheduler.get_jobs()),
            'next_price_update': self.scheduler.get_job('price_update').next_run_time if self.scheduler.get_job('price_update') else None,
            'next_news_update': self.scheduler.get_job('news_update').next_run_time if self.scheduler.get_job('news_update') else None
        }
