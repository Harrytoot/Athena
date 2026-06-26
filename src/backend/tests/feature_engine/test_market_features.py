import pytest
from unittest.mock import AsyncMock

from app.feature_engine.market_features import (
    FEATURE_DEFINITIONS,
    FEATURE_VERSION,
    MarketFeatureEngine,
    MarketFeatures,
)
from app.feature_store.repository import FeatureItem
from app.providers.market.base import MarketProvider


class TestMarketFeatures:

    def test_market_features_dataclass(self):
        items = [
            FeatureItem(name="trend_strength", value=80.0, category="trend", timestamp=None, version="1.0.0", source="mock_v1", confidence=1.0),
            FeatureItem(name="market_turnover", value=75.0, category="liquidity", timestamp=None, version="1.0.0", source="mock_v1", confidence=1.0),
            FeatureItem(name="advancers_ratio", value=55.0, category="breadth", timestamp=None, version="1.0.0", source="mock_v1", confidence=1.0),
            FeatureItem(name="volatility_index", value=40.0, category="volatility", timestamp=None, version="1.0.0", source="mock_v1", confidence=1.0),
            FeatureItem(name="northbound_flow", value=60.0, category="sentiment", timestamp=None, version="1.0.0", source="mock_v1", confidence=1.0),
        ]
        features = MarketFeatures(items=items)
        assert features.trend_strength == 80.0
        assert features.market_turnover == 75.0
        assert features.advancers_ratio == 55.0
        assert features.volatility_index == 40.0
        assert features.northbound_flow == 60.0

    def test_market_features_get_by_name(self):
        items = [
            FeatureItem(name="trend_strength", value=80.0, category="trend", timestamp=None, version="1.0.0", source="mock_v1", confidence=1.0),
        ]
        features = MarketFeatures(items=items)
        item = features.get("trend_strength")
        assert item is not None
        assert item.value == 80.0
        assert features.get("nonexistent") is None

    def test_market_features_raises_on_missing(self):
        import pytest
        features = MarketFeatures(items=[])
        with pytest.raises(KeyError):
            _ = features.trend_strength


class TestMarketFeatureEngine:

    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock(spec=MarketProvider)
        provider.get_trend = AsyncMock(return_value=80.0)
        provider.get_liquidity = AsyncMock(return_value=75.0)
        provider.get_breadth = AsyncMock(return_value=55.0)
        provider.get_volatility = AsyncMock(return_value=40.0)
        provider.get_sentiment = AsyncMock(return_value=60.0)
        return provider

    @pytest.mark.asyncio
    async def test_collect_features_returns_correct_structure(self, mock_provider):
        engine = MarketFeatureEngine(provider=mock_provider)
        features = await engine.collect_features()

        assert isinstance(features, MarketFeatures)
        assert features.trend_strength == 80.0
        assert features.market_turnover == 75.0
        assert features.advancers_ratio == 55.0
        assert features.volatility_index == 40.0
        assert features.northbound_flow == 60.0

    @pytest.mark.asyncio
    async def test_collect_features_items_have_metadata(self, mock_provider):
        engine = MarketFeatureEngine(provider=mock_provider)
        features = await engine.collect_features()

        assert len(features.items) == 5
        for item in features.items:
            assert item.version == FEATURE_VERSION
            assert item.confidence == 1.0
            assert item.source == "mock_v1"
            assert item.timestamp is not None

    @pytest.mark.asyncio
    async def test_collect_features_categories(self, mock_provider):
        engine = MarketFeatureEngine(provider=mock_provider)
        features = await engine.collect_features()

        categories = {item.name: item.category for item in features.items}
        assert categories["trend_strength"] == "trend"
        assert categories["market_turnover"] == "liquidity"
        assert categories["advancers_ratio"] == "breadth"
        assert categories["volatility_index"] == "volatility"
        assert categories["northbound_flow"] == "sentiment"

    @pytest.mark.asyncio
    async def test_collect_features_calls_all_provider_methods(self, mock_provider):
        engine = MarketFeatureEngine(provider=mock_provider)
        await engine.collect_features()

        mock_provider.get_trend.assert_awaited_once()
        mock_provider.get_liquidity.assert_awaited_once()
        mock_provider.get_breadth.assert_awaited_once()
        mock_provider.get_volatility.assert_awaited_once()
        mock_provider.get_sentiment.assert_awaited_once()
