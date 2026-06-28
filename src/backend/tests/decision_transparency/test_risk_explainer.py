import pytest

from app.decision_transparency.risk_explainer import (
    RiskExplainer,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_MODERATE,
    RISK_LEVEL_LOW,
)


class TestRiskExplainerDrawdown:

    def test_high_drawdown(self):
        explainer = RiskExplainer()
        result = explainer.explain_drawdown(
            max_drawdown=-0.25,
            avg_drawdown=-0.10,
            drawdown_count=5,
            avg_duration_days=20.0,
            ulcer_index=0.15,
        )
        assert result.risk_level == RISK_LEVEL_HIGH
        assert result.max_drawdown_pct == pytest.approx(-25.0)
        assert result.drawdown_count == 5

    def test_moderate_drawdown(self):
        explainer = RiskExplainer()
        result = explainer.explain_drawdown(
            max_drawdown=-0.15,
            avg_drawdown=-0.05,
            drawdown_count=3,
            avg_duration_days=10.0,
            ulcer_index=0.08,
        )
        assert result.risk_level == RISK_LEVEL_MODERATE

    def test_low_drawdown(self):
        explainer = RiskExplainer()
        result = explainer.explain_drawdown(
            max_drawdown=-0.05,
            avg_drawdown=-0.02,
            drawdown_count=1,
            avg_duration_days=3.0,
            ulcer_index=0.01,
        )
        assert result.risk_level == RISK_LEVEL_LOW

    def test_drawdown_explanation_not_empty(self):
        explainer = RiskExplainer()
        result = explainer.explain_drawdown(
            max_drawdown=-0.30,
            avg_drawdown=-0.12,
            drawdown_count=7,
            avg_duration_days=25.0,
            ulcer_index=0.20,
        )
        assert len(result.explanation) > 0
        assert "25.0" in result.explanation or "25" in result.explanation


class TestRiskExplainerVolatility:

    def test_volatility_from_returns(self):
        explainer = RiskExplainer()
        returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015, 0.01, -0.005, 0.0]
        result = explainer.explain_volatility(returns)
        assert result.annualized_volatility > 0
        assert result.daily_volatility > 0
        assert result.worst_day_return <= 0

    def test_volatility_insufficient_data(self):
        explainer = RiskExplainer()
        result = explainer.explain_volatility([0.01])
        assert result.risk_level == RISK_LEVEL_LOW
        assert "不足" in result.explanation

    def test_volatility_empty(self):
        explainer = RiskExplainer()
        result = explainer.explain_volatility([])
        assert result.annualized_volatility == 0.0
        assert "不足" in result.explanation

    def test_var_cvar_computed(self):
        explainer = RiskExplainer()
        returns = [-0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05]
        result = explainer.explain_volatility(returns)
        assert result.var_95_daily <= 0
        assert result.cvar_95_daily <= result.var_95_daily

    def test_tail_ratio(self):
        explainer = RiskExplainer()
        returns = [0.01, 0.02, -0.005, 0.015, -0.01]
        result = explainer.explain_volatility(returns)
        assert result.tail_ratio > 0


class TestRiskExplainerCorrelation:

    def test_high_correlation(self):
        explainer = RiskExplainer()
        result = explainer.explain_correlation(
            positions_count=3,
            avg_pairwise_corr=0.85,
            max_single_exposure=0.40,
        )
        assert result.risk_level == RISK_LEVEL_HIGH
        assert result.diversification_score < 0.5

    def test_low_correlation(self):
        explainer = RiskExplainer()
        result = explainer.explain_correlation(
            positions_count=10,
            avg_pairwise_corr=0.10,
            max_single_exposure=0.15,
        )
        assert result.risk_level == RISK_LEVEL_LOW
        assert result.diversification_score > 0.5

    def test_moderate_correlation(self):
        explainer = RiskExplainer()
        result = explainer.explain_correlation(
            positions_count=5,
            avg_pairwise_corr=0.55,
        )
        assert result.risk_level == RISK_LEVEL_MODERATE

    def test_single_position(self):
        explainer = RiskExplainer()
        result = explainer.explain_correlation(
            positions_count=1,
            avg_pairwise_corr=0.0,
        )
        assert "单一" in result.concentration_risk

    def test_zero_positions(self):
        explainer = RiskExplainer()
        result = explainer.explain_correlation(
            positions_count=0,
            avg_pairwise_corr=0.0,
        )
        assert "无持仓" in result.concentration_risk

    def test_high_concentration(self):
        explainer = RiskExplainer()
        result = explainer.explain_correlation(
            positions_count=3,
            avg_pairwise_corr=0.40,
            max_single_exposure=0.60,
        )
        assert "集中" in result.concentration_risk


class TestRiskExplainerOverall:

    def test_overall_high_when_two_high(self):
        explainer = RiskExplainer()
        dd = explainer.explain_drawdown(-0.30, -0.15, 5, 20.0, 0.20)
        vol = explainer.explain_volatility([-0.05, 0.01, -0.04, 0.02, -0.03])
        corr = explainer.explain_correlation(3, 0.80)

        level, summary, warnings = explainer.build_overall(dd, vol, corr)
        assert level == RISK_LEVEL_HIGH
        assert len(warnings) >= 0

    def test_overall_low_when_all_low(self):
        explainer = RiskExplainer()
        dd = explainer.explain_drawdown(-0.03, -0.01, 1, 2.0, 0.01)
        vol = explainer.explain_volatility([0.001, 0.002, -0.001, 0.001, 0.0])
        corr = explainer.explain_correlation(10, 0.10)

        level, summary, warnings = explainer.build_overall(dd, vol, corr)
        assert level == RISK_LEVEL_LOW

    def test_warnings_generated_for_high_risks(self):
        explainer = RiskExplainer()
        dd = explainer.explain_drawdown(-0.30, -0.15, 5, 20.0, 0.20)
        vol = explainer.explain_volatility([-0.05, 0.01, -0.04, 0.02, -0.03, -0.02, 0.01, -0.03])
        corr = explainer.explain_correlation(3, 0.85)

        level, summary, warnings = explainer.build_overall(dd, vol, corr)
        assert len(summary) > 0
