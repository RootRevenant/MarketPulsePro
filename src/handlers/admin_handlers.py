"""
Admin command handlers
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, User, Channel
from src.utils.decorators import require_admin

logger = logging.getLogger(__name__)

@require_admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    admin_text = (
        "👑 **پنل مدیریت**\n\n"
        "🔧 **دستورات:**\n"
        "/stats - آمار ربات\n"
        "/users - لیست کاربران\n"
        "/channels - لیست کانال‌ها\n\n"
        "برای بازگشت به منوی اصلی /start را بزنید."
    )
    
    await update.message.reply_text(admin_text, parse_mode="Markdown")

@require_admin
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    async with AsyncSessionLocal() as session:
        # User stats
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        vip_users = await session.scalar(
            select(func.count(User.id)).where(User.is_vip == True)
        )
        
        # Channel stats
        channel_count = await session.scalar(select(func.count(Channel.id)))
    
    stats_text = (
        "📊 **آمار ربات**\n\n"
        f"👥 کاربران کل: {total_users or 0}\n"
        f"✅ کاربران فعال: {active_users or 0}\n"
        f"👑 کاربران VIP: {vip_users or 0}\n"
        f"📢 کانال‌ها: {channel_count or 0}\n\n"
        f"🕐 تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
    )
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

@require_admin
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).order_by(User.join_date.desc()).limit(10)
        )
        users = result.scalars().all()
    
    if not users:
        await update.message.reply_text("👥 هیچ کاربری یافت نشد.")
        return
    
    message = "👥 **آخرین کاربران**\n\n"
    
    for i, user in enumerate(users, 1):
        status = "✅" if user.is_active else "❌"
        vip = "👑" if user.is_vip else ""
        
        message += f"{i}. {status} {vip} "
        message += f"**{user.first_name or 'بدون نام'}**\n"
        message += f"   🆔 {user.telegram_id}\n"
        message += f"   📅 {user.join_date.strftime('%Y/%m/%d')}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")
