import pytest

from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.robustness_report import RobustnessReport, CostAdjustedMetrics, StabilityMetrics
from app.portfolio.weight_optimizer import WeightOptimizer, StrategyWeight, WeightResult
from app.portfolio.risk_budgeting import RiskBudgeting, RiskConstraint, RiskBudget, RiskBudgetResult


def _make_perf(sharpe=1.0, daily_vol=0.01, calmar=1.0, max_dd=-0.10, annual_ret=0.15):
    return StrategyPerformanceReport(
        total_return=0.30,
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


def _make_weight_result(strategy_ids, weights):
    sws = [
        StrategyWeight(
            strategy_id=sid,
            raw_sharpe=1.0,
            cost_adjusted_sharpe=0.9,
            volatility=0.01,
            stability_score=0.7,
            raw_weight=w,
            constrained_weight=w,
        )
        for sid, w in zip(strategy_ids, weights)
    ]
    return WeightResult(weights=sws)


class TestRiskConstraint:

    def test_defaults(self):
        c = RiskConstraint()
        assert c.max_portfolio_vol == 0.25
        assert c.max_single_risk_ratio == 0.40
        assert c.target_portfolio_vol == 0.15
        assert not c.use_risk_parity


class TestRiskBudgeting:

    def test_empty_weights(self):
        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(WeightResult(), {})
        assert len(result.budgets) == 0
        assert result.portfolio_vol == 0.0

    def test_single_strategy_budget(self):
        wr = _make_weight_result(["s1"], [1.0])
        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(wr, {"s1": 0.01})

        assert len(result.budgets) == 1
        assert result.budgets[0].risk_ratio == pytest.approx(1.0, rel=1e-4)
        assert result.portfolio_vol > 0

    def test_three_strategies_risk_distribution(self):
        wr = _make_weight_result(
            ["s1", "s2", "s3"],
            [0.4, 0.35, 0.25],
        )
        vols = {"s1": 0.01, "s2": 0.015, "s3": 0.02}
        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(wr, vols)

        assert len(result.budgets) == 3
        total_risk_ratio = sum(b.risk_ratio for b in result.budgets)
        assert total_risk_ratio == pytest.approx(1.0, rel=1e-4)
        assert result.portfolio_vol > 0

    def test_high_vol_strategy_contributes_more_risk(self):
        wr = _make_weight_result(
            ["low_vol", "high_vol"],
            [0.5, 0.5],
        )
        vols = {"low_vol": 0.005, "high_vol": 0.03}
        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(wr, vols)

        low = next(b for b in result.budgets if b.strategy_id == "low_vol")
        high = next(b for b in result.budgets if b.strategy_id == "high_vol")
        assert high.risk_contribution > low.risk_contribution

    def test_risk_budget_result_properties(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.5, 0.3, 0.2])
        vols = {"s1": 0.01, "s2": 0.01, "s3": 0.01}
        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(wr, vols)

        assert 0 < result.risk_concentration <= 1.0
        assert result.effective_n_risk >= 1.0
        assert isinstance(result.portfolio_vol, float)

    def test_correlation_matrix_affects_vol(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        vols = {"s1": 0.01, "s2": 0.01}

        high_corr = {"s1": {"s1": 1.0, "s2": 0.9}, "s2": {"s1": 0.9, "s2": 1.0}}
        low_corr = {"s1": {"s1": 1.0, "s2": -0.2}, "s2": {"s1": -0.2, "s2": 1.0}}

        rb = RiskBudgeting()
        result_high = rb.compute_risk_budgets(wr, vols, correlation_matrix=high_corr)
        result_low = rb.compute_risk_budgets(wr, vols, correlation_matrix=low_corr)

        assert result_high.portfolio_vol > result_low.portfolio_vol

    def test_portfolio_vol_capped(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        vols = {"s1": 0.04, "s2": 0.04}

        c = RiskConstraint(max_portfolio_vol=0.10)
        rb = RiskBudgeting(constraint=c)
        result = rb.compute_risk_budgets(wr, vols)

        assert result.portfolio_vol <= 0.10
        assert result.constrained

    def test_risk_ratio_flagging(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.8, 0.1, 0.1])
        vols = {"s1": 0.03, "s2": 0.005, "s3": 0.005}

        c = RiskConstraint(max_single_risk_ratio=0.40)
        rb = RiskBudgeting(constraint=c)
        result = rb.compute_risk_budgets(wr, vols)

        s1_budget = next(b for b in result.budgets if b.strategy_id == "s1")
        assert s1_budget.risk_ratio > 0.40

    def test_risk_parity_weights(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.5, 0.3, 0.2])
        vols = {"s1": 0.01, "s2": 0.02, "s3": 0.03}

        rb = RiskBudgeting()
        rp_weights = rb.compute_risk_parity_weights(wr, vols)

        assert len(rp_weights) == 3
        assert sum(rp_weights) == pytest.approx(1.0, rel=1e-4)
        assert all(0 <= w <= 1.0 for w in rp_weights)

    def test_risk_parity_single_strategy(self):
        wr = _make_weight_result(["s1"], [1.0])
        vols = {"s1": 0.01}

        rb = RiskBudgeting()
        rp_weights = rb.compute_risk_parity_weights(wr, vols)

        assert rp_weights == [1.0]

    def test_zero_volatility_handling(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        vols = {"s1": 0.0, "s2": 0.0}

        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(wr, vols)

        assert result.portfolio_vol == 0.0
        assert len(result.budgets) == 2

    def test_default_correlation_assumption(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.4, 0.3, 0.3])
        vols = {"s1": 0.01, "s2": 0.01, "s3": 0.01}

        rb = RiskBudgeting()
        result = rb.compute_risk_budgets(wr, vols)

        assert result.portfolio_vol > 0
        assert len(result.budgets) == 3
