from decimal import Decimal


def get_price_change_percent(current: Decimal, previous: Decimal) -> Decimal:
    if current == previous:
        return 0
    try:
        return ((current - previous) / previous) * Decimal("100.0")
    except ZeroDivisionError:
        return 0
