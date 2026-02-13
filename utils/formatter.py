"""
Formatting utilities for currency and dates
"""
from datetime import datetime
from typing import Union

def format_currency(amount: Union[int, float], currency: str = "IDR") -> str:
    """
    Format amount to Indonesian Rupiah format
    Example: 50000 -> "Rp 50.000"
    """
    if currency == "IDR":
        # Format with thousand separator
        formatted = f"{int(amount):,}".replace(',', '.')
        return f"Rp {formatted}"
    
    return f"{currency} {amount:,.2f}"

def format_date(date: datetime, format_type: str = "short") -> str:
    """
    Format datetime to readable Indonesian format
    
    Args:
        date: datetime object
        format_type: 'short', 'medium', 'long'
    """
    if format_type == "short":
        return date.strftime("%d/%m/%Y")
    elif format_type == "medium":
        return date.strftime("%d %b %Y")
    elif format_type == "long":
        return date.strftime("%d %B %Y, %H:%M")
    
    return date.strftime("%d/%m/%Y %H:%M")

def format_percentage(value: float) -> str:
    """Format percentage with 1 decimal"""
    return f"{value:.1f}%"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
