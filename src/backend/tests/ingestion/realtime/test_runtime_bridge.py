from datetime import datetime, timezone

import pytest

from app.decision_semantics.schema import DecisionSemantic
from app.feature_store.repository import FeatureItem
from app.ingestion.realtime.runtime_bridge import RuntimeBridge


def _make_feature_item(symbol: str, name: str, value: float, category: str) -> FeatureItem:
    return FeatureItem(
        name=f"{symbol}:{name}",
        value=value,
        category=category,
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        source="realtime_v1",
        confidence=0.90,
    )


def _make_features(symbol: str, momentum: float = 60.0, volume_spike: float = 55.0,
                   spread: float = 40.0, volatility: float = 30.0) -> list[FeatureItem]:
    return [
        _make_feature_item(symbol, "price_momentum", momentum, "momentum"),
        _make_feature_item(symbol, "volume_spike", volume_spike, "liquidity"),
        _make_feature_item(symbol, "bid_ask_spread", spread, "microstructure"),
        _make_feature_item(symbol, "intraday_volatility", volatility, "volatility"),
    ]


class TestRuntimeBridge:

    @pytest.fixture
    def bridge(self):
        return RuntimeBridge()

    @pytest.mark.asyncio
    async def test_map_and_trigger_returns_decision_semantic(self, bridge):
        features = _make_features("000001", momentum=70.0)
        result = await bridge.map_and_trigger(features, "000001")
        assert isinstance(result, DecisionSemantic)
        assert result.symbol == "000001"

    @pytest.mark.asyncio
    async def test_bullish_features_produce_long_signal(self, bridge):
        features = _make_features("000001", momentum=70.0, volume_spike=65.0,
                                  spread=60.0, volatility=25.0)
        result = await bridge.map_and_trigger(features, "000001")
        assert result.signal.direction == "LONG"

    @pytest.mark.asyncio
    async def test_bearish_features_produce_short_signal(self, bridge):
        features = _make_features("000001", momentum=20.0, volume_spike=25.0,
                                  spread=30.0, volatility=75.0)
        result = await bridge.map_and_trigger(features, "000001")
        assert result.signal.direction == "SHORT"

    @pytest.mark.asyncio
    async def test_no_features_returns_none(self, bridge):
        result = await bridge.map_and_trigger([], "000001")
        assert result is None

    @pytest.mark.asyncio
    async def test_features_includes_factors(self, bridge):
        features = _make_features("000001")
        result = await bridge.map_and_trigger(features, "000001")
        assert len(result.factors) == 4

    @pytest.mark.asyncio
    async def test_risk_assessment_included(self, bridge):
        features = _make_features("000001")
        result = await bridge.map_and_trigger(features, "000001")
        assert result.risk is not None
        assert result.risk.overall_level in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_confidence_within_range(self, bridge):
        features = _make_features("000001")
        result = await bridge.map_and_trigger(features, "000001")
        assert 0.0 <= result.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_runtime_state_tracks_symbol(self, bridge):
        features = _make_features("000001", momentum=70.0)
        await bridge.map_and_trigger(features, "000001")

        active = bridge.get_runtime().get_active("000001")
        assert active is not None
        assert active.symbol == "000001"

    @pytest.mark.asyncio
    async def test_runtime_update_updates_existing(self, bridge):
        features1 = _make_features("000001", momentum=70.0)
        features2 = _make_features("000001", momentum=30.0)

        await bridge.map_and_trigger(features1, "000001")
        await bridge.map_and_trigger(features2, "000001")

        active = bridge.get_runtime().get_active("000001")
        assert active is not None

        history = bridge.get_runtime().get_history("000001")
        assert len(history.snapshots) >= 2

    @pytest.mark.asyncio
    async def test_consistency_report_generated(self, bridge):
        features = _make_features("000001")
        result = await bridge.map_and_trigger(features, "000001")
        assert result.consistency is not None

    @pytest.mark.asyncio
    async def test_multiple_symbols_isolation(self, bridge):
        f1 = _make_features("000001", momentum=70.0)
        f2 = _make_features("000002", momentum=20.0)

        r1 = await bridge.map_and_trigger(f1, "000001")
        r2 = await bridge.map_and_trigger(f2, "000002")

        assert r1.symbol == "000001"
        assert r2.symbol == "000002"
        assert r1.signal.direction != r2.signal.direction
