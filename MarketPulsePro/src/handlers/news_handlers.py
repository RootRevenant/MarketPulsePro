"""
News Handlers
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.services.news_service import NewsService
from src.utils.formatters import format_news
from src.utils.decorators import require_subscription


logger = logging.getLogger(__name__)
news_service = NewsService()


@require_subscription
async def show_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show latest news"""
    try:
        # Get news
        iran_news = await news_service.get_iran_news(limit=5)
        world_news = await news_service.get_world_news(limit=5)
        
        # Format message
        message = "📰 **آخرین اخبار اقتصادی**\n\n"
        
        message += "🇮🇷 **ایران:**\n"
        for i, news in enumerate(iran_news, 1):
            message += f"{i}. {news['title']}\n"
            message += f"   📅 {news['time']}\n"
            message += f"   🔗 {news['link'][:50]}...\n\n"
        
        message += "🌍 **جهان:**\n"
        for i, news in enumerate(world_news, 1):
            message += f"{i}. {news['title']}\n"
            message += f"   📅 {news['time']}\n"
            message += f"   🔗 {news['link'][:50]}...\n\n"
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error showing news: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت اخبار")