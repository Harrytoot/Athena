import math
from dataclasses import dataclass, field
from datetime import datetime

from app.strategy.portfolio_builder import PortfolioHistory, PortfolioSnapshot
from app.strategy.risk_manager import RiskResult


@dataclass
class SlippageConfig:
    base_spread_bps: float = 1.0
    vol_sensitivity: float = 0.1
    max_slippage_bps: float = 50.0


@dataclass
class SlippageEstimate:
    timestamp: datetime
    trade_size_pct: float
    daily_volatility: float
    slippage_bps: float
    slippage_pct: float
    effective_slippage: float


class SlippageModel:

    def __init__(self, config: SlippageConfig | None = None):
        self.config = config or SlippageConfig()

    def estimate(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
    ) -> list[SlippageEstimate]:
        snapshots = history.snapshots
        positions = risk_result.positions
        n = min(len(snapshots), len(positions))
        if n < 2:
            return []

        daily_vol = self._compute_rolling_volatility(history.daily_returns)

        estimates: list[SlippageEstimate] = []
        for i in range(1, n):
            prev_pct = positions[i - 1].adjusted_position_pct
            curr_pct = positions[i].adjusted_position_pct
            trade_size = abs(curr_pct - prev_pct)

            vol = daily_vol[i] if i < len(daily_vol) else 0.0

            slippage_bps = self.config.base_spread_bps
            if trade_size > 1e-10 and vol > 0:
                slippage_bps += self.config.vol_sensitivity * vol * 10000 * trade_size

            slippage_bps = min(slippage_bps, self.config.max_slippage_bps)
            slippage_pct = slippage_bps / 10000.0

            effective = 0.0
            if trade_size > 1e-10:
                nav = snapshots[i - 1].nav
                effective = trade_size * nav * slippage_pct

            estimates.append(
                SlippageEstimate(
                    timestamp=snapshots[i].timestamp,
                    trade_size_pct=round(trade_size, 6),
                    daily_volatility=round(vol, 6),
                    slippage_bps=round(slippage_bps, 4),
                    slippage_pct=round(slippage_pct, 8),
                    effective_slippage=round(effective, 4),
                )
            )

        return estimates

    def sensitivity_analysis(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
        vol_multipliers: list[float] | None = None,
    ) -> dict[str, float]:
        if vol_multipliers is None:
            vol_multipliers = [0.5, 1.0, 2.0, 3.0, 5.0]

        results: dict[str, float] = {}

        for mult in vol_multipliers:
            adjusted_config = SlippageConfig(
                base_spread_bps=self.config.base_spread_bps * mult,
                vol_sensitivity=self.config.vol_sensitivity,
                max_slippage_bps=self.config.max_slippage_bps * mult,
            )
            temp_model = SlippageModel(config=adjusted_config)
            estimates = temp_model.estimate(history, risk_result)
            total_slippage = sum(e.effective_slippage for e in estimates)
            nav = history.initial_nav
            pct = total_slippage / nav if nav > 0 else 0.0
            results[f"{mult}x_spread"] = round(pct, 8)

        return results

    def total_slippage_impact(self, estimates: list[SlippageEstimate]) -> float:
        return round(sum(e.effective_slippage for e in estimates), 4)

    def _compute_rolling_volatility(
        self, daily_returns: list[float], window: int = 20
    ) -> list[float]:
        n = len(daily_returns)
        if n < 2:
            return [0.0] * n

        vols: list[float] = []
        for i in range(n):
            start = max(0, i - window + 1)
            sub_returns = daily_returns[start : i + 1]
            if len(sub_returns) < 2:
                vols.append(0.0)
            else:
                mean_r = sum(sub_returns) / len(sub_returns)
                variance = sum((r - mean_r) ** 2 for r in sub_returns) / (len(sub_returns) - 1)
                vols.append(math.sqrt(variance) if variance > 0 else 0.0)
        return vols
