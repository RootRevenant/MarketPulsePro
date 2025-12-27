"""
Admin command handlers
"""

import logging
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import config
from src.core.database import AsyncSessionLocal, User, Channel
from src.utils.decorators import require_admin

logger = logging.getLogger(__name__)


@require_admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    admin_text = (
        "👑 **پنل مدیریت MarketPulse Pro**\n\n"
        "🔧 **دستورات مدیریت:**\n"
        "/stats - نمایش آمار ربات\n"
        "/broadcast [متن] - ارسال پیام همگانی\n"
        "/addchannel @username - افزودن کانال اجباری\n"
        "/listchannels - لیست کانال‌ها\n"
        "/users [صفحه] - لیست کاربران\n"
        "/ban [user_id] - مسدود کردن کاربر\n"
        "/unban [user_id] - آزاد کردن کاربر\n\n"
        
        "📊 **آمار سریع:**\n"
    )
    
    # Get quick stats
    async with AsyncSessionLocal() as session:
        # User count
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        vip_users = await session.scalar(
            select(func.count(User.id)).where(User.is_vip == True)
        )
        
        # Channel count
        channel_count = await session.scalar(select(func.count(Channel.id)))
    
    admin_text += (
        f"👥 کاربران کل: {total_users}\n"
        f"✅ کاربران فعال: {active_users}\n"
        f"👑 کاربران VIP: {vip_users}\n"
        f"📢 کانال‌ها: {channel_count}\n\n"
        
        f"🆔 شناسه شما: {update.effective_user.id}"
    )
    
    await update.message.reply_text(admin_text, parse_mode="Markdown")


@require_admin
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Detailed statistics"""
    
    async with AsyncSessionLocal() as session:
        # User statistics
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        vip_users = await session.scalar(
            select(func.count(User.id)).where(User.is_vip == True)
        )
        banned_users = await session.scalar(
            select(func.count(User.id)).where(User.is_banned == True)
        )
        
        # Today's users
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        today_users = await session.scalar(
            select(func.count(User.id)).where(User.join_date >= today_start)
        )
        
        # Channel statistics
        channel_count = await session.scalar(select(func.count(Channel.id)))
        active_channels = await session.scalar(
            select(func.count(Channel.id)).where(Channel.is_active == True)
        )
    
    # Create statistics message
    stats_text = (
        "📊 **آمار دقیق ربات**\n\n"
        
        "👥 **آمار کاربران:**\n"
        f"• کل کاربران: {total_users:,}\n"
        f"• کاربران فعال: {active_users:,}\n"
        f"• کاربران VIP: {vip_users:,}\n"
        f"• کاربران مسدود: {banned_users:,}\n"
        f"• کاربران امروز: {today_users:,}\n\n"
        
        "📢 **آمار کانال‌ها:**\n"
        f"• کل کانال‌ها: {channel_count}\n"
        f"• کانال‌های فعال: {active_channels}\n\n"
        
        "⚙️ **تنظیمات:**\n"
        f"• کانال‌های اجباری: {config.REQUIRED_CHANNELS_COUNT}\n"
        f"• قیمت VIP: {config.VIP_PRICE:,} تومان\n"
        f"• روزهای تست رایگان: {config.FREE_TRIAL_DAYS}\n\n"
        
        "🕐 **زمان سیستم:**\n"
        f"• تاریخ: {datetime.now().strftime('%Y/%m/%d')}\n"
        f"• ساعت: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        "✅ **وضعیت:**\n"
        f"• ربات: {'🟢 فعال' if total_users else '🟡 در حال راه‌اندازی'}\n"
        f"• دیتابیس: {'🟢 متصل'}\n"
        f"• آپدیت قیمت: {'🟢 فعال'}\n"
        f"• آپدیت خبر: {'🟢 فعال'}"
    )
    
    # Add buttons for more actions
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 خروجی Excel", callback_data="export_excel")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_stats")],
        [InlineKeyboardButton("📊 نمودار رشد", callback_data="growth_chart")]
    ])
    
    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@require_admin
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command"""
    if not context.args:
        await update.message.reply_text(
            "📢 **فرمت دستور:**\n"
            "`/broadcast متن پیام`\n\n"
            "مثال:\n"
            "`/broadcast سلام کاربران عزیز!`"
        )
        return
    
    message = " ".join(context.args)
    
    # Ask for confirmation
    confirm_text = (
        f"📢 **پیام همگانی**\n\n"
        f"{message}\n\n"
        f"این پیام به **همه کاربران** ارسال خواهد شد.\n"
        f"آیا مطمئن هستید؟"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ بله، ارسال کن", callback_data=f"broadcast_confirm:{message[:50]}"),
            InlineKeyboardButton("❌ خیر، لغو", callback_data="broadcast_cancel")
        ]
    ])
    
    await update.message.reply_text(
        confirm_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@require_admin
async def addchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addchannel command"""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "📢 **فرمت دستور:**\n"
            "`/addchannel @channel_username [قیمت]`\n\n"
            "مثال:\n"
            "`/addchannel @example_channel 200000`\n\n"
            "• قیمت: به تومان (اختیاری، پیش‌فرض: 0)"
        )
        return
    
    username = args[0]
    price = int(args[1]) if len(args) > 1 else 0
    
    # Validate username format
    if not username.startswith('@'):
        await update.message.reply_text("❌ نام کاربری باید با @ شروع شود.")
        return
    
    async with AsyncSessionLocal() as session:
        # Check if channel exists
        result = await session.execute(
            select(Channel).where(Channel.username == username)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await update.message.reply_text(f"❌ کانال {username} قبلاً اضافه شده است.")
            return
        
        # Add new channel
        new_channel = Channel(
            username=username,
            monthly_price=price,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        session.add(new_channel)
        await session.commit()
        
        await update.message.reply_text(
            f"✅ کانال {username} با موفقیت اضافه شد.\n"
            f"💰 قیمت: {price:,} تومان"
        )


@require_admin
async def listchannels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listchannels command"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Channel).order_by(Channel.created_at.desc())
        )
        channels = result.scalars().all()
    
    if not channels:
        await update.message.reply_text("📭 هیچ کانالی ثبت نشده است.")
        return
    
    message = "📢 **لیست کانال‌های اجباری**\n\n"
    
    for i, channel in enumerate(channels, 1):
        status = "✅ فعال" if channel.is_active else "❌ غیرفعال"
        message += f"{i}. **{channel.username}**\n"
        message += f"   💰 قیمت: {channel.monthly_price:,} تومان\n"
        message += f"   📅 تاریخ: {channel.created_at.strftime('%Y/%m/%d')}\n"
        message += f"   🔧 وضعیت: {status}\n\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن کانال", callback_data="add_channel_dialog")],
        [InlineKeyboardButton("🗑️ حذف کانال", callback_data="remove_channel_dialog")]
    ])
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@require_admin
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command"""
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    per_page = 10
    
    async with AsyncSessionLocal() as session:
        # Get total pages
        total_users = await session.scalar(select(func.count(User.id)))
        total_pages = (total_users + per_page - 1) // per_page
        
        # Get users for this page
        offset = (page - 1) * per_page
        result = await session.execute(
            select(User)
            .order_by(User.join_date.desc())
            .offset(offset)
            .limit(per_page)
        )
        users = result.scalars().all()
    
    if not users:
        await update.message.reply_text("👥 هیچ کاربری یافت نشد.")
        return
    
    message = f"👥 **لیست کاربران** (صفحه {page}/{total_pages})\n\n"
    
    for i, user in enumerate(users, 1):
        index = offset + i
        status = "✅" if user.is_active else "❌"
        vip = "👑" if user.is_vip else ""
        banned = "🚫" if user.is_banned else ""
        
        message += f"{index}. {status} {vip} {banned} "
        message += f"**{user.first_name or 'بدون نام'}**\n"
        message += f"   🆔 {user.telegram_id}\n"
        message += f"   📅 {user.join_date.strftime('%Y/%m/%d')}\n"
        message += f"   💬 {user.message_count} پیام\n\n"
    
    # Create pagination buttons
    keyboard_buttons = []
    if page > 1:
        keyboard_buttons.append(InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"users_page:{page-1}"))
    
    if page < total_pages:
        keyboard_buttons.append(InlineKeyboardButton("صفحه بعد ▶️", callback_data=f"users_page:{page+1}"))
    
    keyboard = InlineKeyboardMarkup([keyboard_buttons] if keyboard_buttons else [])
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@require_admin
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "🚫 **فرمت دستور:**\n"
            "`/ban user_id`\n\n"
            "مثال:\n"
            "`/ban 123456789`"
        )
        return
    
    user_id = int(context.args[0])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(f"❌ کاربر با شناسه {user_id} یافت نشد.")
            return
        
        if user.is_banned:
            await update.message.reply_text(f"⚠️ کاربر {user_id} قبلاً مسدود شده است.")
            return
        
        # Ban the user
        user.is_banned = True
        user.is_active = False
        await session.commit()
        
        await update.message.reply_text(
            f"✅ کاربر {user_id} ({user.first_name or 'بدون نام'}) مسدود شد."
        )


@require_admin
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "🔓 **فرمت دستور:**\n"
            "`/unban user_id`\n\n"
            "مثال:\n"
            "`/unban 123456789`"
        )
        return
    
    user_id = int(context.args[0])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(f"❌ کاربر با شناسه {user_id} یافت نشد.")
            return
        
        if not user.is_banned:
            await update.message.reply_text(f"⚠️ کاربر {user_id} مسدود نیست.")
            return
        
        # Unban the user
        user.is_banned = False
        user.is_active = True
        await session.commit()
        
        await update.message.reply_text(
            f"✅ کاربر {user_id} ({user.first_name or 'بدون نام'}) آزاد شد."
        )
