"""
Decorators for handlers
"""

import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from typing import Callable, Any

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
        
        # Check subscription
        has_joined = await channel_service.check_user_channels(user_id)
        
        if not has_joined:
            # Get required channels
            channels = await channel_service.get_required_channels()
            
            if channels:
                from src.utils.keyboards import get_channel_keyboard
                
                message = (
                    "🔒 **برای دسترسی به این بخش، لطفاً در کانال‌های زیر عضو شوید:**\n\n"
                )
                
                for i, channel in enumerate(channels, 1):
                    message += f"{i}. {channel.username}\n"
                
                message += "\nپس از عضویت، دکمه 'بررسی عضویت' را بزنید."
                
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


def require_vip(func: Callable) -> Callable:
    """Decorator to require VIP subscription"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is admin (admins have VIP access)
        if user_id in config.ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        
        # Check if user is VIP
        from src.core.database import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            from src.core.database import User
            result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_vip:
                from src.core.config import config
                
                await update.message.reply_text(
                    "👑 **این قابلیت فقط برای کاربران VIP در دسترس است!**\n\n"
                    f"با ارتقاء به VIP می‌توانید از این و سایر قابلیت‌های ویژه استفاده کنید.\n\n"
                    f"💰 قیمت: {config.VIP_PRICE:,} تومان ماهیانه\n\n"
                    "برای اطلاعات بیشتر /vip را ارسال کنید.",
                    parse_mode="Markdown"
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
