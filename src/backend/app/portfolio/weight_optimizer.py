import math
from dataclasses import dataclass, field

from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.robustness_report import RobustnessReport

DEFAULT_MAX_WEIGHT = 0.50
DEFAULT_MIN_WEIGHT = 0.05
DEFAULT_RISK_AVERSION = 1.0


@dataclass
class StrategyWeight:
    strategy_id: str
    raw_sharpe: float
    cost_adjusted_sharpe: float
    volatility: float
    stability_score: float
    raw_weight: float
    constrained_weight: float
    risk_budget: float = 0.0
    capped: bool = False
    cap_reason: str = ""


@dataclass
class WeightResult:
    weights: list[StrategyWeight] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(w.constrained_weight for w in self.weights)

    @property
    def normalized_weights(self) -> list[float]:
        total = self.total_weight
        if total == 0:
            return [0.0] * len(self.weights)
        return [w.constrained_weight / total for w in self.weights]

    @property
    def weighted_sharpe(self) -> float:
        norm = self.normalized_weights
        sharpes = [w.cost_adjusted_sharpe for w in self.weights]
        return sum(w * s for w, s in zip(norm, sharpes))

    @property
    def concentration_ratio(self) -> float:
        norm = self.normalized_weights
        if not norm:
            return 0.0
        return sum(w ** 2 for w in norm)

    @property
    def effective_n(self) -> float:
        cr = self.concentration_ratio
        if cr == 0:
            return 0.0
        return 1.0 / cr


class WeightOptimizer:

    def __init__(
        self,
        max_weight: float = DEFAULT_MAX_WEIGHT,
        min_weight: float = DEFAULT_MIN_WEIGHT,
        risk_aversion: float = DEFAULT_RISK_AVERSION,
        min_acceptable_sharpe: float = -1.0,
    ):
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.risk_aversion = risk_aversion
        self.min_acceptable_sharpe = min_acceptable_sharpe

    def optimize(
        self,
        strategy_metrics: list[tuple[str, StrategyPerformanceReport, RobustnessReport]],
        regime_multipliers: dict[str, float] | None = None,
    ) -> WeightResult:
        if not strategy_metrics:
            return WeightResult()

        n = len(strategy_metrics)
        raw_weights = self._compute_raw_weights(strategy_metrics)

        if regime_multipliers:
            raw_weights = self._apply_regime_multipliers(
                strategy_metrics, raw_weights, regime_multipliers
            )

        constrained = self._apply_constraints(raw_weights)

        weights: list[StrategyWeight] = []
        for i, (sid, perf, robust) in enumerate(strategy_metrics):
            w = constrained[i]
            capped = abs(w - raw_weights[i]) > 1e-8
            cap_reason = ""
            if capped:
                reasons = []
                if w == self.max_weight and raw_weights[i] > self.max_weight:
                    reasons.append("concentration_cap")
                if w == self.min_weight and raw_weights[i] < self.min_weight:
                    reasons.append("min_weight_floor")
                if w == 0.0 and perf.sharpe_ratio < self.min_acceptable_sharpe:
                    reasons.append("sharpe_threshold")
                cap_reason = ",".join(reasons)

            cost_sharpe = robust.cost_metrics.cost_adjusted_sharpe
            stability = robust.overall_stability_score

            weights.append(
                StrategyWeight(
                    strategy_id=sid,
                    raw_sharpe=perf.sharpe_ratio,
                    cost_adjusted_sharpe=cost_sharpe,
                    volatility=perf.daily_volatility,
                    stability_score=stability,
                    raw_weight=raw_weights[i],
                    constrained_weight=w,
                    capped=capped,
                    cap_reason=cap_reason,
                )
            )

        return WeightResult(weights=weights)

    def _compute_raw_weights(
        self,
        strategy_metrics: list[tuple[str, StrategyPerformanceReport, RobustnessReport]],
    ) -> list[float]:
        n = len(strategy_metrics)
        scores = [0.0] * n

        for i, (sid, perf, robust) in enumerate(strategy_metrics):
            cost_sharpe = robust.cost_metrics.cost_adjusted_sharpe
            stability = robust.overall_stability_score

            sharpe_score = max(0.0, cost_sharpe)

            if perf.daily_volatility > 0:
                vol_score = 1.0 / (1.0 + perf.daily_volatility * math.sqrt(252))
            else:
                vol_score = 1.0

            calmar_score = 0.0
            if perf.calmar_ratio > 0:
                calmar_score = min(2.0, perf.calmar_ratio) / 2.0

            drawdown_score = 0.0
            if perf.max_drawdown < 0:
                drawdown_score = max(0.0, 1.0 + perf.max_drawdown)

            stability_score = stability

            combined = (
                0.30 * sharpe_score
                + 0.20 * vol_score
                + 0.15 * calmar_score
                + 0.15 * drawdown_score
                + 0.20 * stability_score
            )

            if perf.sharpe_ratio < self.min_acceptable_sharpe:
                combined = 0.0

            scores[i] = combined

        total = sum(scores)
        if total == 0:
            return [1.0 / n] * n

        return [s / total for s in scores]

    def _apply_constraints(self, raw_weights: list[float]) -> list[float]:
        n = len(raw_weights)
        result = list(raw_weights)

        for i in range(n):
            if result[i] < 0:
                result[i] = 0.0

        for iteration in range(20):
            excess_total = 0.0
            deficit_total = 0.0
            capped_count = 0
            uncapped_indices: list[int] = []
            uncapped_sum = 0.0

            for i in range(n):
                if result[i] > self.max_weight:
                    excess_total += result[i] - self.max_weight
                    result[i] = self.max_weight
                    capped_count += 1
                elif result[i] > 0 and result[i] < self.min_weight:
                    deficit_total += self.min_weight - result[i]
                    result[i] = self.min_weight
                    capped_count += 1
                else:
                    uncapped_indices.append(i)
                    uncapped_sum += result[i]

            if capped_count == 0:
                break

            if uncapped_indices and uncapped_sum > 1e-12:
                scale = (uncapped_sum + excess_total - deficit_total) / uncapped_sum
                for i in uncapped_indices:
                    result[i] *= scale
            elif not uncapped_indices:
                total = sum(result)
                if total > 0:
                    result = [w / total for w in result]
                break

        total = sum(result)
        if total > 1e-12:
            result = [w / total for w in result]

        return [round(w, 6) for w in result]

    def _normalize(self, weights: list[float]) -> list[float]:
        total = sum(weights)
        if total == 0:
            return weights
        return [w / total for w in weights]

    def _apply_regime_multipliers(
        self,
        strategy_metrics: list[tuple[str, StrategyPerformanceReport, RobustnessReport]],
        raw_weights: list[float],
        regime_multipliers: dict[str, float],
    ) -> list[float]:
        adjusted = []
        for i, (sid, perf, robust) in enumerate(strategy_metrics):
            multiplier = regime_multipliers.get(sid, 1.0)
            adjusted.append(raw_weights[i] * multiplier)

        total = sum(adjusted)
        if total == 0:
            return raw_weights
        return [w / total for w in adjusted]
