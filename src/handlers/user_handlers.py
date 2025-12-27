"""
User command handlers
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, User
from src.services.price_service import PriceService
from src.services.news_service import NewsService
from src.services.channel_service import ChannelService
from src.utils.decorators import require_subscription
from src.utils.keyboards import (
    get_main_keyboard,
    get_price_keyboard,
    get_profile_keyboard
)
from src.utils.formatters import format_price, format_change, format_date

logger = logging.getLogger(__name__)
price_service = PriceService()
news_service = NewsService()
channel_service = ChannelService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"New user: {user.id} - {user.username}")
    
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            # Create new user
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
                join_date=datetime.utcnow(),
                last_active=datetime.utcnow()
            )
            session.add(db_user)
            await session.commit()
            logger.info(f"Created new user: {user.id}")
        
        else:
            # Update last active
            db_user.last_active = datetime.utcnow()
            db_user.message_count += 1
            await session.commit()
    
    # Check if user has joined required channels
    has_joined = await channel_service.check_user_channels(user.id)
    
    if not has_joined:
        # Show welcome message with channel requirement
        channels = await channel_service.get_required_channels()
        
        if channels:
            keyboard = []
            for channel in channels[:3]:  # Show max 3 channels
                keyboard.append([
                    InlineKeyboardButton(
                        f"📢 عضویت در {channel.username}",
                        url=f"https://t.me/{channel.username[1:]}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = (
                "🎉 **به ربات MarketPulse Pro خوش آمدید!**\n\n"
                "برای استفاده از ربات، لطفاً در کانال‌های زیر عضو شوید:\n"
                "پس از عضویت، دکمه 'بررسی عضویت' را بزنید."
            )
            
            await update.message.reply_text(
                welcome_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
    
    # User has joined channels or no channels required
    welcome_text = (
        "🎉 **به ربات MarketPulse Pro خوش آمدید!**\n\n"
        "💎 **ویژگی‌های ربات:**\n"
        "• قیمت لحظه‌ای طلا و ارز\n"
        "• قیمت ارزهای دیجیتال\n"
        "• اخبار اقتصادی ایران و جهان\n"
        "• تحلیل و نمودار قیمت‌ها\n\n"
        "📊 برای شروع از دکمه‌های زیر استفاده کنید:"
    )
    
    reply_markup = get_main_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📚 **راهنمای ربات MarketPulse Pro**\n\n"
        "🔹 **دستورات اصلی:**\n"
        "/start - راه‌اندازی ربات\n"
        "/prices - قیمت‌های لحظه‌ای\n"
        "/gold - اطلاعات کامل طلا\n"
        "/crypto - ارزهای دیجیتال\n"
        "/news - اخبار اقتصادی\n"
        "/profile - پروفایل کاربری\n"
        "/vip - اطلاعات اشتراک ویژه\n"
        "/settings - تنظیمات\n\n"
        
        "🔹 **نحوه استفاده:**\n"
        "1. برای مشاهده قیمت‌ها از منوی قیمت استفاده کنید\n"
        "2. اخبار به صورت خودکار هر ساعت آپدیت می‌شود\n"
        "3. برای دریافت هشدار قیمت، روی دکمه هشدار بزنید\n\n"
        
        "🔹 **پشتیبانی:**\n"
        "برای گزارش مشکل یا پیشنهاد:\n"
        "@MarketPulseSupport"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


@require_subscription
async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /prices command"""
    try:
        # Fetch prices
        prices = await price_service.get_all_prices()
        
        message = "📊 **قیمت‌های لحظه‌ای**\n\n"
        
        # Gold
        if "gold_18k" in prices:
            gold_change = prices.get("gold_change_24h", 0)
            message += f"🏅 **طلای 18 عیار:** {format_price(prices['gold_18k'])}\n"
            message += f"📈 تغییرات 24h: {format_change(gold_change)}\n\n"
        
        # USD
        if "usd" in prices:
            usd_change = prices.get("usd_change_24h", 0)
            message += f"💵 **دلار:** {format_price(prices['usd'])}\n"
            message += f"📈 تغییرات 24h: {format_change(usd_change)}\n\n"
        
        # Bitcoin
        if "bitcoin" in prices:
            btc_change = prices.get("bitcoin_change_24h", 0)
            message += f"₿ **بیت‌کوین:** ${prices['bitcoin']:,.0f}\n"
            message += f"📈 تغییرات 24h: {format_change(btc_change)}\n\n"
        
        message += f"🕐 آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
        
        # Send with keyboard
        keyboard = get_price_keyboard()
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in prices_command: {e}")
        await update.message.reply_text(
            "⚠️ خطا در دریافت قیمت‌ها. لطفاً دوباره تلاش کنید."
        )


@require_subscription
async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gold command"""
    try:
        gold_data = await price_service.get_gold_prices()
        
        message = "🏅 **اطلاعات کامل طلا**\n\n"
        
        if gold_data:
            message += f"• **طلای 18 عیار:** {format_price(gold_data.get('18k', 0))}\n"
            message += f"• **طلای 24 عیار:** {format_price(gold_data.get('24k', 0))}\n"
            message += f"• **انس جهانی:** ${gold_data.get('ounce', 0):,.2f}\n"
            message += f"• **سکه امامی:** {format_price(gold_data.get('coin_emami', 0))}\n"
            message += f"• **تغییرات 24h:** {format_change(gold_data.get('change_24h', 0))}\n"
        else:
            message += "⚠️ اطلاعات در دسترس نیست"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 نمودار طلا", callback_data="chart_gold")],
            [InlineKeyboardButton("🔔 هشدار قیمت", callback_data="alert_gold")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in gold_command: {e}")
        await update.message.reply_text(
            "⚠️ خطا در دریافت اطلاعات طلا."
        )


@require_subscription
async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /crypto command"""
    try:
        cryptos = await price_service.get_crypto_prices(limit=5)
        
        message = "💰 **ارزهای دیجیتال برتر**\n\n"
        
        for i, crypto in enumerate(cryptos, 1):
            symbol = crypto['symbol'].upper()
            price = crypto['price']
            change = crypto['change_24h']
            
            message += f"{i}. **{symbol}**: ${price:,.2f}\n"
            message += f"   تغییرات: {format_change(change)}\n\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 نمودار BTC", callback_data="chart_btc")],
            [InlineKeyboardButton("📈 نمودار ETH", callback_data="chart_eth")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in crypto_command: {e}")
        await update.message.reply_text(
            "⚠️ خطا در دریافت اطلاعات ارزهای دیجیتال."
        )


@require_subscription
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /news command"""
    try:
        news_items = await news_service.get_latest_news(limit=3)
        
        if not news_items:
            await update.message.reply_text("📰 هیچ خبر جدیدی موجود نیست.")
            return
        
        message = "📰 **آخرین اخبار اقتصادی**\n\n"
        
        for i, news in enumerate(news_items, 1):
            title = news['title'][:100] + "..." if len(news['title']) > 100 else news['title']
            time = format_date(news['published'])
            
            message += f"{i}. **{title}**\n"
            message += f"   ⏰ {time}\n"
            message += f"   📰 {news['source']}\n\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📰 اخبار بیشتر", callback_data="more_news")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in news_command: {e}")
        await update.message.reply_text(
            "⚠️ خطا در دریافت اخبار."
        )


@require_subscription
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("⚠️ کاربر یافت نشد.")
            return
        
        # Format join date
        join_date = db_user.join_date.strftime("%Y/%m/%d") if db_user.join_date else "نامشخص"
        last_active = db_user.last_active.strftime("%Y/%m/%d %H:%M") if db_user.last_active else "نامشخص"
        
        # VIP status
        vip_status = "✅ فعال" if db_user.is_vip else "❌ غیرفعال"
        trial_status = "✅ استفاده شده" if db_user.free_trial_used else "✅ قابل استفاده"
        
        message = (
            "👤 **پروفایل کاربری**\n\n"
            f"🆔 **شناسه:** {db_user.telegram_id}\n"
            f"👤 **نام:** {db_user.first_name or ''} {db_user.last_name or ''}\n"
            f"🔗 **نام کاربری:** @{db_user.username or 'ندارد'}\n"
            f"📅 **تاریخ عضویت:** {join_date}\n"
            f"🕐 **آخرین فعالیت:** {last_active}\n"
            f"💬 **تعداد پیام‌ها:** {db_user.message_count}\n\n"
            
            "💎 **وضعیت اشتراک:**\n"
            f"• VIP: {vip_status}\n"
            f"• تست رایگان: {trial_status}\n\n"
            
            "⚙️ **تنظیمات:**\n"
            f"• اعلان‌ها: {'✅ فعال' if db_user.notifications_enabled else '❌ غیرفعال'}\n"
            f"• وضعیت: {'✅ فعال' if db_user.is_active else '❌ غیرفعال'}"
        )
        
        keyboard = get_profile_keyboard(db_user)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vip command"""
    from src.core.config import config
    
    vip_text = (
        "👑 **اشتراک ویژه VIP**\n\n"
        "با اشتراک VIP از مزایای زیر بهره‌مند شوید:\n\n"
        
        "✅ **مزایا:**\n"
        "• حذف تمام تبلیغات\n"
        "• دسترسی به تحلیل‌های پیشرفته\n"
        "• نمودارهای حرفه‌ای‌تر\n"
        "• اعلان‌های فوری قبل از عموم\n"
        "• پشتیبانی اختصاصی\n\n"
        
        "💰 **قیمت:**\n"
        f"ماهیانه: {config.VIP_PRICE:,} تومان\n\n"
        
        "🆓 **تست رایگان:**\n"
        f"{config.FREE_TRIAL_DAYS} روز تست رایگان برای کاربران جدید\n\n"
        
        "برای فعالسازی VIP با پشتیبانی تماس بگیرید:\n"
        "@MarketPulseSupport"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
    ])
    
    await update.message.reply_text(
        vip_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("⚠️ کاربر یافت نشد.")
            return
        
        settings_text = (
            "⚙️ **تنظیمات کاربری**\n\n"
            "در این بخش می‌توانید تنظیمات ربات را تغییر دهید.\n\n"
            
            f"🔔 **اعلان‌ها:** {'✅ فعال' if db_user.notifications_enabled else '❌ غیرفعال'}\n"
            f"🌟 **نمادهای موردعلاقه:** {len(db_user.favorite_symbols)} عدد\n\n"
            
            "برای تغییر تنظیمات از دکمه‌های زیر استفاده کنید:"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'🔕 غیرفعال کردن' if db_user.notifications_enabled else '🔔 فعال کردن'} اعلان‌ها",
                    callback_data="toggle_notifications"
                )
            ],
            [InlineKeyboardButton("🌟 مدیریت علاقه‌مندی‌ها", callback_data="manage_favorites")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile")]
        ])
        
        await update.message.reply_text(
            settings_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user = update.effective_user
    text = update.message.text
    
    logger.info(f"Message from {user.id}: {text}")
    
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
    
    # Simple echo for now
    await update.message.reply_text(
        "🤖 لطفاً از دستورات یا منوی ربات استفاده کنید.\n"
        "برای مشاهده دستورات /help را ارسال کنید."
    )
