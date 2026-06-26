import math
from dataclasses import dataclass, field
from datetime import datetime

from app.strategy.portfolio_builder import PortfolioHistory, PortfolioSnapshot
from app.strategy.risk_manager import RiskResult


@dataclass
class TransactionCostConfig:
    commission_rate: float = 0.0003
    stamp_duty_rate: float = 0.0005
    apply_stamp_duty_sell_only: bool = True
    min_commission: float = 5.0


@dataclass
class CostEvent:
    timestamp: datetime
    turnover: float
    commission: float
    stamp_duty: float
    total_cost: float


@dataclass
class CostAdjustedHistory:
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
    def total_return(self) -> float:
        if not self.snapshots:
            return 0.0
        start = self.snapshots[0].nav
        if start == 0:
            return 0.0
        return (self.snapshots[-1].nav - start) / start


class TransactionCostSimulator:

    def __init__(self, config: TransactionCostConfig | None = None):
        self.config = config or TransactionCostConfig()

    def simulate(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
    ) -> list[CostEvent]:
        snapshots = history.snapshots
        positions = risk_result.positions
        n = min(len(snapshots), len(positions))
        if n < 2:
            return []

        events: list[CostEvent] = []
        for i in range(1, n):
            prev_pct = positions[i - 1].adjusted_position_pct
            curr_pct = positions[i].adjusted_position_pct
            delta_pct = curr_pct - prev_pct

            if abs(delta_pct) < 1e-10:
                events.append(
                    CostEvent(
                        timestamp=snapshots[i].timestamp,
                        turnover=0.0,
                        commission=0.0,
                        stamp_duty=0.0,
                        total_cost=0.0,
                    )
                )
                continue

            nav = snapshots[i - 1].nav
            turnover = abs(delta_pct) * nav

            commission = turnover * self.config.commission_rate
            if commission < self.config.min_commission:
                commission = self.config.min_commission

            stamp_duty = 0.0
            if self.config.apply_stamp_duty_sell_only:
                if delta_pct < 0:
                    sell_amount = abs(delta_pct) * nav
                    stamp_duty = sell_amount * self.config.stamp_duty_rate
            else:
                stamp_duty = turnover * self.config.stamp_duty_rate

            total_cost = commission + stamp_duty

            events.append(
                CostEvent(
                    timestamp=snapshots[i].timestamp,
                    turnover=round(turnover, 2),
                    commission=round(commission, 4),
                    stamp_duty=round(stamp_duty, 4),
                    total_cost=round(total_cost, 4),
                )
            )

        return events

    def adjust_history(
        self,
        history: PortfolioHistory,
        cost_events: list[CostEvent],
    ) -> CostAdjustedHistory:
        snapshots = history.snapshots
        n = len(snapshots)
        if n < 2 or len(cost_events) < n - 1:
            return CostAdjustedHistory(snapshots=list(snapshots))

        adjusted: list[PortfolioSnapshot] = [snapshots[0]]
        cumulative_cost = 0.0

        for i in range(1, n):
            orig = snapshots[i]
            if i - 1 < len(cost_events):
                cumulative_cost += cost_events[i - 1].total_cost

            adj_nav = orig.nav - cumulative_cost
            if adj_nav < 0:
                adj_nav = 0.0

            prev_adj_nav = adjusted[i - 1].nav
            adj_daily_return = 0.0
            if prev_adj_nav != 0 and i > 0:
                adj_daily_return = (adj_nav - prev_adj_nav) / prev_adj_nav

            initial_nav = history.initial_nav
            adj_cumulative_return = 0.0
            if initial_nav != 0:
                adj_cumulative_return = (adj_nav - initial_nav) / initial_nav

            adjusted.append(
                PortfolioSnapshot(
                    timestamp=orig.timestamp,
                    position=orig.position,
                    price=orig.price,
                    nav=round(adj_nav, 2),
                    daily_return=round(adj_daily_return, 6),
                    cumulative_return=round(adj_cumulative_return, 6),
                    leverage=orig.leverage,
                    position_value=orig.position_value,
                )
            )

        return CostAdjustedHistory(snapshots=adjusted)

    def compute_cost_adjusted_sharpe(
        self,
        history: PortfolioHistory,
        cost_events: list[CostEvent],
        risk_free_rate: float = 0.02,
    ) -> float:
        TRADING_DAYS = 252.0
        snapshots = history.snapshots
        n = len(snapshots)
        if n < 2:
            return 0.0

        cost_by_idx: list[float] = [0.0]
        for i in range(1, n):
            if i - 1 < len(cost_events):
                cost_by_idx.append(cost_by_idx[-1] + cost_events[i - 1].total_cost)
            else:
                cost_by_idx.append(cost_by_idx[-1])

        daily_returns: list[float] = []
        for i in range(1, n):
            prev_nav = snapshots[i - 1].nav - (cost_by_idx[i - 1] if i - 1 < len(cost_by_idx) else 0)
            curr_nav = snapshots[i].nav - (cost_by_idx[i] if i < len(cost_by_idx) else 0)
            if prev_nav > 0:
                daily_returns.append((curr_nav - prev_nav) / prev_nav)

        if len(daily_returns) < 2:
            return 0.0

        mean_r = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_vol = math.sqrt(variance) if variance > 0 else 0.0

        if daily_vol == 0:
            return 0.0

        daily_rf = risk_free_rate / TRADING_DAYS
        daily_sharpe = (mean_r - daily_rf) / daily_vol
        return round(daily_sharpe * math.sqrt(TRADING_DAYS), 6)

    def compute_total_costs(self, cost_events: list[CostEvent]) -> float:
        return round(sum(e.total_cost for e in cost_events), 4)

    def cost_ratio(self, history: PortfolioHistory, cost_events: list[CostEvent]) -> float:
        total_cost = self.compute_total_costs(cost_events)
        if history.initial_nav == 0:
            return 0.0
        return round(total_cost / abs(history.initial_nav), 6)
