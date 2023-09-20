# custom_filters.py

from django import template
from book.models import BookNote
from datetime import date, timedelta

register = template.Library()

@register.filter
def get_booknote(book, user):
    return book.booknotes.filter(user=user).first()

@register.filter(name='format_date')
def format_date(value):
    # Check if the value is a date object
    if isinstance(value, date):
        day = value.day
        month = value.strftime("%B")
        year = value.year

        # Add the "st," "nd," "rd," or "th" suffix to the day
        if 10 <= day % 100 <= 20:
            day_str = str(day) + "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            day_str = str(day) + suffix

        return f"{day_str} {month}, {year}"

    return value

@register.filter
def add_timedelta(value, days):
    if value is not None:
        return value + timedelta(days=days)
    return value