from decimal import Decimal

from app.domain.entities.recommendation import Recommendation, RecommendationAction, RecommendationItem, RecommendationPriority, RecommendationSource


class TestRecommendationItem:

    def test_create_item(self):
        item = RecommendationItem(
            symbol="600519", name="贵州茅台",
            action=RecommendationAction.BUY,
            priority=RecommendationPriority.HIGH,
            source=RecommendationSource.FUNDAMENTAL,
            confidence=Decimal("85"),
            reason="估值合理，建议买入",
        )
        assert item.symbol == "600519"
        assert item.action == RecommendationAction.BUY
        assert item.priority == RecommendationPriority.HIGH
        assert item.confidence == Decimal("85")

    def test_default_values(self):
        item = RecommendationItem()
        assert item.action == RecommendationAction.WATCH
        assert item.priority == RecommendationPriority.LOW
        assert item.confidence == Decimal("0")


class TestRecommendation:

    def test_create_recommendation(self):
        r = Recommendation(
            id="r1",
            market_regime="Bull",
            market_temperature=65,
            summary="市场向好，建议积极操作",
        )
        r.add_item(RecommendationItem(symbol="600519", name="茅台", action=RecommendationAction.BUY, priority=RecommendationPriority.HIGH, source=RecommendationSource.FUNDAMENTAL, confidence=Decimal("85"), reason="估值合理"))
        assert len(r.items) == 1
        assert r.market_regime == "Bull"
        assert r.summary == "市场向好，建议积极操作"

    def test_empty_recommendation(self):
        r = Recommendation()
        assert len(r.items) == 0
        assert r.market_regime == ""
