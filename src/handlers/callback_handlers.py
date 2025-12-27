"""
Callback query handlers
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, User
from src.services.price_service import PriceService
from src.services.news_service import NewsService
from src.services.channel_service import ChannelService
from src.utils.keyboards import (
    get_main_keyboard,
    get_price_keyboard,
    get_admin_keyboard
)
from src.utils.formatters import format_price, format_change

logger = logging.getLogger(__name__)
price_service = PriceService()
news_service = NewsService()
channel_service = ChannelService()


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()  # Always answer callback queries
    
    data = query.data
    user = query.from_user
    
    logger.debug(f"Callback from {user.id}: {data}")
    
    # Update user activity
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if db_user:
            db_user.last_active = datetime.utcnow()
            db_user.message_count += 1
            await session.commit()
    
    # Route based on callback data
    if data.startswith("menu_"):
        await handle_menu_callback(query, data)
    
    elif data.startswith("price_"):
        await handle_price_callback(query, data)
    
    elif data.startswith("admin_"):
        await handle_admin_callback(query, data)
    
    elif data.startswith("check_membership"):
        await handle_check_membership(query)
    
    elif data.startswith("refresh_"):
        await handle_refresh_callback(query, data)
    
    elif data.startswith("toggle_"):
        await handle_toggle_callback(query, data)
    
    elif data.startswith("chart_"):
        await handle_chart_callback(query, data)
    
    elif data.startswith("alert_"):
        await handle_alert_callback(query, data)
    
    else:
        # Unknown callback
        await query.edit_message_text(
            "⚠️ این دکمه دیگر فعال نیست.",
            reply_markup=get_main_keyboard()
        )


async def handle_menu_callback(query, data: str):
    """Handle menu callbacks"""
    if data == "menu_main":
        await show_main_menu(query)
    
    elif data == "menu_prices":
        await show_price_menu(query)
    
    elif data == "menu_news":
        await show_news_menu(query)
    
    elif data == "menu_profile":
        await show_profile_menu(query)
    
    elif data == "menu_settings":
        await show_settings_menu(query)
    
    elif data == "menu_vip":
        await show_vip_menu(query)
    
    elif data == "menu_help":
        await show_help_menu(query)
    
    elif data == "menu_charts":
        await show_charts_menu(query)
    
    elif data == "menu_alerts":
        await show_alerts_menu(query)


async def handle_price_callback(query, data: str):
    """Handle price callbacks"""
    if data == "price_gold":
        await show_gold_prices(query)
    
    elif data == "price_currency":
        await show_currency_prices(query)
    
    elif data == "price_crypto":
        await show_crypto_prices(query)
    
    elif data == "price_all":
        await show_all_prices(query)
    
    elif data == "refresh_prices":
        await refresh_prices(query)


async def handle_admin_callback(query, data: str):
    """Handle admin callbacks"""
    from src.core.config import config
    
    # Check if user is admin
    if query.from_user.id not in config.ADMIN_IDS:
        await query.edit_message_text(
            "⛔ **دسترسی محدود!**\n"
            "این بخش فقط برای مدیران قابل دسترسی است.",
            parse_mode="Markdown"
        )
        return
    
    if data == "admin_stats":
        await show_admin_stats(query)
    
    elif data == "admin_users":
        await show_admin_users(query)
    
    elif data == "admin_channels":
        await show_admin_channels(query)
    
    elif data == "admin_broadcast":
        await show_admin_broadcast(query)
    
    elif data == "admin_settings":
        await show_admin_settings(query)
    
    elif data == "admin_refresh":
        await admin_refresh(query)
    
    elif data == "admin_export":
        await admin_export(query)


async def handle_check_membership(query):
    """Handle check membership callback"""
    user_id = query.from_user.id
    
    # Check membership
    has_joined = await channel_service.check_user_channels(user_id)
    
    if has_joined:
        await query.edit_message_text(
            "✅ **تبریک!**\n\n"
            "عضویت شما در کانال‌های مورد نیاز تأیید شد.\n"
            "اکنون می‌توانید از تمام امکانات ربات استفاده کنید.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        # Get required channels
        channels = await channel_service.get_required_channels()
        
        from src.utils.keyboards import get_channel_keyboard
        
        message = (
            "❌ **عضویت شما تأیید نشد!**\n\n"
            "لطفاً در کانال‌های زیر عضو شوید:\n\n"
        )
        
        for i, channel in enumerate(channels, 1):
            message += f"{i}. {channel.username}\n"
        
        message += "\nپس از عضویت، دکمه 'بررسی عضویت' را بزنید."
        
        keyboard = get_channel_keyboard(channels)
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


async def show_main_menu(query):
    """Show main menu"""
    welcome_text = (
        "🎉 **به ربات MarketPulse Pro خوش آمدید!**\n\n"
        "💎 **ویژگی‌های ربات:**\n"
        "• قیمت لحظه‌ای طلا و ارز\n"
        "• قیمت ارزهای دیجیتال\n"
        "• اخبار اقتصادی ایران و جهان\n"
        "• تحلیل و نمودار قیمت‌ها\n\n"
        "📊 برای شروع از دکمه‌های زیر استفاده کنید:"
    )
    
    await query.edit_message_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


async def show_price_menu(query):
    """Show price menu"""
    message = "📊 **قیمت‌های لحظه‌ای**\n\n"
    message += "لطفاً یکی از گزینه‌ها را انتخاب کنید:"
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=get_price_keyboard()
    )


async def show_gold_prices(query):
    """Show gold prices"""
    try:
        gold_data = await price_service.get_gold_prices()
        
        message = "🏅 **اطلاعات کامل طلا**\n\n"
        
        if gold_data:
            message += f"• **طلای 18 عیار:** {format_price(gold_data.get('gold_18k', 0))}\n"
            message += f"• **طلای 24 عیار:** {format_price(gold_data.get('gold_24k', 0))}\n"
            message += f"• **انس جهانی:** ${gold_data.get('ounce', 0):,.2f}\n"
            message += f"• **سکه امامی:** {format_price(gold_data.get('coin_emami', 0))}\n"
            message += f"• **تغییرات:** {format_change(gold_data.get('gold_change_24h', 0))}\n"
        else:
            message += "⚠️ اطلاعات در دسترس نیست"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 نمودار طلا", callback_data="chart_gold")],
            [InlineKeyboardButton("🔔 هشدار قیمت", callback_data="alert_gold")],
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


async def show_news_menu(query):
    """Show news menu"""
    try:
        news_items = await news_service.get_latest_news(limit=3)
        
        if not news_items:
            message = "📰 **اخبار اقتصادی**\n\n"
            message += "در حال حاضر هیچ خبر جدیدی موجود نیست."
        else:
            message = "📰 **آخرین اخبار اقتصادی**\n\n"
            
            for i, news in enumerate(news_items, 1):
                title = news['title'][:80] + "..." if len(news['title']) > 80 else news['title']
                message += f"{i}. **{title}**\n"
                message += f"   📰 {news['source']}\n\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📰 اخبار بیشتر", callback_data="more_news")],
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_news")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
        ])
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing news menu: {e}")
        await query.edit_message_text(
            "⚠️ خطا در دریافت اخبار.",
            reply_markup=get_main_keyboard()
        )


async def refresh_prices(query):
    """Refresh prices"""
    # Clear cache
    price_service.cache.clear()
    
    # Show loading
    await query.edit_message_text(
        "🔄 در حال بروزرسانی قیمت‌ها...",
        reply_markup=None
    )
    
    # Get fresh prices
    await show_price_menu(query)


async def show_admin_stats(query):
    """Show admin statistics"""
    from src.core.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from datetime import datetime, timedelta
    
    async with AsyncSessionLocal() as session:
        # User stats
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        vip_users = await session.scalar(
            select(func.count(User.id)).where(User.is_vip == True)
        )
        
        # Today's users
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        today_users = await session.scalar(
            select(func.count(User.id)).where(User.join_date >= today_start)
        )
    
    stats_text = (
        "📊 **آمار مدیر**\n\n"
        
        "👥 **کاربران:**\n"
        f"• کل: {total_users:,}\n"
        f"• فعال: {active_users:,}\n"
        f"• VIP: {vip_users:,}\n"
        f"• امروز: {today_users:,}\n\n"
        
        "📈 **رشد:**\n"
        f"• میانگین روزانه: {today_users:,}\n\n"
        
        "🕐 **آخرین آپدیت:**\n"
        f"• زمان: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_refresh")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
    ])
    
    await query.edit_message_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# Add more callback handlers as needed...

async def show_profile_menu(query):
    """Show profile menu"""
    from src.handlers.user_handlers import profile_command
    from telegram import Update
    from unittest.mock import Mock
    
    # Create a mock update
    mock_update = Mock()
    mock_update.effective_user = query.from_user
    mock_update.message = Mock()
    mock_update.message.reply_text = query.edit_message_text
    mock_update.message.from_user = query.from_user
    
    await profile_command(mock_update, None)


async def show_settings_menu(query):
    """Show settings menu"""
    from src.handlers.user_handlers import settings_command
    from telegram import Update
    from unittest.mock import Mock
    
    # Create a mock update
    mock_update = Mock()
    mock_update.effective_user = query.from_user
    mock_update.message = Mock()
    mock_update.message.reply_text = query.edit_message_text
    mock_update.message.from_user = query.from_user
    
    await settings_command(mock_update, None)


async def show_vip_menu(query):
    """Show VIP menu"""
    from src.handlers.user_handlers import vip_command
    from telegram import Update
    from unittest.mock import Mock
    
    # Create a mock update
    mock_update = Mock()
    mock_update.effective_user = query.from_user
    mock_update.message = Mock()
    mock_update.message.reply_text = query.edit_message_text
    mock_update.message.from_user = query.from_user
    
    await vip_command(mock_update, None)
