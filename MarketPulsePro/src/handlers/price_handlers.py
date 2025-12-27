"""
Price Handlers
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.services.price_service import PriceService
from src.services.channel_service import ChannelService
from src.utils.formatters import format_price, format_change
from src.utils.keyboards import get_price_keyboard, get_crypto_keyboard
from src.utils.decorators import require_subscription, require_vip


logger = logging.getLogger(__name__)
price_service = PriceService()
channel_service = ChannelService()


@require_subscription
async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all prices"""
    user_id = update.effective_user.id
    
    try:
        # Fetch prices
        prices = await price_service.get_all_prices()
        
        # Format message
        message = "📊 **قیمت‌های لحظه‌ای**\n\n"
        
        # Gold
        gold = prices.get("gold", {})
        if gold:
            message += f"🏅 **طلا**\n"
            message += f"• ۱۸ عیار: {format_price(gold.get('18k'))}\n"
            message += f"• ۲۴ عیار: {format_price(gold.get('24k'))}\n"
            message += f"• انس جهانی: ${gold.get('ounce', 0):,.0f}\n"
            message += f"• تغییرات: {format_change(gold.get('change_24h', 0))}\n\n"
        
        # USD
        usd = prices.get("usd", {})
        if usd:
            message += f"💵 **دلار**\n"
            message += f"• قیمت: {format_price(usd.get('price'))}\n"
            message += f"• تغییر: {format_change(usd.get('change_24h', 0))}\n\n"
        
        # Bitcoin
        btc = prices.get("bitcoin", {})
        if btc:
            message += f"₿ **بیت‌کوین**\n"
            message += f"• قیمت: ${btc.get('price', 0):,.0f}\n"
            message += f"• تغییر ۲۴h: {format_change(btc.get('change_24h', 0))}\n"
        
        # Add timestamp
        message += f"\n⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
        
        # Send message with keyboard
        keyboard = get_price_keyboard()
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing prices: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت قیمت‌ها")


@require_subscription
async def show_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed gold prices"""
    try:
        gold_data = await price_service.get_gold_prices()
        
        message = "🏅 **اطلاعات کامل طلا**\n\n"
        
        # Iranian Gold
        message += "**ایران:**\n"
        message += f"• طلای ۱۸ عیار: {format_price(gold_data['18k'])}\n"
        message += f"• طلای ۲۴ عیار: {format_price(gold_data['24k'])}\n"
        message += f"• سکه امامی: {format_price(gold_data['coin_emami'])}\n"
        message += f"• سکه نیم: {format_price(gold_data['coin_nim'])}\n"
        message += f"• سکه ربع: {format_price(gold_data['coin_rob'])}\n"
        message += f"• سکه گرمی: {format_price(gold_data['coin_gerami'])}\n\n"
        
        # Global Gold
        message += "**جهانی:**\n"
        message += f"• انس طلا: ${gold_data['ounce']:,.2f}\n"
        message += f"• مثقال: ${gold_data['mithqal']:,.2f}\n"
        message += f"• گرم: ${gold_data['gram']:,.2f}\n\n"
        
        # Changes
        message += "**تغییرات:**\n"
        message += f"• ۲۴ ساعت: {format_change(gold_data['change_24h'])}\n"
        message += f"• ۷ روز: {format_change(gold_data['change_7d'])}\n"
        
        # Add chart button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 نمودار طلا", callback_data="chart_gold")],
            [InlineKeyboardButton("🔔 هشدار قیمت", callback_data="alert_gold")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_prices")]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing gold: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت اطلاعات طلا")


@require_subscription
async def show_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cryptocurrency prices"""
    try:
        cryptos = await price_service.get_crypto_prices()
        
        message = "💰 **ارزهای دیجیتال**\n\n"
        
        for crypto in cryptos[:10]:  # Show top 10
            symbol = crypto['symbol'].upper()
            name = crypto['name']
            price = crypto['price']
            change = crypto['change_24h']
            
            message += f"**{symbol}** ({name})\n"
            message += f"• قیمت: ${price:,.2f}\n"
            message += f"• تغییر: {format_change(change)}\n\n"
        
        # Send with keyboard
        keyboard = get_crypto_keyboard()
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing crypto: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت اطلاعات ارزهای دیجیتال")


@require_subscription
@require_vip
async def show_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show price chart"""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "📊 لطفاً نماد مورد نظر را وارد کنید:\n"
            "مثال: `/chart gold` یا `/chart btc`"
        )
        return
    
    symbol = args[0].lower()
    
    try:
        # Generate chart
        chart_path = await price_service.generate_chart(symbol, period="7d")
        
        if chart_path:
            # Send chart image
            with open(chart_path, 'rb') as photo:
                caption = f"📈 نمودار {symbol.upper()}\nدوره: ۷ روز اخیر"
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption
                )
        else:
            await update.message.reply_text("⚠️ نمودار برای این نماد موجود نیست")
            
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        await update.message.reply_text("⚠️ خطا در تولید نمودار")