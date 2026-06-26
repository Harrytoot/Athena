from datetime import datetime, timezone

from app.execution.execution_report import ExecutionReport, ExecutionQuality
from app.portfolio.portfolio_engine import (
    PortfolioReport, PortfolioComposition, PortfolioMetrics,
)
from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.stress_tester import StressTestResult, StressScenario
from app.realism_validation.assumption_audit import AssumptionAuditReport, AssumptionResult
from app.realism_validation.execution_gap_analyzer import ExecutionGapReport, ExecutionGap
from app.realism_validation.slippage_reality_check import SlippageRealityReport, SlippageRealityResult
from app.realism_validation.liquidity_crisis_simulator import LiquidityCrisisReport, LiquidityCrisisStage
from app.realism_validation.real_vs_sim_report import RealVsSimReportGenerator, RealVsSimReport, RealismDimensionScore


def _make_assumption_audit(overall=0.75, unrealistic=2, critical=None):
    assumptions = [
        AssumptionResult(
            name="订单成交率", description="检查成交率", is_realistic=True, score=0.85,
            details="ok",
        ),
        AssumptionResult(
            name="夏普比率合理性", description="检查夏普", is_realistic=True, score=0.9,
            details="ok",
        ),
    ]
    return AssumptionAuditReport(
        assumptions=assumptions,
        unrealistic_count=unrealistic,
        overall_realism=overall,
        critical_issues=critical or [],
        assessment="正常",
    )


def _make_execution_gap(overall_gap=0.15, critical_gaps=1):
    gaps = [
        ExecutionGap(
            category="成交率", simulated_value=0.85, realistic_benchmark=0.92,
            gap_ratio=0.08, severity="low", description="ok",
        ),
        ExecutionGap(
            category="滑点", simulated_value=8.0, realistic_benchmark=10.0,
            gap_ratio=0.20, severity="medium", description="ok",
        ),
    ]
    return ExecutionGapReport(
        gaps=gaps,
        overall_gap_ratio=overall_gap,
        critical_gaps=critical_gaps,
        assessment="正常",
    )


def _make_slippage_reality(baseline_realistic=True, stress_realistic=True, amplification=3.0):
    return SlippageRealityReport(
        baseline=SlippageRealityResult(
            category="normal", avg_slippage_bps=5.0, max_slippage_bps=15.0,
            amplification_vs_baseline=1.0, is_realistic=baseline_realistic,
            details="正常",
        ),
        stress=SlippageRealityResult(
            category="stress", avg_slippage_bps=15.0, max_slippage_bps=45.0,
            amplification_vs_baseline=amplification, is_realistic=stress_realistic,
            details="压力",
        ),
        amplification_ratio=amplification,
        realistic_range=(5.0, 80.0),
        assessment="正常",
    )


def _make_liquidity_crisis(survival=0.55, breakdown=0.10):
    stages = [
        LiquidityCrisisStage(
            stage=1, label="正常", liquidity_remaining_pct=0.85,
            fill_rate=0.80, slippage_bps=8.0, spread_bps=3.0,
            is_viable=True, description="正常",
        ),
        LiquidityCrisisStage(
            stage=8, label="完全枯竭", liquidity_remaining_pct=0.0,
            fill_rate=0.0, slippage_bps=200.0, spread_bps=50.0,
            is_viable=False, description="不可交易",
        ),
    ]
    return LiquidityCrisisReport(
        stages=stages,
        breakdown_threshold_pct=breakdown,
        survival_probability=survival,
        max_viable_position_pct=0.08,
        recovery_time_estimate_days=15,
        assessment="正常",
    )


class TestRealVsSimReportGenerator:

    def test_generate_returns_report(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit()
        gap = _make_execution_gap()
        reality = _make_slippage_reality()
        crisis = _make_liquidity_crisis()

        report = generator.generate(audit, gap, reality, crisis)

        assert isinstance(report, RealVsSimReport)
        assert len(report.dimensions) == 5
        assert report.realism_consistency_score > 0

    def test_high_quality_inputs_produce_high_score(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit(overall=0.95, unrealistic=0)
        gap = _make_execution_gap(overall_gap=0.05, critical_gaps=0)
        reality = _make_slippage_reality(baseline_realistic=True, stress_realistic=True)
        crisis = _make_liquidity_crisis(survival=0.85, breakdown=0.05)

        report = generator.generate(audit, gap, reality, crisis)

        assert report.realism_consistency_score >= 0.7
        assert report.realism_grade in ("A", "B")

    def test_low_quality_inputs_produce_low_score(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit(overall=0.3, unrealistic=8, critical=["issues"])
        gap = _make_execution_gap(overall_gap=0.70, critical_gaps=4)
        reality = _make_slippage_reality(baseline_realistic=False, stress_realistic=False)
        crisis = _make_liquidity_crisis(survival=0.15, breakdown=0.50)

        report = generator.generate(audit, gap, reality, crisis)

        assert report.realism_consistency_score < 0.5
        assert len(report.critical_findings) > 0

    def test_dimensions_have_correct_weights(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit()
        gap = _make_execution_gap()
        reality = _make_slippage_reality()
        crisis = _make_liquidity_crisis()

        report = generator.generate(audit, gap, reality, crisis)

        total_weight = sum(d.weight for d in report.dimensions)
        assert abs(total_weight - 1.0) < 0.01

        dim_names = [d.dimension for d in report.dimensions]
        assert "系统假设真实性" in dim_names
        assert "执行偏差分析" in dim_names
        assert "滑点真实性" in dim_names
        assert "流动性危机" in dim_names
        assert "压力生存能力" in dim_names

    def test_execution_gap_ratio_field_set(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit()
        gap = _make_execution_gap(overall_gap=0.25)
        reality = _make_slippage_reality()
        crisis = _make_liquidity_crisis()

        report = generator.generate(audit, gap, reality, crisis)

        assert report.execution_gap_ratio == 0.25

    def test_slippage_stress_normal_ratio_field_set(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit()
        gap = _make_execution_gap()
        reality = _make_slippage_reality(amplification=3.5)
        crisis = _make_liquidity_crisis()

        report = generator.generate(audit, gap, reality, crisis)

        assert report.slippage_stress_normal_ratio == 3.5

    def test_realism_grade_computed(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit(overall=0.85)
        gap = _make_execution_gap(overall_gap=0.10)
        reality = _make_slippage_reality()
        crisis = _make_liquidity_crisis(survival=0.80)

        report = generator.generate(audit, gap, reality, crisis)

        assert report.realism_grade in ("A", "B", "C", "D", "F")
        assert isinstance(report.is_acceptable, bool)

    def test_generated_at_is_set(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit()
        gap = _make_execution_gap()
        reality = _make_slippage_reality()
        crisis = _make_liquidity_crisis()

        report = generator.generate(audit, gap, reality, crisis)

        assert isinstance(report.generated_at, datetime)

    def test_overall_assessment_not_empty(self):
        generator = RealVsSimReportGenerator(seed=42)
        audit = _make_assumption_audit()
        gap = _make_execution_gap()
        reality = _make_slippage_reality()
        crisis = _make_liquidity_crisis()

        report = generator.generate(audit, gap, reality, crisis)

        assert report.overall_assessment
        assert len(report.overall_assessment) > 0
