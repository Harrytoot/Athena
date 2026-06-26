from datetime import datetime, timezone

from app.execution.execution_report import ExecutionReport, ExecutionQuality
from app.realism_validation.execution_gap_analyzer import (
    ExecutionGapAnalyzer, ExecutionGapReport, ExecutionGap,
)


def _make_execution_report(
    fill_rate=0.85, avg_slippage=8.0, max_slippage=20.0,
    liquidity_score=0.65, avg_latency=40.0, max_latency=100.0,
    partial_ratio=0.12, quality_score=0.60,
    total_notional=500_000.0,
):
    return ExecutionReport(
        generated_at=datetime.now(timezone.utc),
        total_orders=10,
        filled_orders=7,
        partially_filled=2,
        unfilled_orders=1,
        total_requested_notional=total_notional,
        total_executed_notional=total_notional * fill_rate,
        fill_rate=fill_rate,
        quality=ExecutionQuality(
            fill_rate=fill_rate,
            partial_fill_ratio=partial_ratio,
            avg_slippage_bps=avg_slippage,
            max_slippage_bps=max_slippage,
            total_slippage_cost=500.0,
            avg_latency_ms=avg_latency,
            max_latency_ms=max_latency,
            liquidity_score=liquidity_score,
            overall_quality_score=quality_score,
        ),
        warnings=[],
        summary="",
    )


class TestExecutionGapAnalyzer:

    def test_normal_regime_produces_report(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report()
        report = analyzer.analyze(exec_report, market_regime="normal")

        assert isinstance(report, ExecutionGapReport)
        assert len(report.gaps) == 6
        assert report.overall_gap_ratio >= 0.0
        assert report.assessment

    def test_zero_latency_detected_as_high_gap(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report(avg_latency=0.0, max_latency=0.0)
        report = analyzer.analyze(exec_report, market_regime="normal")

        latency_gaps = [g for g in report.gaps if g.category == "延迟"]
        assert len(latency_gaps) == 1
        assert latency_gaps[0].severity in ("high", "critical")

    def test_crisis_regime_increases_gaps(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report()
        normal = analyzer.analyze(exec_report, market_regime="normal")
        crisis = analyzer.analyze(exec_report, market_regime="crisis")

        assert crisis.overall_gap_ratio > normal.overall_gap_ratio

    def test_low_gap_for_realistic_report(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report(
            fill_rate=0.92, avg_slippage=10.0, max_slippage=30.0,
            liquidity_score=0.70, avg_latency=50.0, partial_ratio=0.15,
            quality_score=0.65,
        )
        report = analyzer.analyze(exec_report, market_regime="normal")

        assert report.overall_gap_ratio < 0.40
        assert report.critical_gaps <= 2

    def test_high_fill_rate_produces_gap(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report(fill_rate=1.0)
        report = analyzer.analyze(exec_report, market_regime="normal")

        fill_gaps = [g for g in report.gaps if g.category == "成交率"]
        assert len(fill_gaps) == 1
        assert fill_gaps[0].gap_ratio > 0

    def test_gap_by_category_returns_dict(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report()
        report = analyzer.analyze(exec_report, market_regime="normal")

        gbc = report.gap_by_category
        assert isinstance(gbc, dict)
        assert "成交率" in gbc
        assert "滑点" in gbc

    def test_bull_regime_eases_benchmarks(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report(fill_rate=0.88, avg_slippage=8.0)
        normal = analyzer.analyze(exec_report, market_regime="normal")
        bull = analyzer.analyze(exec_report, market_regime="bull")

        assert normal.overall_gap_ratio != bull.overall_gap_ratio

    def test_has_critical_property(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report(avg_latency=0.0)
        report = analyzer.analyze(exec_report, market_regime="normal")

        assert isinstance(report.has_critical, bool)

    def test_low_vol_regime(self):
        analyzer = ExecutionGapAnalyzer(seed=42)
        exec_report = _make_execution_report()
        report = analyzer.analyze(exec_report, market_regime="low_vol")

        assert isinstance(report, ExecutionGapReport)
        assert report.overall_gap_ratio >= 0.0
