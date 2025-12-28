"""
Keyboard utilities
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 قیمت‌ها", callback_data="menu_prices"),
            InlineKeyboardButton("📰 اخبار", callback_data="menu_news")
        ],
        [
            InlineKeyboardButton("👤 پروفایل", callback_data="menu_profile"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_price_keyboard():
    """Get price menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏅 طلا و سکه", callback_data="price_gold")],
        [InlineKeyboardButton("💵 ارز", callback_data="price_currency")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Get admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 آمار", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 کانال‌ها", callback_data="admin_channels")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
