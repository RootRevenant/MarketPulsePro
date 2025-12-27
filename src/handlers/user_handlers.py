import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, User
from src.services.price_service import PriceService
from src.utils.decorators import require_subscription
from src.utils.keyboards import get_main_keyboard
from src.utils.formatters import format_price, format_change

logger = logging.getLogger(__name__)
price_service = PriceService()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"New user: {user.id} - {user.username}")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
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
            db_user.last_active = datetime.utcnow()
            db_user.message_count += 1
            await session.commit()
    
    welcome_text = (
        "🎉 **به ربات MarketPulse Pro خوش آمدید!**\n\n"
        "💎 **ویژگی‌های ربات:**\n"
        "• قیمت لحظه‌ای طلا و ارز\n"
        "• قیمت ارزهای دیجیتال\n"
        "• اخبار اقتصادی ایران و جهان\n\n"
        "📊 برای شروع از دکمه‌های زیر استفاده کنید:"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@require_subscription
async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prices = await price_service.get_all_prices()
        
        message = "📊 **قیمت‌های لحظه‌ای**\n\n"
        
        if "gold_18k" in prices:
            message += f"🏅 **طلای 18 عیار:** {format_price(prices['gold_18k'])}\n"
        if "usd" in prices:
            message += f"💵 **دلار:** {format_price(prices['usd'])}\n"
        
        message += f"\n🕐 آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
        
        from src.utils.keyboards import get_price_keyboard
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_price_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in prices_command: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت قیمت‌ها.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 **راهنمای ربات MarketPulse Pro**\n\n"
        "🔹 **دستورات اصلی:**\n"
        "/start - راه‌اندازی ربات\n"
        "/prices - قیمت‌های لحظه‌ای\n"
        "/help - راهنمای ربات\n\n"
        "🔹 **پشتیبانی:**\n"
        "برای گزارش مشکل:\n"
        "@MarketPulseSupport"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")