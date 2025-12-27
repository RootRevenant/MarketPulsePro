"""
Admin Handlers
"""

import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.core.config import config
from src.models.user import User
from src.models.channel import Channel
from src.utils.decorators import require_admin
from src.utils.keyboards import get_admin_keyboard


logger = logging.getLogger(__name__)


@require_admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    user = update.effective_user
    
    keyboard = get_admin_keyboard()
    
    message = (
        "👑 **پنل مدیریت MarketPulse Pro**\n\n"
        f"👤 مدیر: {user.full_name}\n"
        f"🆔 شناسه: {user.id}\n\n"
        "🔧 گزینه مورد نظر را انتخاب کنید:"
    )
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@require_admin
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    try:
        from src.core.database import async_session
        from sqlalchemy import func, select
        
        async with async_session() as session:
            # User stats
            total_users = await session.scalar(
                select(func.count(User.id))
            )
            active_users = await session.scalar(
                select(func.count(User.id)).where(User.is_active == True)
            )
            vip_users = await session.scalar(
                select(func.count(User.id)).where(User.is_vip == True)
            )
            
            # Channel stats
            total_channels = await session.scalar(
                select(func.count(Channel.id))
            )
            active_channels = await session.scalar(
                select(func.count(Channel.id)).where(Channel.is_active == True)
            )
        
        # Format message
        message = (
            "📊 **آمار ربات**\n\n"
            f"👥 **کاربران:**\n"
            f"• کل کاربران: {total_users:,}\n"
            f"• کاربران فعال: {active_users:,}\n"
            f"• کاربران VIP: {vip_users:,}\n\n"
            f"📢 **کانال‌ها:**\n"
            f"• کل کانال‌ها: {total_channels}\n"
            f"• کانال‌های فعال: {active_channels}\n\n"
            f"⏰ **سیستم:**\n"
            f"• زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• ورژن: 1.0.0\n"
        )
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت آمار")


@require_admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not context.args:
        await update.message.reply_text(
            "📢 لطفاً پیام خود را وارد کنید:\n"
            "مثال: `/broadcast سلام به همه کاربران!`"
        )
        return
    
    message = " ".join(context.args)
    confirm_text = (
        f"📢 **پیام همگانی**\n\n"
        f"{message}\n\n"
        f"آیا مطمئن هستید؟"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ بله، ارسال کن", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ خیر، لغو", callback_data="broadcast_cancel")
        ]
    ])
    
    await update.message.reply_text(
        confirm_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@require_admin
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a required channel"""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "📢 افزودن کانال اجباری:\n"
            "فرمت: `/addchannel @channel_username 200000`\n"
            "• 200000: قیمت ماهیانه (تومان)"
        )
        return
    
    username = args[0]
    try:
        price = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ قیمت باید عدد باشد")
        return
    
    try:
        from src.core.database import async_session
        from sqlalchemy import select
        
        async with async_session() as session:
            # Check if channel exists
            existing = await session.scalar(
                select(Channel).where(Channel.username == username)
            )
            
            if existing:
                await update.message.reply_text("⚠️ این کانال قبلاً اضافه شده است")
                return
            
            # Add new channel
            channel = Channel(
                username=username,
                monthly_price=price,
                is_active=True
            )
            
            session.add(channel)
            await session.commit()
            
            await update.message.reply_text(
                f"✅ کانال {username} با موفقیت اضافه شد\n"
                f"💰 قیمت ماهیانه: {price:,} تومان"
            )
            
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await update.message.reply_text("⚠️ خطا در افزودن کانال")