"""
Text formatting utilities
"""

from datetime import datetime

def format_price(price):
    """Format price with Persian formatting"""
    if not price:
        return "نامشخص"
    try:
        return f"{price:,.0f}".replace(",", "٬") + " تومان"
    except:
        return "نامشخص"

def format_change(change):
    """Format percentage change"""
    if not change:
        return "۰٫۰٪"
    try:
        change = float(change)
        symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        return f"{symbol} {abs(change):.2f}٪"
    except:
        return "➡️ ۰٫۰٪"

def format_date(date_obj):
    """Format datetime object"""
    if not date_obj:
        return "نامشخص"
    try:
        return date_obj.strftime("%Y/%m/%d %H:%M")
    except:
        return "نامشخص"
