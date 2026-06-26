import math
from dataclasses import dataclass, field

from app.execution.execution_report import ExecutionReport


@dataclass
class ExecutionGap:
    category: str
    simulated_value: float
    realistic_benchmark: float
    gap_ratio: float
    severity: str
    description: str


@dataclass
class ExecutionGapReport:
    gaps: list[ExecutionGap] = field(default_factory=list)
    overall_gap_ratio: float = 0.0
    critical_gaps: int = 0
    assessment: str = ""

    @property
    def has_critical(self) -> bool:
        return self.critical_gaps > 0

    @property
    def gap_by_category(self) -> dict[str, float]:
        return {g.category: g.gap_ratio for g in self.gaps}


EXECUTION_FILL_RATE_BENCHMARK = 0.92
EXECUTION_SLIPPAGE_BENCHMARK_BPS = 10.0
EXECUTION_LIQUIDITY_BENCHMARK = 0.70
EXECUTION_LATENCY_BENCHMARK_MS = 50.0
EXECUTION_COST_BENCHMARK_BPS = 15.0
EXECUTION_PARTIAL_FILL_BENCHMARK = 0.15
EXECUTION_QUALITY_BENCHMARK = 0.65

SEVERITY_LOW_THRESHOLD = 0.10
SEVERITY_MEDIUM_THRESHOLD = 0.25
SEVERITY_HIGH_THRESHOLD = 0.50


class ExecutionGapAnalyzer:

    def __init__(self, seed: int | None = None):
        self.seed = seed

    def analyze(
        self,
        execution_report: ExecutionReport,
        market_regime: str = "normal",
    ) -> ExecutionGapReport:
        regime_mult = self._regime_multiplier(market_regime)

        gaps: list[ExecutionGap] = []

        g = self._fill_rate_gap(execution_report, regime_mult)
        gaps.append(g)

        g = self._slippage_gap(execution_report, regime_mult)
        gaps.append(g)

        g = self._liquidity_gap(execution_report, regime_mult)
        gaps.append(g)

        g = self._latency_gap(execution_report, regime_mult)
        gaps.append(g)

        g = self._partial_fill_gap(execution_report, regime_mult)
        gaps.append(g)

        g = self._quality_gap(execution_report, regime_mult)
        gaps.append(g)

        gap_ratios = [g.gap_ratio for g in gaps]
        overall_gap = round(sum(gap_ratios) / len(gap_ratios), 4) if gap_ratios else 0.0

        critical_gaps = sum(1 for g in gaps if g.severity in ("high", "critical"))

        assessment = self._assess(overall_gap, gaps)

        return ExecutionGapReport(
            gaps=gaps,
            overall_gap_ratio=overall_gap,
            critical_gaps=critical_gaps,
            assessment=assessment,
        )

    def _fill_rate_gap(self, report: ExecutionReport, mult: float) -> ExecutionGap:
        sim_fill = report.fill_rate
        benchmark = max(0.0, EXECUTION_FILL_RATE_BENCHMARK * mult)

        if benchmark <= 0:
            return ExecutionGap(
                category="成交率",
                simulated_value=sim_fill,
                realistic_benchmark=0.0,
                gap_ratio=0.0,
                severity="low",
                description="无可比基准",
            )

        gap = abs(sim_fill - benchmark)
        gap_ratio = round(gap / benchmark, 4)
        severity = self._classify_severity(gap_ratio)

        desc = (
            f"模拟成交率 {sim_fill:.1%} vs 实际基准 {benchmark:.1%}，"
            f"偏差 {gap:.1%}"
        )

        return ExecutionGap(
            category="成交率",
            simulated_value=round(sim_fill, 4),
            realistic_benchmark=round(benchmark, 4),
            gap_ratio=gap_ratio,
            severity=severity,
            description=desc,
        )

    def _slippage_gap(self, report: ExecutionReport, mult: float) -> ExecutionGap:
        sim_slippage = report.quality.avg_slippage_bps
        benchmark = EXECUTION_SLIPPAGE_BENCHMARK_BPS / max(0.1, mult)

        if benchmark <= 0:
            return ExecutionGap(
                category="滑点",
                simulated_value=sim_slippage,
                realistic_benchmark=0.0,
                gap_ratio=0.0,
                severity="low",
                description="无可比基准",
            )

        gap = abs(sim_slippage - benchmark)
        gap_ratio = round(gap / benchmark, 4) if benchmark > 0 else 0.0

        if sim_slippage < benchmark:
            direction = "低于"
        else:
            direction = "高于"

        severity = self._classify_severity(gap_ratio)

        desc = (
            f"模拟滑点 {sim_slippage:.1f}bps {direction} 实际基准 {benchmark:.1f}bps，"
            f"偏差 {gap:.1f}bps"
        )

        return ExecutionGap(
            category="滑点",
            simulated_value=round(sim_slippage, 2),
            realistic_benchmark=round(benchmark, 2),
            gap_ratio=gap_ratio,
            severity=severity,
            description=desc,
        )

    def _liquidity_gap(self, report: ExecutionReport, mult: float) -> ExecutionGap:
        sim_liq = report.quality.liquidity_score
        benchmark = max(0.0, EXECUTION_LIQUIDITY_BENCHMARK * mult)

        if benchmark <= 0:
            return ExecutionGap(
                category="流动性",
                simulated_value=sim_liq,
                realistic_benchmark=0.0,
                gap_ratio=0.0,
                severity="low",
                description="无可比基准",
            )

        gap = abs(sim_liq - benchmark)
        gap_ratio = round(gap / benchmark, 4)
        severity = self._classify_severity(gap_ratio)

        desc = (
            f"模拟流动性评分 {sim_liq:.2f} vs 实际基准 {benchmark:.2f}，"
            f"偏差 {gap:.2f}"
        )

        return ExecutionGap(
            category="流动性",
            simulated_value=round(sim_liq, 4),
            realistic_benchmark=round(benchmark, 4),
            gap_ratio=gap_ratio,
            severity=severity,
            description=desc,
        )

    def _latency_gap(self, report: ExecutionReport, mult: float) -> ExecutionGap:
        sim_latency = report.quality.avg_latency_ms
        benchmark = EXECUTION_LATENCY_BENCHMARK_MS / max(0.1, mult)

        if sim_latency <= 0:
            return ExecutionGap(
                category="延迟",
                simulated_value=0.0,
                realistic_benchmark=benchmark,
                gap_ratio=0.0 if benchmark <= 0 else 1.0,
                severity="high" if benchmark > 0 else "low",
                description="模拟延迟为0，真实交易系统存在不可忽视的延迟" if benchmark > 0 else "无可比基准",
            )

        if benchmark <= 0:
            return ExecutionGap(
                category="延迟",
                simulated_value=sim_latency,
                realistic_benchmark=0.0,
                gap_ratio=0.0,
                severity="low",
                description="无可比基准",
            )

        gap = abs(sim_latency - benchmark)
        gap_ratio = round(gap / benchmark, 4)
        severity = self._classify_severity(gap_ratio)

        if sim_latency < benchmark:
            direction = "低于"
        else:
            direction = "高于"

        desc = (
            f"模拟延迟 {sim_latency:.0f}ms {direction} 实际基准 {benchmark:.0f}ms，"
            f"偏差 {gap:.0f}ms"
        )

        return ExecutionGap(
            category="延迟",
            simulated_value=round(sim_latency, 2),
            realistic_benchmark=round(benchmark, 2),
            gap_ratio=gap_ratio,
            severity=severity,
            description=desc,
        )

    def _partial_fill_gap(self, report: ExecutionReport, mult: float) -> ExecutionGap:
        sim_partial = report.quality.partial_fill_ratio
        benchmark = EXECUTION_PARTIAL_FILL_BENCHMARK / max(0.1, mult)

        if benchmark <= 0:
            return ExecutionGap(
                category="部分成交率",
                simulated_value=sim_partial,
                realistic_benchmark=0.0,
                gap_ratio=0.0,
                severity="low",
                description="无可比基准",
            )

        gap = abs(sim_partial - benchmark)
        gap_ratio = round(gap / benchmark, 4)
        severity = self._classify_severity(gap_ratio)

        desc = (
            f"模拟部分成交率 {sim_partial:.1%} vs 实际基准 {benchmark:.1%}，"
            f"偏差 {gap:.1%}"
        )

        return ExecutionGap(
            category="部分成交率",
            simulated_value=round(sim_partial, 4),
            realistic_benchmark=round(benchmark, 4),
            gap_ratio=gap_ratio,
            severity=severity,
            description=desc,
        )

    def _quality_gap(self, report: ExecutionReport, mult: float) -> ExecutionGap:
        sim_quality = report.quality.overall_quality_score
        benchmark = max(0.0, EXECUTION_QUALITY_BENCHMARK * mult)

        if benchmark <= 0:
            return ExecutionGap(
                category="综合执行质量",
                simulated_value=sim_quality,
                realistic_benchmark=0.0,
                gap_ratio=0.0,
                severity="low",
                description="无可比基准",
            )

        gap = abs(sim_quality - benchmark)
        gap_ratio = round(gap / benchmark, 4)
        severity = self._classify_severity(gap_ratio)

        desc = (
            f"模拟执行质量 {sim_quality:.2f} vs 实际基准 {benchmark:.2f}，"
            f"偏差 {gap:.2f}"
        )

        return ExecutionGap(
            category="综合执行质量",
            simulated_value=round(sim_quality, 4),
            realistic_benchmark=round(benchmark, 4),
            gap_ratio=gap_ratio,
            severity=severity,
            description=desc,
        )

    def _regime_multiplier(self, regime: str) -> float:
        if regime == "crisis":
            return 0.60
        if regime == "stress":
            return 0.75
        if regime == "bull":
            return 1.10
        if regime == "low_vol":
            return 1.05
        return 1.0

    def _classify_severity(self, gap_ratio: float) -> str:
        if gap_ratio >= SEVERITY_HIGH_THRESHOLD:
            return "critical"
        if gap_ratio >= SEVERITY_MEDIUM_THRESHOLD:
            return "high"
        if gap_ratio >= SEVERITY_LOW_THRESHOLD:
            return "medium"
        return "low"

    def _assess(self, overall: float, gaps: list[ExecutionGap]) -> str:
        parts: list[str] = []
        if overall <= 0.10:
            parts.append("执行偏差: 极小")
        elif overall <= 0.20:
            parts.append("执行偏差: 低")
        elif overall <= 0.35:
            parts.append("执行偏差: 中")
        elif overall <= 0.50:
            parts.append("执行偏差: 高")
        else:
            parts.append("执行偏差: 严重")

        worst = max(gaps, key=lambda g: g.gap_ratio)
        parts.append(f"最大偏差维度: {worst.category} ({worst.severity})")

        return " | ".join(parts)
