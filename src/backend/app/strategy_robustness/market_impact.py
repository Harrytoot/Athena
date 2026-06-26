import math
from dataclasses import dataclass, field
from datetime import datetime

from app.strategy.portfolio_builder import PortfolioHistory
from app.strategy.risk_manager import RiskResult


@dataclass
class ImpactConfig:
    impact_coefficient: float = 0.1
    sqroot_alpha: float = 0.5
    daily_volume_estimate: float = 1e8
    max_impact_bps: float = 100.0


@dataclass
class ImpactEstimate:
    timestamp: datetime
    trade_size_pct: float
    trade_notional: float
    participation_rate: float
    impact_bps: float
    impact_amount: float


class MarketImpactModel:

    def __init__(self, config: ImpactConfig | None = None):
        self.config = config or ImpactConfig()

    def estimate(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
    ) -> list[ImpactEstimate]:
        snapshots = history.snapshots
        positions = risk_result.positions
        n = min(len(snapshots), len(positions))
        if n < 2:
            return []

        estimates: list[ImpactEstimate] = []
        for i in range(1, n):
            prev_pct = positions[i - 1].adjusted_position_pct
            curr_pct = positions[i].adjusted_position_pct
            trade_size = curr_pct - prev_pct

            if abs(trade_size) < 1e-10:
                estimates.append(
                    ImpactEstimate(
                        timestamp=snapshots[i].timestamp,
                        trade_size_pct=0.0,
                        trade_notional=0.0,
                        participation_rate=0.0,
                        impact_bps=0.0,
                        impact_amount=0.0,
                    )
                )
                continue

            nav = snapshots[i - 1].nav
            trade_notional = abs(trade_size) * nav

            participation_rate = trade_notional / self.config.daily_volume_estimate

            impact_fraction = (
                self.config.impact_coefficient
                * (participation_rate ** self.config.sqroot_alpha)
            )
            impact_bps = impact_fraction * 10000.0
            impact_bps = min(impact_bps, self.config.max_impact_bps)

            impact_amount = trade_notional * (impact_bps / 10000.0)

            estimates.append(
                ImpactEstimate(
                    timestamp=snapshots[i].timestamp,
                    trade_size_pct=round(trade_size, 6),
                    trade_notional=round(trade_notional, 2),
                    participation_rate=round(participation_rate, 8),
                    impact_bps=round(impact_bps, 4),
                    impact_amount=round(impact_amount, 4),
                )
            )

        return estimates

    def total_impact(self, estimates: list[ImpactEstimate]) -> float:
        return round(sum(e.impact_amount for e in estimates), 4)

    def impact_ratio(self, history: PortfolioHistory, estimates: list[ImpactEstimate]) -> float:
        total = self.total_impact(estimates)
        if history.initial_nav == 0:
            return 0.0
        return round(total / abs(history.initial_nav), 8)

    def sensitivity_analysis(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
        volume_multipliers: list[float] | None = None,
    ) -> dict[str, float]:
        if volume_multipliers is None:
            volume_multipliers = [0.1, 0.5, 1.0, 2.0, 5.0]

        results: dict[str, float] = {}

        for mult in volume_multipliers:
            adjusted_config = ImpactConfig(
                impact_coefficient=self.config.impact_coefficient,
                sqroot_alpha=self.config.sqroot_alpha,
                daily_volume_estimate=self.config.daily_volume_estimate * mult,
                max_impact_bps=self.config.max_impact_bps,
            )
            temp_model = MarketImpactModel(config=adjusted_config)
            estimates = temp_model.estimate(history, risk_result)
            total = sum(e.impact_amount for e in estimates)
            nav = history.initial_nav
            pct = total / nav if nav > 0 else 0.0
            results[f"{mult}x_volume"] = round(pct, 8)

        return results
