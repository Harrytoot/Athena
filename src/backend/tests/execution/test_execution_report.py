import pytest

from app.execution.slippage_engine import SlippageEstimate
from app.execution.liquidity_model import LiquidityProfile
from app.execution.execution_report import (
    ExecutionReport,
    ExecutionQuality,
    ExecutionReportGenerator,
)


class TestExecutionReportGenerator:

    def test_generate_basic(self):
        gen = ExecutionReportGenerator()
        report = gen.generate(
            total_orders=10,
            filled_count=8,
            partial_count=2,
            requested_notional=1_000_000,
            executed_notional=850_000,
            slippage_estimates=[],
        )

        assert isinstance(report, ExecutionReport)
        assert report.total_orders == 10
        assert report.filled_orders == 8
        assert report.partially_filled == 2
        assert report.unfilled_orders == 0
        assert report.fill_rate == pytest.approx(0.8, rel=1e-4)

    def test_generate_with_slippage(self):
        gen = ExecutionReportGenerator()
        slippage = [
            SlippageEstimate("s1", 100_000, 0.01, 0.001, 5.0, 5.0, "buy"),
            SlippageEstimate("s2", 200_000, 0.02, 0.002, 15.0, 30.0, "sell"),
        ]
        report = gen.generate(
            total_orders=5,
            filled_count=5,
            partial_count=0,
            requested_notional=1_000_000,
            executed_notional=980_000,
            slippage_estimates=slippage,
        )

        assert report.quality.total_slippage_cost == pytest.approx(35.0, rel=1e-4)
        assert report.quality.avg_slippage_bps == pytest.approx(10.0, rel=1e-4)
        assert report.quality.max_slippage_bps == pytest.approx(15.0, rel=1e-4)

    def test_generate_with_liquidity(self):
        gen = ExecutionReportGenerator()
        profiles = [
            LiquidityProfile("s1", 1e8, 1e7, 2.0, 0.9, True),
            LiquidityProfile("s2", 1e8, 5e6, 3.0, 0.8, True),
            LiquidityProfile("s3", 1e8, 1e6, 5.0, 0.3, False),
        ]
        report = gen.generate(
            total_orders=3,
            filled_count=3,
            partial_count=0,
            requested_notional=1_000_000,
            executed_notional=1_000_000,
            slippage_estimates=[],
            liquidity_profiles=profiles,
        )

        assert report.quality.liquidity_score == pytest.approx(2/3, rel=1e-4)

    def test_execution_efficiency(self):
        report = ExecutionReport(
            total_orders=10,
            filled_orders=8,
            partially_filled=2,
            unfilled_orders=0,
            total_requested_notional=1_000_000,
            total_executed_notional=850_000,
            fill_rate=0.85,
        )
        assert report.execution_efficiency == pytest.approx(0.85, rel=1e-4)

    def test_zero_requested_is_zero_efficiency(self):
        report = ExecutionReport(
            total_orders=0,
            total_requested_notional=0.0,
            total_executed_notional=0.0,
        )
        assert report.execution_efficiency == 0.0

    def test_quality_grade_a(self):
        quality = ExecutionQuality(overall_quality_score=0.85)
        assert quality.quality_grade == "A"
        assert quality.is_acceptable

    def test_quality_grade_b(self):
        quality = ExecutionQuality(overall_quality_score=0.65)
        assert quality.quality_grade == "B"
        assert quality.is_acceptable

    def test_quality_grade_c(self):
        quality = ExecutionQuality(overall_quality_score=0.45)
        assert quality.quality_grade == "C"
        assert quality.is_acceptable

    def test_quality_grade_d(self):
        quality = ExecutionQuality(overall_quality_score=0.25)
        assert quality.quality_grade == "D"
        assert not quality.is_acceptable

    def test_quality_grade_f(self):
        quality = ExecutionQuality(overall_quality_score=0.10)
        assert quality.quality_grade == "F"
        assert not quality.is_acceptable

    def test_warnings_generated_for_low_fill_rate(self):
        gen = ExecutionReportGenerator()
        report = gen.generate(
            total_orders=10,
            filled_count=4,
            partial_count=2,
            requested_notional=1_000_000,
            executed_notional=500_000,
            slippage_estimates=[],
        )

        assert report.has_warnings
        assert any("fill" in w.lower() for w in report.warnings)

    def test_warnings_for_high_slippage(self):
        gen = ExecutionReportGenerator()
        slippage = [
            SlippageEstimate("s1", 100_000, 0.10, 0.01, 80.0, 80.0, "buy"),
        ]
        report = gen.generate(
            total_orders=5,
            filled_count=5,
            partial_count=0,
            requested_notional=500_000,
            executed_notional=500_000,
            slippage_estimates=slippage,
        )

        assert report.has_warnings
        assert any("slippage" in w.lower() for w in report.warnings)

    def test_summary_generated(self):
        gen = ExecutionReportGenerator()
        report = gen.generate(
            total_orders=10,
            filled_count=10,
            partial_count=0,
            requested_notional=1_000_000,
            executed_notional=1_000_000,
            slippage_estimates=[],
        )

        assert isinstance(report.summary, str)
        assert len(report.summary) > 0

    def test_has_warnings_false(self):
        report = ExecutionReport(warnings=[])
        assert not report.has_warnings

    def test_has_warnings_true(self):
        report = ExecutionReport(warnings=["Low fill rate"])
        assert report.has_warnings

    def test_overall_quality_score_best_case(self):
        gen = ExecutionReportGenerator()
        profiles = [
            LiquidityProfile("s1", 1e8, 1e7, 1.0, 0.95, True),
        ]
        report = gen.generate(
            total_orders=10,
            filled_count=10,
            partial_count=0,
            requested_notional=1_000_000,
            executed_notional=1_000_000,
            slippage_estimates=[],
            liquidity_profiles=profiles,
        )

        assert report.quality.overall_quality_score > 0.7
