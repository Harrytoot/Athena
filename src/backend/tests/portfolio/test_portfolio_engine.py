import math

import pytest

from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.robustness_report import RobustnessReport, CostAdjustedMetrics, StabilityMetrics
from app.strategy_validation.performance_report import StrategyValidationReport
from app.portfolio.portfolio_engine import (
    PortfolioEngine,
    PortfolioReport,
    PortfolioComposition,
    PortfolioMetrics,
    StrategyInput,
)
from app.portfolio.risk_budgeting import RiskConstraint


def _make_perf(sharpe=1.0, daily_vol=0.01, calmar=1.0, max_dd=-0.10, annual_ret=0.15, total_ret=0.30):
    return StrategyPerformanceReport(
        total_return=total_ret,
        annualized_return=annual_ret,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        max_drawdown_duration=5,
        win_rate=0.55,
        avg_daily_return=0.001,
        daily_volatility=daily_vol,
        calmar_ratio=calmar,
        total_days=252,
        avg_leverage=0.5,
        positive_days=130,
        negative_days=122,
    )


def _make_robust(cost_sharpe=0.9, stability=0.7):
    return RobustnessReport(
        cost_metrics=CostAdjustedMetrics(
            raw_sharpe=1.0,
            cost_adjusted_sharpe=cost_sharpe,
            total_transaction_costs=100.0,
            cost_ratio=0.01,
            total_slippage=50.0,
            slippage_ratio=0.005,
            total_market_impact=30.0,
            impact_ratio=0.003,
            total_friction=180.0,
            friction_ratio=0.01,
        ),
        stability=StabilityMetrics(
            perturbation_stability=stability,
            perturbation_mean_sharpe=cost_sharpe,
            perturbation_sharpe_std=0.1,
            stress_scenarios_passed=5,
            stress_scenarios_total=6,
            stress_resilience_score=0.83,
        ),
        overall_stability_score=stability,
        overall_assessment="good",
    )


def _make_strategy(sid, sharpe=1.0, daily_vol=0.01, calmar=1.0, max_dd=-0.10, stability=0.7):
    return StrategyInput(
        strategy_id=sid,
        performance=_make_perf(sharpe=sharpe, daily_vol=daily_vol, calmar=calmar, max_dd=max_dd),
        robustness=_make_robust(cost_sharpe=sharpe * 0.9, stability=stability),
    )


class TestPortfolioEngine:

    def test_empty_strategies(self):
        engine = PortfolioEngine()
        report = engine.construct([])
        assert isinstance(report, PortfolioReport)
        assert not report.is_ready

    def test_single_strategy(self):
        engine = PortfolioEngine()
        strategies = [_make_strategy("s1", sharpe=1.5)]
        report = engine.construct(strategies)

        assert report.is_ready
        assert len(report.composition.allocations) == 1
        assert report.composition.weight_result.total_weight == pytest.approx(1.0, rel=1e-4)
        assert report.metrics.expected_return != 0.0

    def test_multiple_strategies(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("momentum", sharpe=1.5),
            _make_strategy("mean_rev", sharpe=1.0),
            _make_strategy("arbitrage", sharpe=0.8),
        ]
        report = engine.construct(strategies)

        assert report.is_ready
        assert report.composition.active_strategies == 3
        assert report.metrics.diversification_ratio > 0

    def test_portfolio_metrics_populated(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.5),
            _make_strategy("s2", sharpe=1.0),
        ]
        report = engine.construct(strategies)

        m = report.metrics
        assert m.expected_sharpe > 0
        assert m.expected_volatility > 0
        assert m.diversification_ratio >= 1.0
        assert isinstance(m.stability_score, float)

    def test_risk_flags_detected(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("negative", sharpe=-0.5),
        ]
        report = engine.construct(strategies)

        assert len(report.risk_flags) > 0

    def test_assessment_string(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.5),
            _make_strategy("s2", sharpe=1.2),
            _make_strategy("s3", sharpe=1.0),
            _make_strategy("s4", sharpe=0.8),
            _make_strategy("s5", sharpe=0.7),
        ]
        report = engine.construct(strategies)

        assert isinstance(report.assessment, str)
        assert len(report.assessment) > 0

    def test_rebalance_integration(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.5),
            _make_strategy("s2", sharpe=1.0),
        ]
        current_allocations = []

        report = engine.rebalance(current_allocations, strategies)
        assert report.rebalance is not None

    def test_custom_risk_constraint(self):
        c = RiskConstraint(max_portfolio_vol=0.10, max_single_risk_ratio=0.30)
        engine = PortfolioEngine(risk_constraint=c)
        strategies = [
            _make_strategy("s1", sharpe=1.5),
            _make_strategy("s2", sharpe=1.0),
        ]
        report = engine.construct(strategies)

        assert report.composition.risk_budget_result.portfolio_vol > 0

    def test_custom_max_weight(self):
        engine = PortfolioEngine(max_strategy_weight=0.40)
        strategies = [
            _make_strategy("star", sharpe=3.0),
            _make_strategy("avg", sharpe=1.0),
            _make_strategy("weak", sharpe=0.5),
        ]
        report = engine.construct(strategies)

        star_weight = next(
            a.weight for a in report.composition.allocations if a.strategy_id == "star"
        )
        assert star_weight <= 0.40 + 1e-4

    def test_cash_reserve_respected(self):
        engine = PortfolioEngine(total_capital=1_000_000, cash_reserve_pct=0.10)
        strategies = [
            _make_strategy("s1", sharpe=1.5),
        ]
        report = engine.construct(strategies)

        assert report.composition.allocations[0].capital <= 900_000

    def test_regime_multipliers_integration(self):
        engine = PortfolioEngine(max_strategy_weight=1.0)
        strategies = [
            _make_strategy("bull_favored", sharpe=1.0),
            _make_strategy("bear_favored", sharpe=1.0),
        ]
        regime = {"bull_favored": 1.5, "bear_favored": 0.5}
        report = engine.construct(strategies, regime_multipliers=regime)

        bull_w = next(
            a.weight for a in report.composition.allocations if a.strategy_id == "bull_favored"
        )
        bear_w = next(
            a.weight for a in report.composition.allocations if a.strategy_id == "bear_favored"
        )
        assert bull_w > bear_w

    def test_correlation_impact(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.5, daily_vol=0.01),
            _make_strategy("s2", sharpe=1.0, daily_vol=0.01),
        ]

        high_corr = {"s1": {"s1": 1.0, "s2": 0.9}, "s2": {"s1": 0.9, "s2": 1.0}}
        low_corr = {"s1": {"s1": 1.0, "s2": -0.2}, "s2": {"s1": -0.2, "s2": 1.0}}

        report_high = engine.construct(strategies, correlation_matrix=high_corr)
        report_low = engine.construct(strategies, correlation_matrix=low_corr)

        assert report_low.metrics.diversification_ratio > report_high.metrics.diversification_ratio

    def test_negative_sharpe_strategies_filtered(self):
        engine = PortfolioEngine(max_strategy_weight=1.0)
        strategies = [
            _make_strategy("good", sharpe=1.5),
            _make_strategy("bad", sharpe=-0.8),
        ]
        report = engine.construct(strategies)

        bad_alloc = next(
            a for a in report.composition.allocations if a.strategy_id == "bad"
        )
        good_alloc = next(
            a for a in report.composition.allocations if a.strategy_id == "good"
        )
        assert bad_alloc.weight < good_alloc.weight

    def test_high_volatility_strategies_penalized(self):
        engine = PortfolioEngine(max_strategy_weight=1.0)
        strategies = [
            _make_strategy("stable", sharpe=1.0, daily_vol=0.005),
            _make_strategy("volatile", sharpe=1.0, daily_vol=0.04),
        ]
        report = engine.construct(strategies)

        stable_w = next(
            a.weight for a in report.composition.allocations if a.strategy_id == "stable"
        )
        volatile_w = next(
            a.weight for a in report.composition.allocations if a.strategy_id == "volatile"
        )
        assert stable_w > volatile_w

    def test_risk_flags_high_vol_warning(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.0, daily_vol=0.04),
        ]
        report = engine.construct(strategies)

        assert any("volatility" in f.lower() for f in report.risk_flags)

    def test_low_diversification_flag(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.5),
        ]
        report = engine.construct(strategies)

        assert any("diversification" in f.lower() for f in report.risk_flags)

    def test_capped_strategy_flag(self):
        engine = PortfolioEngine(max_strategy_weight=0.40)
        strategies = [
            _make_strategy("star", sharpe=4.0),
            _make_strategy("avg", sharpe=1.0),
        ]
        report = engine.construct(strategies)

        assert any("capped" in f for f in report.risk_flags)

    def test_composition_properties(self):
        engine = PortfolioEngine()
        strategies = [
            _make_strategy("s1", sharpe=1.5),
            _make_strategy("s2", sharpe=1.0),
            _make_strategy("s3", sharpe=0.8),
        ]
        report = engine.construct(strategies)

        comp = report.composition
        assert comp.total_weight == pytest.approx(1.0, rel=1e-4)
        assert comp.active_strategies == 3
