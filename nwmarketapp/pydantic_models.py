from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class ItemPriceHistory(BaseModel):
    scan_time: datetime
    price: Decimal
    quantity: int


class ItemSummary(BaseModel):
    grouped_hist: List[ItemPriceHistory]
    recent_lowest_price: Decimal
    price_change: Decimal
    price_change_text: str  # todo: property
    recent_price_time: datetime
    lowest_10_raw: List[ItemPriceHistory]
    item_name: str
