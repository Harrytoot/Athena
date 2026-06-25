from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Stock:
    code: str
    name: str
    exchange: str = ""
    sector: str = ""
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    pb_ratio: Optional[Decimal] = None

    @property
    def listing_status(self) -> str:
        if self.market_cap and self.market_cap > 0:
            return "listed"
        return "unknown"


@dataclass(frozen=True)
class StockPrice:
    code: str
    trade_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    amount: Decimal
    change_pct: Optional[Decimal] = None
    change_amount: Optional[Decimal] = None
