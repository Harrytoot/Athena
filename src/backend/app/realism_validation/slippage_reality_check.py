import math
from dataclasses import dataclass, field

from app.execution.execution_report import ExecutionReport
from app.strategy_robustness.stress_tester import StressTestResult

REALISTIC_SLIPPAGE_STRESS_LOW_BPS = 5.0
REALISTIC_SLIPPAGE_STRESS_HIGH_BPS = 80.0
REALISTIC_SLIPPAGE_NORMAL_LOW_BPS = 1.0
REALISTIC_SLIPPAGE_NORMAL_HIGH_BPS = 20.0
MAX_REALISTIC_AMPLIFICATION = 10.0
MIN_REALISTIC_AMPLIFICATION = 1.1
REALISTIC_AMPLIFICATION_IDEAL = 3.0


@dataclass
class SlippageRealityResult:
    category: str
    avg_slippage_bps: float
    max_slippage_bps: float
    amplification_vs_baseline: float
    is_realistic: bool
    details: str


@dataclass
class SlippageRealityReport:
    baseline: SlippageRealityResult = field(
        default_factory=lambda: SlippageRealityResult(
            category="normal",
            avg_slippage_bps=0.0,
            max_slippage_bps=0.0,
            amplification_vs_baseline=1.0,
            is_realistic=True,
            details="",
        )
    )
    stress: SlippageRealityResult = field(
        default_factory=lambda: SlippageRealityResult(
            category="stress",
            avg_slippage_bps=0.0,
            max_slippage_bps=0.0,
            amplification_vs_baseline=1.0,
            is_realistic=False,
            details="",
        )
    )
    amplification_ratio: float = 1.0
    realistic_range: tuple[float, float] = (1.0, 10.0)
    assessment: str = ""


class SlippageRealityChecker:

    def __init__(self, seed: int | None = None):
        self.seed = seed

    def check(
        self,
        execution_report: ExecutionReport,
        stress_results: list[StressTestResult],
    ) -> SlippageRealityReport:
        baseline_avg = execution_report.quality.avg_slippage_bps
        baseline_max = execution_report.quality.max_slippage_bps

        stress_avg_slippage, stress_max_slippage = self._estimate_stress_slippage(
            stress_results
        )

        baseline = self._build_baseline_result(baseline_avg, baseline_max)
        stress = self._build_stress_result(stress_avg_slippage, stress_max_slippage, baseline_avg)

        amplification = 1.0
        if baseline_avg > 0:
            amplification = stress_avg_slippage / baseline_avg
        elif stress_avg_slippage > 0:
            amplification = MAX_REALISTIC_AMPLIFICATION

        realistic_range = self._compute_realistic_range(baseline_avg)

        assessment = self._assess(baseline, stress, amplification)

        return SlippageRealityReport(
            baseline=baseline,
            stress=stress,
            amplification_ratio=round(amplification, 4),
            realistic_range=realistic_range,
            assessment=assessment,
        )

    def _build_baseline_result(
        self, avg_bps: float, max_bps: float
    ) -> SlippageRealityResult:
        is_realistic = (
            avg_bps >= REALISTIC_SLIPPAGE_NORMAL_LOW_BPS
            and avg_bps <= REALISTIC_SLIPPAGE_NORMAL_HIGH_BPS
        )
        details = (
            f"正常市场: 平均滑点 {avg_bps:.1f}bps, 最大 {max_bps:.1f}bps"
        )
        if avg_bps == 0 and max_bps == 0:
            is_realistic = False
            details += " — 零滑点不真实"
        elif avg_bps < REALISTIC_SLIPPAGE_NORMAL_LOW_BPS and avg_bps > 0:
            is_realistic = False
            details += f" — 低于{REALISTIC_SLIPPAGE_NORMAL_LOW_BPS}bps下限"
        elif avg_bps > REALISTIC_SLIPPAGE_NORMAL_HIGH_BPS:
            is_realistic = False
            details += f" — 高于{REALISTIC_SLIPPAGE_NORMAL_HIGH_BPS}bps上限"

        return SlippageRealityResult(
            category="normal",
            avg_slippage_bps=round(avg_bps, 2),
            max_slippage_bps=round(max_bps, 2),
            amplification_vs_baseline=1.0,
            is_realistic=is_realistic,
            details=details,
        )

    def _build_stress_result(
        self, avg_bps: float, max_bps: float, baseline_avg: float
    ) -> SlippageRealityResult:
        is_realistic = (
            avg_bps >= REALISTIC_SLIPPAGE_STRESS_LOW_BPS
            and avg_bps <= REALISTIC_SLIPPAGE_STRESS_HIGH_BPS
        )
        amplification = avg_bps / baseline_avg if baseline_avg > 0 else float("inf")

        details = (
            f"压力市场: 平均滑点 {avg_bps:.1f}bps, 最大 {max_bps:.1f}bps"
        )
        if avg_bps < REALISTIC_SLIPPAGE_STRESS_LOW_BPS:
            is_realistic = False
            details += (
                f" — 压力下滑点{avg_bps:.1f}bps低于现实下限"
                f"{REALISTIC_SLIPPAGE_STRESS_LOW_BPS}bps，模型低估了压力下的交易成本"
            )
        elif avg_bps > REALISTIC_SLIPPAGE_STRESS_HIGH_BPS:
            is_realistic = False
            details += (
                f" — 压力下滑点{avg_bps:.1f}bps高于现实上限"
                f"{REALISTIC_SLIPPAGE_STRESS_HIGH_BPS}bps，模型可能过度悲观"
            )
        elif baseline_avg > 0 and amplification < MIN_REALISTIC_AMPLIFICATION:
            is_realistic = False
            details += (
                f" — 放大倍率 {amplification:.1f}x 过低，"
                f"压力下滑点应至少放大{MIN_REALISTIC_AMPLIFICATION}x"
            )
        elif baseline_avg > 0 and amplification > MAX_REALISTIC_AMPLIFICATION:
            is_realistic = False
            details += (
                f" — 放大倍率 {amplification:.1f}x 过高，"
                f"超出{MAX_REALISTIC_AMPLIFICATION}x合理上限"
            )

        return SlippageRealityResult(
            category="stress",
            avg_slippage_bps=round(avg_bps, 2),
            max_slippage_bps=round(max_bps, 2),
            amplification_vs_baseline=round(amplification, 4)
            if amplification != float("inf")
            else 0.0,
            is_realistic=is_realistic,
            details=details,
        )

    def _estimate_stress_slippage(
        self, stress_results: list[StressTestResult]
    ) -> tuple[float, float]:
        if not stress_results:
            return 0.0, 0.0

        returns = [abs(r.total_return) for r in stress_results if r.survived]
        max_drawdowns = [abs(r.max_drawdown) for r in stress_results if r.survived]

        if not returns:
            avg_total_return = 0.0
            max_dd = 0.0
        else:
            avg_total_return = sum(returns) / len(returns)
            max_dd = max(max_drawdowns) if max_drawdowns else 0.0

        stress_factor = 1.0 + avg_total_return * 2.0 + max_dd * 5.0
        stress_factor = max(2.0, min(15.0, stress_factor))

        avg_slippage = 5.0 * stress_factor
        max_slippage = avg_slippage * 3.0

        return round(avg_slippage, 2), round(max_slippage, 2)

    def _compute_realistic_range(
        self, baseline_bps: float
    ) -> tuple[float, float]:
        low = REALISTIC_SLIPPAGE_STRESS_LOW_BPS
        high = REALISTIC_SLIPPAGE_STRESS_HIGH_BPS
        if baseline_bps > 0:
            low = max(REALISTIC_SLIPPAGE_STRESS_LOW_BPS, baseline_bps * MIN_REALISTIC_AMPLIFICATION)
            high = min(
                REALISTIC_SLIPPAGE_STRESS_HIGH_BPS,
                baseline_bps * MAX_REALISTIC_AMPLIFICATION,
            )
        return round(low, 2), round(high, 2)

    def _assess(
        self,
        baseline: SlippageRealityResult,
        stress: SlippageRealityResult,
        amplification: float,
    ) -> str:
        parts: list[str] = []

        if baseline.is_realistic and stress.is_realistic:
            parts.append("滑点真实度: 高")
        elif baseline.is_realistic or stress.is_realistic:
            parts.append("滑点真实度: 中")
        else:
            parts.append("滑点真实度: 低")

        parts.append(f"压力放大倍率: {amplification:.1f}x")
        if amplification >= 2.0 and amplification <= 6.0:
            parts.append("放大效应: 合理")
        elif amplification < 2.0:
            parts.append("放大效应: 偏低")
        else:
            parts.append("放大效应: 偏高")

        return " | ".join(parts)
