from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    RANGE = "range"
    VOLATILE = "volatile"


@dataclass(frozen=True)
class MarketSnapshot:
    index_code: str
    index_name: str
    current_point: Decimal
    change_pct: Decimal
    change_amount: Decimal
    volume: Decimal
    amount: Decimal
    update_time: Optional[datetime] = None


@dataclass(frozen=True)
class HotSector:
    sector_name: str
    change_pct: Decimal
    leader_stock: str = ""
    leader_change_pct: Optional[Decimal] = None


@dataclass(frozen=True)
class AiMarketSummary:
    regime: MarketRegime
    confidence: float
    summary: str
    key_observation: str = ""
    risk_warning: str = ""


@dataclass(frozen=True)
class MarketOverview:
    regime: MarketRegime
    summary: str
    indices: list[MarketSnapshot] = field(default_factory=list)
    hot_sectors: list[HotSector] = field(default_factory=list)
    rise_count: int = 0
    fall_count: int = 0
    limit_up_count: int = 0
    limit_down_count: int = 0
    ai_summary: Optional[AiMarketSummary] = None
    updated_at: Optional[datetime] = None
