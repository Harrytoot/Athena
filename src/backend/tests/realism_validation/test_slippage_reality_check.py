from datetime import datetime, timezone

from app.execution.execution_report import ExecutionReport, ExecutionQuality
from app.strategy_robustness.stress_tester import StressTestResult, StressScenario
from app.realism_validation.slippage_reality_check import (
    SlippageRealityChecker, SlippageRealityReport, SlippageRealityResult,
)


def _make_execution_report(avg_slippage=5.0, max_slippage=18.0):
    return ExecutionReport(
        generated_at=datetime.now(timezone.utc),
        total_orders=10,
        filled_orders=8,
        partially_filled=1,
        unfilled_orders=1,
        total_requested_notional=500_000.0,
        total_executed_notional=425_000.0,
        fill_rate=0.85,
        quality=ExecutionQuality(
            fill_rate=0.85,
            partial_fill_ratio=0.1,
            avg_slippage_bps=avg_slippage,
            max_slippage_bps=max_slippage,
            total_slippage_cost=250.0,
            avg_latency_ms=30.0,
            max_latency_ms=80.0,
            liquidity_score=0.7,
            overall_quality_score=0.65,
        ),
        warnings=[],
        summary="",
    )


def _make_stress_results(num=5, survived=True, returns=None):
    if returns is None:
        returns = [-0.05, -0.08, -0.03, -0.10, -0.06]
    results = []
    for i in range(num):
        results.append(StressTestResult(
            scenario=list(StressScenario)[i % len(list(StressScenario))],
            description="test",
            total_return=returns[i % len(returns)],
            annualized_return=-0.10,
            sharpe_ratio=-0.5,
            max_drawdown=-0.12,
            win_rate=0.35,
            calmar_ratio=-0.8,
            total_days=252,
            return_delta_vs_baseline=0.0,
            sharpe_delta_vs_baseline=0.0,
            max_drawdown_delta_vs_baseline=0.0,
            survived=survived,
        ))
    return results


class TestSlippageRealityChecker:

    def test_normal_slippage_is_realistic(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report(avg_slippage=5.0, max_slippage=18.0)
        stress = _make_stress_results()

        report = checker.check(exec_report, stress)

        assert isinstance(report, SlippageRealityReport)
        assert report.baseline.is_realistic

    def test_zero_slippage_is_unrealistic(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report(avg_slippage=0.0, max_slippage=0.0)
        stress = _make_stress_results()

        report = checker.check(exec_report, stress)

        assert not report.baseline.is_realistic

    def test_amplification_ratio_computed(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report(avg_slippage=5.0, max_slippage=18.0)
        stress = _make_stress_results()

        report = checker.check(exec_report, stress)

        assert report.amplification_ratio > 0
        assert report.stress.amplification_vs_baseline > 1.0

    def test_realistic_range_is_sane(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report(avg_slippage=5.0, max_slippage=18.0)
        stress = _make_stress_results()

        report = checker.check(exec_report, stress)

        low, high = report.realistic_range
        assert low < high
        assert low >= 0

    def test_no_stress_results_handled(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report()
        stress: list = []

        report = checker.check(exec_report, stress)

        assert isinstance(report, SlippageRealityReport)
        assert report.stress.avg_slippage_bps == 0.0

    def test_extreme_stress_returns_handle(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report(avg_slippage=10.0, max_slippage=30.0)
        stress = _make_stress_results(returns=[-0.30, -0.40, -0.50, -0.20, -0.35])

        report = checker.check(exec_report, stress)

        assert report.amplification_ratio > 1.0
        assert report.stress.avg_slippage_bps > report.baseline.avg_slippage_bps

    def test_deterministic_output(self):
        exec_report = _make_execution_report()
        stress = _make_stress_results()

        c1 = SlippageRealityChecker(seed=123)
        c2 = SlippageRealityChecker(seed=123)

        r1 = c1.check(exec_report, stress)
        r2 = c2.check(exec_report, stress)

        assert r1.amplification_ratio == r2.amplification_ratio
        assert r1.stress.avg_slippage_bps == r2.stress.avg_slippage_bps

    def test_assessment_generated(self):
        checker = SlippageRealityChecker(seed=42)
        exec_report = _make_execution_report()
        stress = _make_stress_results()

        report = checker.check(exec_report, stress)

        assert report.assessment
        assert len(report.assessment) > 0
