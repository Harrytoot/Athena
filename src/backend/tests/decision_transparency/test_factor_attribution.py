import pytest

from app.decision_transparency.factor_attribution import (
    FactorAttributionEngine,
    FactorAttribution,
    FactorAttributionItem,
)
from app.domain.market.market_score import MarketScore


class TestFactorAttributionEngine:

    def test_attribute_strong_bull(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=90.0, liquidity=85.0, breadth=80.0, volatility=70.0, sentiment=75.0)
        result = engine.attribute(score)

        assert result.total_score == score.total
        assert len(result.items) == 5
        assert all(item.is_positive for item in result.items)
        assert result.positive_contribution_sum > 0
        assert result.negative_contribution_sum == 0.0

    def test_attribute_with_negative_factors(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=10.0, liquidity=15.0, breadth=20.0, volatility=30.0, sentiment=12.0)
        result = engine.attribute(score)

        assert result.total_score < 30.0
        assert result.dominant_factor != ""

    def test_contributions_sum_to_near_total(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=75.0, liquidity=60.0, breadth=55.0, volatility=45.0, sentiment=65.0)

        result = engine.attribute(score)

        weighted_sum = sum(item.weighted_contribution for item in result.items)
        assert weighted_sum == pytest.approx(result.total_score, rel=1e-6)

    def test_contribution_percentages(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=60.0, liquidity=60.0, breadth=60.0, volatility=60.0, sentiment=60.0)

        result = engine.attribute(score)

        for item in result.items:
            expected_pct = item.weighted_contribution / 100.0 * 100
            assert item.contribution_percentage == pytest.approx(expected_pct, rel=1e-4)

    def test_dominant_factor_is_largest_contributor(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=90.0, liquidity=30.0, breadth=30.0, volatility=30.0, sentiment=30.0)

        result = engine.attribute(score)

        assert result.dominant_factor == "trend"
        max_contrib = max(item.weighted_contribution for item in result.items)
        dominant_item = next(i for i in result.items if i.factor_name == result.dominant_factor)
        assert dominant_item.weighted_contribution == max_contrib

    def test_consensus_strong_bull(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=90.0, liquidity=85.0, breadth=80.0, volatility=75.0, sentiment=88.0)

        result = engine.attribute(score)

        assert "看多" in result.factor_consensus

    def test_consensus_strong_bear(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=10.0, liquidity=15.0, breadth=20.0, volatility=5.0, sentiment=8.0)

        result = engine.attribute(score)

        assert "看空" in result.factor_consensus

    def test_consensus_divergent(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=80.0, liquidity=20.0, breadth=50.0, volatility=70.0, sentiment=30.0)

        result = engine.attribute(score)

        assert "分歧" in result.factor_consensus or "偏" in result.factor_consensus

    def test_attribution_summary_not_empty(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=70.0, liquidity=65.0, breadth=60.0, volatility=55.0, sentiment=50.0)

        result = engine.attribute(score)
        assert len(result.attribution_summary) > 0

    def test_interpretations_match_values(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=95.0, liquidity=85.0, breadth=5.0, volatility=15.0, sentiment=50.0)

        result = engine.attribute(score)

        trend_item = next(i for i in result.items if i.factor_name == "trend")
        assert "强势" in trend_item.interpretation or "极强" in trend_item.interpretation

        breadth_item = next(i for i in result.items if i.factor_name == "breadth")
        assert "普跌" in breadth_item.interpretation or "极弱" in breadth_item.interpretation

    def test_factor_labels_not_empty(self):
        engine = FactorAttributionEngine()
        score = MarketScore(trend=50.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)

        result = engine.attribute(score)

        for item in result.items:
            assert len(item.factor_label) > 0
