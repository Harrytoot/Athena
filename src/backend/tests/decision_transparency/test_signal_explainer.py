import pytest

from app.decision_transparency.signal_explainer import (
    SignalExplainer,
    SignalExplanation,
    FactorNarrative,
)
from app.domain.market.market_score import MarketScore


class TestSignalExplainer:

    def test_strong_bull_explanation(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=90.0, liquidity=85.0, breadth=80.0, volatility=70.0, sentiment=75.0)
        result = explainer.explain(score)

        assert result.direction == "LONG"
        assert result.direction_label == "看多"
        assert result.market_state == "Strong Bull"
        assert result.total_score == score.total
        assert result.confidence_score >= 75.0
        assert len(result.factor_narratives) == 5
        assert len(result.summary) > 0

    def test_bear_explanation(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=10.0, liquidity=15.0, breadth=20.0, volatility=30.0, sentiment=12.0)
        result = explainer.explain(score)

        assert result.direction == "SHORT"
        assert result.direction_label == "看空"
        assert result.market_state == "Extreme Bear"
        assert result.confidence_score >= 75.0

    def test_neutral_explanation(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=50.0, liquidity=48.0, breadth=52.0, volatility=45.0, sentiment=55.0)
        result = explainer.explain(score)

        assert result.direction == "NEUTRAL"
        assert result.direction_label == "中性"
        assert result.market_state == "Neutral"

    def test_confidence_very_high(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=98.0, liquidity=96.0, breadth=94.0, volatility=92.0, sentiment=95.0)
        result = explainer.explain(score)

        assert result.confidence_level in ("HIGH", "VERY_HIGH")
        assert result.confidence_score >= 85.0

    def test_confidence_low_on_mixed(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=80.0, liquidity=20.0, breadth=50.0, volatility=70.0, sentiment=30.0)
        result = explainer.explain(score)

        assert result.confidence_level in ("MODERATE", "LOW")

    def test_factor_narratives_present(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=75.0, liquidity=60.0, breadth=55.0, volatility=45.0, sentiment=65.0)
        result = explainer.explain(score)

        names = {n.name for n in result.factor_narratives}
        assert names == {"trend", "liquidity", "breadth", "volatility", "sentiment"}

        for n in result.factor_narratives:
            assert len(n.assessment) > 0
            assert n.weight > 0
            assert n.contribution == pytest.approx(n.value * n.weight, rel=1e-4)

    def test_confidence_bounded_zero_to_hundred(self):
        explainer = SignalExplainer()
        score = MarketScore(trend=0.0, liquidity=100.0, breadth=0.0, volatility=100.0, sentiment=0.0)
        result = explainer.explain(score)
        assert 0.0 <= result.confidence_score <= 100.0

    def test_all_states_explained(self):
        explainer = SignalExplainer()
        test_cases = [
            (95.0, "Strong Bull"),
            (70.0, "Bull"),
            (50.0, "Neutral"),
            (30.0, "Bear"),
            (5.0, "Extreme Bear"),
        ]
        for val, expected_state in test_cases:
            score = MarketScore(trend=val, liquidity=val, breadth=val, volatility=val, sentiment=val)
            result = explainer.explain(score)
            assert result.market_state == expected_state

    def test_custom_weights(self):
        explainer = SignalExplainer(
            trend_weight=0.40,
            liquidity_weight=0.20,
            breadth_weight=0.20,
            volatility_weight=0.10,
            sentiment_weight=0.10,
        )
        score = MarketScore(trend=80.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)
        result = explainer.explain(score)
        assert result.total_score > 0
