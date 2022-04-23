from datetime import date, datetime
from decimal import Decimal

from dateutil.parser import isoparse
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def price_change_html(price_change: Decimal, price_change_date: date) -> str:
    if not price_change_date:
        return ""
    date_str = price_change_date.strftime("%x")
    text_class = "yellow_text" if not price_change or price_change <= 0 else "blue_text"
    increase_text = "decrease" if not price_change or price_change <= 0 else "increase"
    return mark_safe(f'<span class="{text_class}">{price_change}% {increase_text}</span> since {date_str}')


def fromisoformat(dt_str: str) -> datetime:
    return isoparse(dt_str).strftime('%x %I:%M %p')


register.simple_tag(price_change_html)
register.simple_tag(fromisoformat)
