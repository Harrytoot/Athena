from datetime import datetime, timezone

import pytest

from app.strategy_robustness.robustness_report import (
    CostAdjustedMetrics,
    TurnoverImpact,
    StabilityMetrics,
    RobustnessReport,
    RobustnessReportGenerator,
)
from tests.strategy_robustness import _build_history, _risk_result


class TestCostAdjustedMetrics:

    def test_defaults(self):
        metrics = CostAdjustedMetrics(
            raw_sharpe=0.0,
            cost_adjusted_sharpe=0.0,
            total_transaction_costs=0.0,
            cost_ratio=0.0,
            total_slippage=0.0,
            slippage_ratio=0.0,
            total_market_impact=0.0,
            impact_ratio=0.0,
            total_friction=0.0,
            friction_ratio=0.0,
        )
        assert metrics.sharpe_erosion == 0.0

    def test_sharpe_erosion(self):
        metrics = CostAdjustedMetrics(
            raw_sharpe=1.5,
            cost_adjusted_sharpe=1.2,
            total_transaction_costs=500.0,
            cost_ratio=0.005,
            total_slippage=200.0,
            slippage_ratio=0.002,
            total_market_impact=100.0,
            impact_ratio=0.001,
            total_friction=800.0,
            friction_ratio=0.008,
        )
        assert metrics.sharpe_erosion == 0.3


class TestRobustnessReportGenerator:

    def test_empty_history(self):
        gen = RobustnessReportGenerator()
        history = _build_history([], [])
        risk = _risk_result([])
        report = gen.generate(history, risk)
        assert isinstance(report, RobustnessReport)
        assert report.cost_metrics.cost_adjusted_sharpe == 0.0
        assert report.stability.perturbation_stability == 0.0
        assert report.overall_stability_score >= 0.0

    def test_generate_with_performance_report(self):
        from app.strategy.pnl_analyzer import PnLAnalyzer

        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.5] * 30,
            [100.0 + i * 0.3 for i in range(30)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.5] * 30)
        analyzer = PnLAnalyzer()
        perf = analyzer.analyze(history)
        report = gen.generate(history, risk, perf_report=perf)

        assert isinstance(report, RobustnessReport)
        assert isinstance(report.cost_metrics, CostAdjustedMetrics)
        assert isinstance(report.turnover_impact, TurnoverImpact)
        assert isinstance(report.stability, StabilityMetrics)
        assert len(report.stress_results) > 0

    def test_cost_metrics_populated(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.0, 0.5, 1.0, 0.5, 0.0] * 6,
            [100.0 + i * 0.2 for i in range(30)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 0.5, 1.0, 0.5, 0.0] * 6)
        report = gen.generate(history, risk)

        cm = report.cost_metrics
        assert cm.total_transaction_costs >= 0
        assert cm.total_slippage >= 0
        assert cm.total_market_impact >= 0
        assert cm.total_friction >= 0
        assert cm.friction_ratio >= 0

    def test_overall_stability_score_range(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [1.0] * 20,
            [100.0 + i * 0.5 for i in range(20)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 20)
        report = gen.generate(history, risk)
        assert 0.0 <= report.overall_stability_score <= 1.0

    def test_overall_assessment_not_empty(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [1.0] * 20,
            [100.0 + i * 0.5 for i in range(20)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 20)
        report = gen.generate(history, risk)
        assert len(report.overall_assessment) > 0
        assert "|" in report.overall_assessment

    def test_turnover_impact_with_trades(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.0, 1.0, -1.0, 0.5, -0.5] * 4,
            [100.0 + i * 0.1 for i in range(20)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, -1.0, 0.5, -0.5] * 4)
        report = gen.generate(history, risk)
        ti = report.turnover_impact
        assert ti.avg_daily_turnover > 0
        assert ti.total_turnover > 0
        assert ti.turnover_count > 0
        assert len(ti.slippage_sensitivity) > 0
        assert len(ti.impact_sensitivity) > 0

    def test_turnover_impact_no_trades(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.5] * 10,
            [100.0 + i for i in range(10)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.5] * 10)
        report = gen.generate(history, risk)
        ti = report.turnover_impact
        assert ti.avg_daily_turnover == 0.0
        assert ti.total_turnover == 0.0
        assert ti.cost_per_turnover_pct == 0.0

    def test_stability_metrics(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.5] * 50,
            [100.0 + i * 0.2 for i in range(50)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.5] * 50)
        report = gen.generate(history, risk)
        sm = report.stability
        assert sm.stress_scenarios_total > 0
        assert 0 <= sm.stress_scenarios_passed <= sm.stress_scenarios_total
        assert 0.0 <= sm.stress_resilience_score <= 1.0

    def test_friction_includes_all_costs(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.0, 1.0, 0.0],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.0])
        report = gen.generate(history, risk)
        cm = report.cost_metrics
        expected_friction = cm.total_transaction_costs + cm.total_slippage + cm.total_market_impact
        assert cm.total_friction == pytest.approx(expected_friction, rel=1e-4)

    def test_cost_adjusted_sharpe_not_higher_than_raw(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [0.0, 1.0, 0.8, 0.5, 0.3, 0.0] * 5,
            [100.0 + i * 0.3 for i in range(30)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.8, 0.5, 0.3, 0.0] * 5)
        report = gen.generate(history, risk)
        cm = report.cost_metrics
        assert cm.cost_adjusted_sharpe <= cm.raw_sharpe or cm.raw_sharpe <= 0

    def test_stress_results_in_report(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [1.0] * 30,
            [100.0 + i * 0.5 for i in range(30)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 30)
        report = gen.generate(history, risk)
        assert len(report.stress_results) > 0
        for sr in report.stress_results:
            assert sr.description
            assert isinstance(sr.sharpe_ratio, float)

    def test_custom_configs_passed_through(self):
        from app.strategy_robustness.transaction_cost import TransactionCostConfig
        from app.strategy_robustness.slippage_model import SlippageConfig
        from app.strategy_robustness.market_impact import ImpactConfig

        cost_cfg = TransactionCostConfig(commission_rate=0.001, stamp_duty_rate=0.002)
        slip_cfg = SlippageConfig(base_spread_bps=5.0)
        imp_cfg = ImpactConfig(impact_coefficient=0.2)

        gen = RobustnessReportGenerator(
            cost_config=cost_cfg,
            slippage_config=slip_cfg,
            impact_config=imp_cfg,
        )
        history = _build_history(
            [0.0, 1.0, 0.5],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5])
        report = gen.generate(history, risk)
        assert report.cost_metrics.total_transaction_costs > 0

    def test_negative_performance_still_reports(self):
        gen = RobustnessReportGenerator()
        history = _build_history(
            [1.0] * 10,
            [100.0 - i * 1.0 for i in range(10)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 10)
        report = gen.generate(history, risk)
        assert isinstance(report, RobustnessReport)
        assert report.overall_stability_score >= 0.0
