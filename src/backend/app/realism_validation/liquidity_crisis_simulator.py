import math
import random
from dataclasses import dataclass, field

from app.execution.execution_report import ExecutionReport

CRISIS_STAGES = 8
LIQUIDITY_DECAY_RATE = 0.15
SPREAD_EXPANSION_FACTOR = 2.5
MIN_VIABLE_LIQUIDITY_PCT = 0.05
DEFAULT_BASE_LIQUIDITY = 1e8
RECOVERY_DAYS_BASE = 10
BREAKDOWN_THRESHOLD_DEFAULT = 0.10


@dataclass
class LiquidityCrisisStage:
    stage: int
    label: str
    liquidity_remaining_pct: float
    fill_rate: float
    slippage_bps: float
    spread_bps: float
    is_viable: bool
    description: str


@dataclass
class LiquidityCrisisReport:
    stages: list[LiquidityCrisisStage] = field(default_factory=list)
    breakdown_threshold_pct: float = BREAKDOWN_THRESHOLD_DEFAULT
    survival_probability: float = 0.0
    max_viable_position_pct: float = 0.0
    recovery_time_estimate_days: int = 0
    assessment: str = ""

    @property
    def total_stages(self) -> int:
        return len(self.stages)

    @property
    def viable_stages(self) -> int:
        return sum(1 for s in self.stages if s.is_viable)

    @property
    def worst_stage_slippage(self) -> float:
        if not self.stages:
            return 0.0
        return max(s.slippage_bps for s in self.stages)


class LiquidityCrisisSimulator:

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def simulate(
        self,
        execution_report: ExecutionReport,
        base_liquidity: float = DEFAULT_BASE_LIQUIDITY,
    ) -> LiquidityCrisisReport:
        baseline_fill = execution_report.fill_rate
        baseline_slippage = execution_report.quality.avg_slippage_bps
        baseline_spread = 2.0

        stages: list[LiquidityCrisisStage] = []
        breakdown_identified = False
        breakdown_threshold = BREAKDOWN_THRESHOLD_DEFAULT

        for i in range(CRISIS_STAGES):
            remaining = max(0.0, 1.0 - i * LIQUIDITY_DECAY_RATE)
            stage_index = i + 1
            label = self._stage_label(stage_index, remaining)

            fill_rate = self._compute_crisis_fill_rate(baseline_fill, remaining, stage_index)
            slippage = self._compute_crisis_slippage(baseline_slippage, remaining, stage_index)
            spread = self._compute_crisis_spread(baseline_spread, remaining, stage_index)

            is_viable = fill_rate > 0.05 and remaining > MIN_VIABLE_LIQUIDITY_PCT

            if not is_viable and not breakdown_identified:
                breakdown_identified = True
                breakdown_threshold = remaining + LIQUIDITY_DECAY_RATE

            description = self._describe_stage(label, fill_rate, slippage, spread, is_viable)

            stages.append(
                LiquidityCrisisStage(
                    stage=stage_index,
                    label=label,
                    liquidity_remaining_pct=round(remaining, 4),
                    fill_rate=round(fill_rate, 4),
                    slippage_bps=round(slippage, 2),
                    spread_bps=round(spread, 2),
                    is_viable=is_viable,
                    description=description,
                )
            )

        survival_prob = self._compute_survival_probability(stages)
        max_viable_position = self._compute_max_viable_position(stages)
        recovery_days = self._estimate_recovery_days(stages)

        assessment = self._assess(survival_prob, max_viable_position, stages)

        return LiquidityCrisisReport(
            stages=stages,
            breakdown_threshold_pct=round(breakdown_threshold, 4),
            survival_probability=round(survival_prob, 4),
            max_viable_position_pct=round(max_viable_position, 4),
            recovery_time_estimate_days=recovery_days,
            assessment=assessment,
        )

    def _stage_label(self, index: int, remaining: float) -> str:
        if remaining >= 0.85:
            return "正常"
        if remaining >= 0.70:
            return "轻度紧张"
        if remaining >= 0.55:
            return "中度紧张"
        if remaining >= 0.40:
            return "流动性收缩"
        if remaining >= 0.25:
            return "流动性短缺"
        if remaining >= 0.10:
            return "流动性危机"
        if remaining > 0:
            return "接近枯竭"
        return "完全枯竭"

    def _compute_crisis_fill_rate(
        self, baseline_fill: float, remaining: float, stage: int
    ) -> float:
        if baseline_fill <= 0:
            baseline_fill = 0.90

        fill = baseline_fill * remaining
        cascade_factor = 1.0 - (stage - 1) * 0.04
        fill *= max(0.0, cascade_factor)

        noise = self._rng.gauss(0, 0.01)
        fill += noise

        return max(0.0, min(1.0, fill))

    def _compute_crisis_slippage(
        self, baseline_slippage: float, remaining: float, stage: int
    ) -> float:
        if baseline_slippage <= 0:
            baseline_slippage = 5.0

        inverse_liquidity = 1.0 / max(0.01, remaining)
        slippage = baseline_slippage * inverse_liquidity * (1.0 + stage * 0.15)

        noise = self._rng.gauss(0, baseline_slippage * 0.1)
        slippage += noise

        return max(0.0, min(500.0, slippage))

    def _compute_crisis_spread(
        self, baseline_spread: float, remaining: float, stage: int
    ) -> float:
        spread = baseline_spread * (1.0 + stage * 0.3)
        if remaining < 0.3:
            spread *= SPREAD_EXPANSION_FACTOR

        noise = self._rng.gauss(0, baseline_spread * 0.1)
        spread += noise

        return max(baseline_spread, min(200.0, spread))

    def _describe_stage(
        self,
        label: str,
        fill_rate: float,
        slippage: float,
        spread: float,
        is_viable: bool,
    ) -> str:
        viable_text = "可交易" if is_viable else "不可交易"
        return (
            f"[{label}] 成交率: {fill_rate:.1%} | "
            f"滑点: {slippage:.1f}bps | 价差: {spread:.1f}bps | {viable_text}"
        )

    def _compute_survival_probability(
        self, stages: list[LiquidityCrisisStage]
    ) -> float:
        if not stages:
            return 0.0

        weights = [math.exp(-(s.stage - 1) * 0.2) for s in stages]
        total_weight = sum(weights)

        survival = 0.0
        for s, w in zip(stages, weights):
            if s.is_viable:
                survival += w / total_weight

        return round(survival, 4)

    def _compute_max_viable_position(
        self, stages: list[LiquidityCrisisStage]
    ) -> float:
        viable = [s for s in stages if s.is_viable]
        if not viable:
            return 0.01

        avg_fill = sum(s.fill_rate for s in viable) / len(viable)
        min_liquidity = min(s.liquidity_remaining_pct for s in viable)

        max_position = avg_fill * min_liquidity * 0.10
        return round(max(0.005, min(0.50, max_position)), 4)

    def _estimate_recovery_days(
        self, stages: list[LiquidityCrisisStage]
    ) -> int:
        breakdown_idx = None
        for i, s in enumerate(stages):
            if not s.is_viable:
                breakdown_idx = i
                break

        if breakdown_idx is None:
            return RECOVERY_DAYS_BASE - 5

        depth = 1.0 - stages[breakdown_idx].liquidity_remaining_pct
        recovery = int(RECOVERY_DAYS_BASE + depth * 30)
        return max(5, min(60, recovery))

    def _assess(
        self,
        survival_prob: float,
        max_position: float,
        stages: list[LiquidityCrisisStage],
    ) -> str:
        parts: list[str] = []

        if survival_prob >= 0.8:
            parts.append("流动性韧性: 高")
        elif survival_prob >= 0.5:
            parts.append("流动性韧性: 中")
        elif survival_prob >= 0.3:
            parts.append("流动性韧性: 低")
        else:
            parts.append("流动性韧性: 极低")

        parts.append(f"崩潰阈值: {stages[-1].liquidity_remaining_pct:.0%}")

        if max_position >= 0.10:
            parts.append(f"最大可行仓位: {max_position:.1%} (充裕)")
        elif max_position >= 0.05:
            parts.append(f"最大可行仓位: {max_position:.1%} (适中)")
        else:
            parts.append(f"最大可行仓位: {max_position:.1%} (受限)")

        return " | ".join(parts)
