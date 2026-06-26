import math
from dataclasses import dataclass, field
from datetime import datetime

from app.portfolio.weight_optimizer import WeightResult
from app.portfolio.allocator import AllocationResult, CapitalAllocation

TRADING_DAYS = 252.0


@dataclass
class RebalanceAction:
    strategy_id: str
    action: str
    from_capital: float
    to_capital: float
    delta: float
    delta_pct: float


@dataclass
class RebalanceResult:
    actions: list[RebalanceAction] = field(default_factory=list)
    triggered: bool = False
    trigger_reason: str = ""
    total_turnover: float = 0.0
    turnover_ratio: float = 0.0
    previous_weights: list[float] = field(default_factory=list)
    target_weights: list[float] = field(default_factory=list)

    @property
    def action_count(self) -> int:
        return len(self.actions)

    @property
    def max_single_trade(self) -> float:
        if not self.actions:
            return 0.0
        return max(abs(a.delta_pct) for a in self.actions)


class Rebalancer:

    def __init__(
        self,
        drift_threshold: float = 0.05,
        calendar_frequency_days: int = 20,
        volatility_scale_factor: float = 1.0,
    ):
        self.drift_threshold = drift_threshold
        self.calendar_frequency_days = calendar_frequency_days
        self.volatility_scale_factor = volatility_scale_factor

    def check(
        self,
        current_allocations: list[CapitalAllocation],
        target_weights: WeightResult,
        last_rebalance_date: datetime | None = None,
        current_date: datetime | None = None,
        recent_volatility: float | None = None,
    ) -> RebalanceResult:
        if not current_allocations or not target_weights.weights:
            return RebalanceResult()

        prev_map = {a.strategy_id: a.weight for a in current_allocations}
        target_map = {w.strategy_id: nw for w, nw in zip(target_weights.weights, target_weights.normalized_weights)}

        all_ids = set(prev_map.keys()) | set(target_map.keys())
        prev_weights = [prev_map.get(sid, 0.0) for sid in all_ids]
        target_ws = [target_map.get(sid, 0.0) for sid in all_ids]
        ids = list(all_ids)

        drift = self._compute_drift(prev_weights, target_ws)

        triggered = False
        reasons: list[str] = []

        effective_threshold = self.drift_threshold
        if recent_volatility is not None:
            effective_threshold = self.drift_threshold * (
                1.0 + recent_volatility * self.volatility_scale_factor
            )

        if drift > effective_threshold:
            triggered = True
            reasons.append(f"drift:{drift:.4f}>{effective_threshold:.4f}")

        if last_rebalance_date and current_date:
            days_since = (current_date - last_rebalance_date).days
            if days_since >= self.calendar_frequency_days:
                if not triggered:
                    triggered = True
                reasons.append(f"calendar:{days_since}>={self.calendar_frequency_days}")

        actions: list[RebalanceAction] = []
        total_turnover = 0.0
        total_weight = sum(target_ws)
        total_weight = total_weight if total_weight > 0 else 1.0

        for sid, prev_w, target_w in zip(ids, prev_weights, target_ws):
            delta = target_w - prev_w
            action = "hold"
            if delta > 0.001:
                action = "buy"
            elif delta < -0.001:
                action = "sell"

            delta_pct = abs(delta) / total_weight if total_weight > 0 else 0.0
            total_turnover += delta_pct

            actions.append(
                RebalanceAction(
                    strategy_id=sid,
                    action=action,
                    from_capital=0.0,
                    to_capital=0.0,
                    delta=round(delta, 6),
                    delta_pct=round(delta_pct, 6),
                )
            )

        return RebalanceResult(
            actions=actions,
            triggered=triggered,
            trigger_reason=";".join(reasons) if reasons else "",
            total_turnover=round(total_turnover, 6),
            turnover_ratio=round(total_turnover / 2.0, 6) if total_turnover > 0 else 0.0,
            previous_weights=[round(w, 6) for w in prev_weights],
            target_weights=[round(w, 6) for w in target_ws],
        )

    def _compute_drift(self, prev_weights: list[float], target_weights: list[float]) -> float:
        if not prev_weights:
            return 0.0
        total_deviation = sum(abs(p - t) for p, t in zip(prev_weights, target_weights))
        return total_deviation / 2.0
