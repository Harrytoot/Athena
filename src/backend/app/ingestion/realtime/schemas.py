from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MarketTick:
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: float
    turnover: float
    high: float
    low: float
    open: float
    pre_close: float
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_volume: float = 0.0
    ask_volume: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BarData:
    symbol: str
    name: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    turnover: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
