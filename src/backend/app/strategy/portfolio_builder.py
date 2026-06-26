from dataclasses import dataclass, field
from datetime import datetime

from app.strategy.position_sizer import StrategyPosition

DEFAULT_INITIAL_NAV = 1_000_000.0


@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    position: StrategyPosition | None
    price: float
    nav: float
    daily_return: float
    cumulative_return: float
    leverage: float
    position_value: float = 0.0


@dataclass
class PortfolioHistory:
    snapshots: list[PortfolioSnapshot] = field(default_factory=list)

    @property
    def nav_series(self) -> list[float]:
        return [s.nav for s in self.snapshots]

    @property
    def daily_returns(self) -> list[float]:
        return [s.daily_return for s in self.snapshots]

    @property
    def cumulative_returns(self) -> list[float]:
        return [s.cumulative_return for s in self.snapshots]

    @property
    def initial_nav(self) -> float:
        if not self.snapshots:
            return DEFAULT_INITIAL_NAV
        return self.snapshots[0].nav

    @property
    def final_nav(self) -> float:
        if not self.snapshots:
            return DEFAULT_INITIAL_NAV
        return self.snapshots[-1].nav

    @property
    def total_return(self) -> float:
        if not self.snapshots:
            return 0.0
        start = self.initial_nav
        if start == 0:
            return 0.0
        return (self.final_nav - start) / start


class PortfolioBuilder:

    def __init__(self, initial_nav: float = DEFAULT_INITIAL_NAV):
        self.initial_nav = initial_nav

    def build(
        self,
        positions: list[StrategyPosition],
        prices: list[float],
    ) -> PortfolioHistory:
        n = len(positions)
        if n == 0 or n != len(prices):
            return PortfolioHistory()

        nav = self.initial_nav
        prev_nav = self.initial_nav
        snapshots: list[PortfolioSnapshot] = []

        for i, (pos, price) in enumerate(zip(positions, prices)):
            if i > 0 and prices[i - 1] != 0:
                prev_position_pct = positions[i - 1].position_pct
                price_return = (prices[i] - prices[i - 1]) / prices[i - 1]
                strategy_return = prev_position_pct * price_return
                nav = prev_nav * (1.0 + strategy_return)

            daily_return = 0.0
            if i > 0 and prev_nav != 0:
                daily_return = (nav - prev_nav) / prev_nav
            cumulative_return = 0.0
            if self.initial_nav != 0:
                cumulative_return = (nav - self.initial_nav) / self.initial_nav

            target_notional = pos.position_pct * nav
            position_value = target_notional

            snapshots.append(
                PortfolioSnapshot(
                    timestamp=pos.timestamp,
                    position=pos,
                    price=price,
                    nav=round(nav, 2),
                    daily_return=round(daily_return, 6),
                    cumulative_return=round(cumulative_return, 6),
                    leverage=round(abs(pos.position_pct), 6),
                    position_value=round(position_value, 2),
                )
            )
            prev_nav = nav

        return PortfolioHistory(snapshots=snapshots)
