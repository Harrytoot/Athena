from datetime import datetime, timezone

from app.execution.execution_report import ExecutionReport, ExecutionQuality
from app.realism_validation.liquidity_crisis_simulator import (
    LiquidityCrisisSimulator, LiquidityCrisisReport, LiquidityCrisisStage,
)


def _make_execution_report(fill_rate=0.85, avg_slippage=5.0):
    return ExecutionReport(
        generated_at=datetime.now(timezone.utc),
        total_orders=10,
        filled_orders=7,
        partially_filled=2,
        unfilled_orders=1,
        total_requested_notional=500_000.0,
        total_executed_notional=425_000.0,
        fill_rate=fill_rate,
        quality=ExecutionQuality(
            fill_rate=fill_rate,
            partial_fill_ratio=0.1,
            avg_slippage_bps=avg_slippage,
            max_slippage_bps=18.0,
            total_slippage_cost=250.0,
            avg_latency_ms=30.0,
            max_latency_ms=80.0,
            liquidity_score=0.7,
            overall_quality_score=0.65,
        ),
        warnings=[],
        summary="",
    )


class TestLiquidityCrisisSimulator:

    def test_simulate_produces_stages(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        assert isinstance(report, LiquidityCrisisReport)
        assert len(report.stages) == 8
        assert report.stages[0].is_viable
        assert not report.stages[-1].is_viable

    def test_stages_show_progressive_deterioration(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        fill_rates = [s.fill_rate for s in report.stages]
        slippages = [s.slippage_bps for s in report.stages]

        assert fill_rates[0] > fill_rates[-1]
        assert slippages[0] < slippages[-1]

    def test_breakdown_threshold_identified(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        assert report.breakdown_threshold_pct > 0
        assert report.breakdown_threshold_pct < 0.50

    def test_survival_probability_in_range(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        assert 0.0 <= report.survival_probability <= 1.0

    def test_max_viable_position_in_range(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        assert 0.005 <= report.max_viable_position_pct <= 0.50

    def test_recovery_time_estimate(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        assert report.recovery_time_estimate_days >= 5
        assert report.recovery_time_estimate_days <= 60

    def test_low_baseline_fill_reduces_survival(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        good = _make_execution_report(fill_rate=0.90, avg_slippage=3.0)
        bad = _make_execution_report(fill_rate=0.50, avg_slippage=20.0)

        good_report = simulator.simulate(good)
        bad_report = simulator.simulate(bad)

        assert bad_report.survival_probability < good_report.survival_probability

    def test_deterministic_with_seed(self):
        exec_report = _make_execution_report()

        sim1 = LiquidityCrisisSimulator(seed=123)
        sim2 = LiquidityCrisisSimulator(seed=123)

        r1 = sim1.simulate(exec_report)
        r2 = sim2.simulate(exec_report)

        assert r1.survival_probability == r2.survival_probability
        assert r1.stages[-1].slippage_bps == r2.stages[-1].slippage_bps

    def test_assessment_generated(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        assert report.assessment
        assert len(report.assessment) > 0

    def test_crisis_stage_labels(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        labels = [s.label for s in report.stages]
        assert labels[0] == "正常"
        assert labels[-1] == "完全枯竭"

    def test_worst_stage_slippage(self):
        simulator = LiquidityCrisisSimulator(seed=42)
        exec_report = _make_execution_report()

        report = simulator.simulate(exec_report)

        max_slip = report.worst_stage_slippage
        assert max_slip > 0
        assert max_slip == max(s.slippage_bps for s in report.stages)
