"""
Text formatting utilities
"""

from datetime import datetime
from typing import Union, Optional


def format_price(price: Union[float, int]) -> str:
    """Format price with Persian formatting"""
    if not price:
        return "نامشخص"
    
    try:
        # Format with thousand separators
        return f"{price:,.0f}".replace(",", "٬") + " تومان"
    except (ValueError, TypeError):
        return "نامشخص"


def format_change(change: float) -> str:
    """Format percentage change"""
    if not change:
        return "۰٫۰٪"
    
    try:
        change = float(change)
        symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        
        # Format with Persian numbers
        persian_digits = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
        formatted = f"{abs(change):.2f}".translate(persian_digits)
        
        return f"{symbol} {formatted}٪"
    except (ValueError, TypeError):
        return "➡️ ۰٫۰٪"


def format_date(date_obj: datetime) -> str:
    """Format datetime object to Persian date string"""
    if not date_obj:
        return "نامشخص"
    
    try:
        # Convert to Persian month names
        month_names = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد",
            4: "تیر", 5: "مرداد", 6: "شهریور",
            7: "مهر", 8: "آبان", 9: "آذر",
            10: "دی", 11: "بهمن", 12: "اسفند"
        }
        
        # Jalali conversion (simplified)
        # Note: This is a simplified version. For production, use libraries like jdatetime
        gregorian_year = date_obj.year
        gregorian_month = date_obj.month
        gregorian_day = date_obj.day
        
        # Simple conversion (not accurate)
        jalali_year = gregorian_year - 621
        jalali_month = (gregorian_month + 2) % 12 + 1
        jalali_day = gregorian_day
        
        month_name = month_names.get(jalali_month, "نامشخص")
        
        # Format time
        time_str = date_obj.strftime("%H:%M")
        
        # Convert to Persian numbers
        persian_digits = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
        jalali_day_str = str(jalali_day).translate(persian_digits)
        jalali_year_str = str(jalali_year).translate(persian_digits)
        time_str = time_str.translate(persian_digits)
        
        return f"{jalali_day_str} {month_name} {jalali_year_str} - {time_str}"
        
    except Exception:
        # Fallback to simple format
        return date_obj.strftime("%Y/%m/%d %H:%M")


def format_number(number: Union[int, float]) -> str:
    """Format number with thousand separators"""
    try:
        # Format with Persian separators
        formatted = f"{number:,.0f}".replace(",", "٬")
        # Convert to Persian digits
        persian_digits = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
        return formatted.translate(persian_digits)
    except (ValueError, TypeError):
        return "۰"


def format_currency(amount: float, currency: str = "تومان") -> str:
    """Format currency amount"""
    formatted_number = format_number(amount)
    return f"{formatted_number} {currency}"


def format_time_ago(date_obj: datetime) -> str:
    """Format time difference as 'X time ago' in Persian"""
    if not date_obj:
        return "نامشخص"
    
    now = datetime.utcnow()
    diff = now - date_obj
    
    # Convert to Persian
    persian_digits = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{str(years).translate(persian_digits)} سال پیش"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{str(months).translate(persian_digits)} ماه پیش"
    elif diff.days > 7:
        weeks = diff.days // 7
        return f"{str(weeks).translate(persian_digits)} هفته پیش"
    elif diff.days > 0:
        return f"{str(diff.days).translate(persian_digits)} روز پیش"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{str(hours).translate(persian_digits)} ساعت پیش"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{str(minutes).translate(persian_digits)} دقیقه پیش"
    else:
        return "همین الآن"
