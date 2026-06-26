from dataclasses import dataclass
from datetime import datetime

from app.strategy.signal_mapper import SizedSignal

DEFAULT_BASE_ALLOCATION = 1.0


@dataclass
class StrategyPosition:
    timestamp: datetime
    direction: int
    signal_weight: float
    position_pct: float
    notional: float


class PositionSizer:

    def __init__(self, base_allocation: float = DEFAULT_BASE_ALLOCATION):
        self.base_allocation = base_allocation

    def size(self, signal: SizedSignal, nav: float = 1.0) -> StrategyPosition:
        position_pct = signal.direction * signal.weight * self.base_allocation
        notional = position_pct * nav
        return StrategyPosition(
            timestamp=signal.timestamp,
            direction=signal.direction,
            signal_weight=signal.weight,
            position_pct=round(position_pct, 6),
            notional=round(notional, 2),
        )

    def size_all(
        self,
        signals: list[SizedSignal],
        nav_series: list[float] | None = None,
    ) -> list[StrategyPosition]:
        if nav_series is None:
            return [self.size(s) for s in signals]
        if len(signals) != len(nav_series):
            return [self.size(s) for s in signals]
        return [self.size(s, nav=nav_series[i]) for i, s in enumerate(signals)]
