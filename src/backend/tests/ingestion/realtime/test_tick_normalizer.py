import pytest

from app.feature_store.repository import FeatureItem
from app.ingestion.realtime.schemas import MarketTick
from app.ingestion.realtime.tick_normalizer import (
    REALTIME_FEATURE_CONFIDENCE,
    REALTIME_FEATURE_DEFINITIONS,
    REALTIME_FEATURE_SOURCE,
    REALTIME_FEATURE_VERSION,
    TickNormalizer,
)


def _make_tick(symbol="000001", price=50.0, change_pct=1.0, volume=1e7, turnover=5e8,
               high=None, low=None, open_price=None, pre_close=None):
    return MarketTick(
        symbol=symbol,
        name=f"Stock_{symbol}",
        price=price,
        change_pct=change_pct,
        volume=volume,
        turnover=turnover,
        high=high or price * 1.01,
        low=low or price * 0.99,
        open=open_price or price * 0.995,
        pre_close=pre_close or price * 0.99,
        bid_price=price * 0.999,
        ask_price=price * 1.001,
        bid_volume=5000,
        ask_volume=3000,
    )


class TestTickNormalizer:

    @pytest.fixture
    def normalizer(self):
        return TickNormalizer()

    def test_normalize_produces_four_features(self, normalizer):
        tick = _make_tick()
        items = normalizer.normalize(tick)
        assert len(items) == len(REALTIME_FEATURE_DEFINITIONS)

    def test_normalize_prepends_symbol_to_name(self, normalizer):
        tick = _make_tick(symbol="600000")
        items = normalizer.normalize(tick)
        for item in items:
            assert item.name.startswith("600000:")

    def test_normalize_assigns_metadata(self, normalizer):
        tick = _make_tick()
        items = normalizer.normalize(tick)
        for item in items:
            assert item.version == REALTIME_FEATURE_VERSION
            assert item.source == REALTIME_FEATURE_SOURCE
            assert item.confidence == REALTIME_FEATURE_CONFIDENCE
            assert item.timestamp is not None

    def test_normalize_values_within_range(self, normalizer):
        tick = _make_tick()
        items = normalizer.normalize(tick)
        for item in items:
            assert 0.0 <= item.value <= 100.0

    def test_normalize_all_items_are_feature_item(self, normalizer):
        tick = _make_tick()
        items = normalizer.normalize(tick)
        for item in items:
            assert isinstance(item, FeatureItem)

    def test_normalize_with_categories(self, normalizer):
        tick = _make_tick()
        items = normalizer.normalize(tick)
        categories = {item.name.split(":")[-1]: item.category for item in items}
        assert categories.get("price_momentum") == "momentum"
        assert categories.get("volume_spike") == "liquidity"
        assert categories.get("bid_ask_spread") == "microstructure"
        assert categories.get("intraday_volatility") == "volatility"

    def test_normalize_batch(self, normalizer):
        ticks = [_make_tick("000001"), _make_tick("000002")]
        items = normalizer.normalize_batch(ticks)
        assert len(items) == 2 * len(REALTIME_FEATURE_DEFINITIONS)
        symbols = set(item.name.split(":")[0] for item in items)
        assert symbols == {"000001", "000002"}

    def test_normalize_batch_empty(self, normalizer):
        items = normalizer.normalize_batch([])
        assert items == []

    def test_normalize_with_avg_volume(self, normalizer):
        tick = _make_tick(volume=2e7)
        items = normalizer.normalize(tick, avg_volume=1e7)
        vol_item = next(i for i in items if i.name.endswith(":volume_spike"))
        assert vol_item.value > 50.0

    def test_normalize_with_negative_change(self, normalizer):
        tick = _make_tick(price=45.0, change_pct=-5.0, pre_close=50.0)
        items = normalizer.normalize(tick)
        momentum_item = next(i for i in items if i.name.endswith(":price_momentum"))
        assert momentum_item.value < 50.0

    def test_normalize_zero_pre_close(self, normalizer):
        tick = _make_tick(price=0, change_pct=0, pre_close=0)
        items = normalizer.normalize(tick)
        for item in items:
            assert 0.0 <= item.value <= 100.0

    def test_custom_metadata(self):
        normalizer = TickNormalizer(version="2.0.0", source="test", confidence=0.5)
        tick = _make_tick()
        items = normalizer.normalize(tick)
        for item in items:
            assert item.version == "2.0.0"
            assert item.source == "test"
            assert item.confidence == 0.5
