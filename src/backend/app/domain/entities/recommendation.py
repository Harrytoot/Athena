from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class RecommendationAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WATCH = "watch"


class RecommendationSource(str, Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    PORTFOLIO = "portfolio"
    MARKET = "market"
    DIVERSIFICATION = "diversification"


class RecommendationPriority(int, Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class RecommendationItem:
    symbol: str = ""
    name: str = ""
    action: RecommendationAction = RecommendationAction.WATCH
    priority: RecommendationPriority = RecommendationPriority.LOW
    source: RecommendationSource = RecommendationSource.MARKET
    confidence: Decimal = Decimal("0")
    reason: str = ""
    detail: Optional[str] = None


@dataclass
class Recommendation:
    id: Optional[str] = None
    generated_at: Optional[datetime] = None
    market_regime: str = ""
    market_temperature: int = 0
    items: list[RecommendationItem] = field(default_factory=list)
    summary: str = ""

    def add_item(self, item: RecommendationItem):
        self.items.append(item)
