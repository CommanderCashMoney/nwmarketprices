from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Union

from pydantic import BaseModel, root_validator

from nwmarketapp.models import Prices


class ItemPriceHistory(BaseModel):
    scan_time: datetime
    price: Decimal

    @root_validator
    def validate(cls, price_obj: Union[Dict, Prices]):
        if isinstance(price_obj, dict):
            return price_obj
        return cls(scan_time=price_obj.timestamp, price=price_obj.price)


class ItemSummary(BaseModel):
    grouped_hist: List[List[ItemPriceHistory]]
    recent_lowest_price: Decimal
    price_change: Decimal
    price_change_text: str  # todo: property
    recent_price_time: datetime
    lowest_10_raw: List[ItemPriceHistory]
    item_name: str
