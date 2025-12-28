"""
Callback query handlers
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, User
from src.services.price_service import PriceService
from src.services.news_service import NewsService
from src.utils.keyboards import get_main_keyboard, get_price_keyboard, get_admin_keyboard
from src.utils.formatters import format_price, format_change

logger = logging.getLogger(__name__)
price_service = PriceService()
news_service = NewsService()

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Update user activity
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if db_user:
            db_user.last_active = datetime.utcnow()
            db_user.message_count += 1
            await session.commit()
    
    # Route callbacks
    if data == "menu_main":
        await show_main_menu(query)
    elif data == "menu_prices":
        await show_price_menu(query)
    elif data == "price_gold":
        await show_gold_prices(query)
    elif data == "price_currency":
        await show_currency_prices(query)
    elif data == "admin_stats":
        await show_admin_stats(query)
    elif data == "admin_channels":
        await show_admin_channels(query)
    else:
        await query.edit_message_text(
            "⚠️ این دکمه دیگر فعال نیست.",
            reply_markup=get_main_keyboard()
        )

async def show_main_menu(query):
    """Show main menu"""
    welcome_text = (
        "🎉 **به ربات MarketPulse Pro خوش آمدید!**\n\n"
        "💎 **ویژگی‌های ربات:**\n"
        "• قیمت لحظه‌ای طلا و ارز\n"
        "• اخبار اقتصادی\n"
        "• مدیریت کاربران\n\n"
        "📊 برای شروع از دکمه‌های زیر استفاده کنید:"
    )
    
    await query.edit_message_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def show_price_menu(query):
    """Show price menu"""
    message = "📊 **قیمت‌های لحظه‌ای**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:"
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=get_price_keyboard()
    )

async def show_gold_prices(query):
    """Show gold prices"""
    try:
        gold_data = await price_service.get_gold_prices()
        
        message = "🏅 **اطلاعات طلا**\n\n"
        
        if gold_data:
            message += f"• **طلای 18 عیار:** {format_price(gold_data.get('gold_18k', 0))}\n"
            message += f"• **طلای 24 عیار:** {format_price(gold_data.get('gold_24k', 0))}\n"
            message += f"• **انس جهانی:** ${gold_data.get('ounce', 0):,.2f}\n"
        else:
            message += "⚠️ اطلاعات در دسترس نیست"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_prices")]
        ])
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing gold prices: {e}")
        await query.edit_message_text(
            "⚠️ خطا در دریافت اطلاعات طلا.",
            reply_markup=get_price_keyboard()
        )

async def show_currency_prices(query):
    """Show currency prices"""
    try:
        currency_data = await price_service.get_currency_prices()
        
        message = "💵 **نرخ ارز**\n\n"
        
        if currency_data:
            message += f"• **دلار:** {format_price(currency_data.get('usd', 0))}\n"
            message += f"• **یورو:** {format_price(currency_data.get('eur', 0))}\n"
            message += f"• **پوند:** {format_price(currency_data.get('gbp', 0))}\n"
        else:
            message += "⚠️ اطلاعات در دسترس نیست"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_prices")]
        ])
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing currency prices: {e}")
        await query.edit_message_text(
            "⚠️ خطا در دریافت اطلاعات ارز.",
            reply_markup=get_price_keyboard()
        )

async def show_admin_stats(query):
    """Show admin statistics"""
    from datetime import datetime
    
    async with AsyncSessionLocal() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
    
    stats_text = (
        "📊 **آمار مدیر**\n\n"
        f"👥 کاربران کل: {total_users or 0}\n"
        f"✅ کاربران فعال: {active_users or 0}\n\n"
        f"🕐 آخرین آپدیت: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
    ])
    
    await query.edit_message_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def show_admin_channels(query):
    """Show admin channels"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Channel).order_by(Channel.created_at.desc())
        )
        channels = result.scalars().all()
    
    if not channels:
        message = "📭 هیچ کانالی ثبت نشده است."
    else:
        message = "📢 **کانال‌های اجباری**\n\n"
        for i, channel in enumerate(channels, 1):
            status = "✅ فعال" if channel.is_active else "❌ غیرفعال"
            message += f"{i}. **{channel.username}**\n"
            message += f"   وضعیت: {status}\n\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
    ])
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
