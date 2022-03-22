from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Type, Union

from pydantic import BaseModel, root_validator

from nwmarketapp.models import Prices
from nwmarketapp.utils import get_price_change_percent


class ItemPriceHistory(BaseModel):
    name: str
    scan_time: datetime
    price: Decimal
    quantity: int

    @root_validator(pre=False)
    def validate(cls: Type["ItemPriceHistory"], price_obj: Union[Dict, Prices]):
        if "scan_time" in price_obj:
            return price_obj
        return cls(
            name=price_obj["name"],
            scan_time=price_obj["timestamp"],
            price=price_obj["price"],
            quantity=price_obj["avail"] or 0
        )


class ItemSummary(BaseModel):
    grouped_hist: List[List[ItemPriceHistory]]
    recent_lowest_price: Decimal
    price_change: Decimal = Decimal("0")
    price_change_text: str = "Not Enough Data"
    recent_price_time: datetime
    lowest_10_raw: List[ItemPriceHistory]
    item_name: str

    @root_validator(pre=True)
    def root_validator(cls, values: dict) -> dict:
        grouped_hist = values["grouped_hist"]
        price_change_values = {}
        if len(grouped_hist) <= 1:
            return values

        prev_lowest = grouped_hist[-2]
        prev_date = prev_lowest[0]["timestamp_date"]
        prev_lowest_price_f = min([price["price"] for price in prev_lowest])
        prev_lowest_price = Decimal(format(prev_lowest_price_f, ".15g"))

        price_change = get_price_change_percent(values["recent_lowest_price"], prev_lowest_price)
        price_change_percent = round(price_change)
        price_change_values["price_change"] = round(price_change)
        price_change_template = '<span class="{color}_text">{change_percent}% increase</span> since {prev_date}'
        price_change_values["price_change_text"] = price_change_template.format(
            color="blue" if price_change >= 0 else "yellow",
            change_percent=price_change_percent,
            prev_date=prev_date.strftime("%x")
        )

        return {**values, **price_change_values}
