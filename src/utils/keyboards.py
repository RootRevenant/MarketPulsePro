"""
Keyboard utilities
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from typing import List, Optional


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 قیمت‌ها", callback_data="menu_prices"),
            InlineKeyboardButton("📰 اخبار", callback_data="menu_news")
        ],
        [
            InlineKeyboardButton("📈 نمودارها", callback_data="menu_charts"),
            InlineKeyboardButton("🔔 هشدارها", callback_data="menu_alerts")
        ],
        [
            InlineKeyboardButton("👤 پروفایل", callback_data="menu_profile"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("💎 VIP", callback_data="menu_vip"),
            InlineKeyboardButton("🆘 راهنما", callback_data="menu_help")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_price_keyboard() -> InlineKeyboardMarkup:
    """Get price menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🏅 طلا و سکه", callback_data="price_gold"),
            InlineKeyboardButton("💵 ارز", callback_data="price_currency")
        ],
        [
            InlineKeyboardButton("💰 ارز دیجیتال", callback_data="price_crypto"),
            InlineKeyboardButton("📊 همه قیمت‌ها", callback_data="price_all")
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_prices"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_profile_keyboard(user) -> InlineKeyboardMarkup:
    """Get profile keyboard based on user status"""
    keyboard = []
    
    # Add VIP button if not VIP
    if not user.is_vip:
        keyboard.append([InlineKeyboardButton("💎 ارتقاء به VIP", callback_data="upgrade_vip")])
    
    # Add notification toggle
    notification_text = "🔕 غیرفعال کردن اعلان‌ها" if user.notifications_enabled else "🔔 فعال کردن اعلان‌ها"
    keyboard.append([InlineKeyboardButton(notification_text, callback_data="toggle_notifications")])
    
    # Add other buttons
    keyboard.append([
        InlineKeyboardButton("⭐ علاقه‌مندی‌ها", callback_data="favorites"),
        InlineKeyboardButton("📊 آمار من", callback_data="my_stats")
    ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📢 کانال‌ها", callback_data="admin_channels"),
            InlineKeyboardButton("📨 ارسال همگانی", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings"),
            InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton("📥 خروجی", callback_data="admin_export"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_channel_keyboard(channels) -> InlineKeyboardMarkup:
    """Get keyboard for channel list"""
    keyboard = []
    
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"📢 {channel.username}",
                url=f"https://t.me/{channel.username[1:]}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership"),
        InlineKeyboardButton("🔄 تلاش مجدد", callback_data="refresh_channels")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Get pagination keyboard"""
    keyboard = []
    
    # Previous button
    if current_page > 1:
        keyboard.append(
            InlineKeyboardButton("◀️", callback_data=f"{prefix}_page:{current_page-1}")
        )
    
    # Page number
    keyboard.append(
        InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
    )
    
    # Next button
    if current_page < total_pages:
        keyboard.append(
            InlineKeyboardButton("▶️", callback_data=f"{prefix}_page:{current_page+1}")
        )
    
    return InlineKeyboardMarkup([keyboard])


def get_confirm_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """Get confirmation keyboard"""
    callback_data = f"{action}_confirm:{data}" if data else f"{action}_confirm"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data=callback_data),
            InlineKeyboardButton("❌ لغو", callback_data=f"{action}_cancel")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)
