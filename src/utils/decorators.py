"""
Decorators for handlers
"""

import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from typing import Callable

from src.core.config import config
from src.services.channel_service import ChannelService

logger = logging.getLogger(__name__)
channel_service = ChannelService()


def require_subscription(func: Callable) -> Callable:
    """Decorator to require channel subscription"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is admin
        if user_id in config.ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        
        # Check subscription (این بخش را می‌توانید بعداً کامل کنید)
        # فعلاً برای تست، همه کاربران را تأیید می‌کنیم
        has_joined = True  # Temporary: skip channel check
        
        if not has_joined:
            from src.utils.keyboards import get_channel_keyboard
            channels = []  # Empty for now
            
            message = (
                "🔒 **برای دسترسی به این بخش، لطفاً در کانال‌های زیر عضو شوید:**\n\n"
                "پس از عضویت، دکمه 'بررسی عضویت' را بزنید."
            )
            
            keyboard = get_channel_keyboard(channels)
            
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            return
        
        # User has access, call the original function
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def require_admin(func: Callable) -> Callable:
    """Decorator to require admin privileges"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text(
                "⛔ **دسترسی محدود!**\n"
                "این دستور فقط برای مدیران ربات قابل استفاده است."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors in handlers"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            error_message = (
                "⚠️ **خطایی رخ داد!**\n\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.\n"
                "برای راهنمایی /help را ارسال کنید."
            )
            
            try:
                await update.message.reply_text(error_message)
            except:
                pass
    
    return wrapper
