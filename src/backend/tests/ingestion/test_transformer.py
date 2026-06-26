import pytest

from app.feature_store.repository import FeatureItem
from app.ingestion.transformer import (
    FEATURE_CONFIDENCE,
    FEATURE_DEFINITIONS,
    FEATURE_SOURCE,
    FEATURE_VERSION,
    DataTransformer,
)


class TestDataTransformer:
    @pytest.fixture
    def transformer(self):
        return DataTransformer()

    def test_transform_complete_raw_data(self, transformer):
        raw = {
            "trend_strength": 65.5,
            "market_turnover": 72.3,
            "advancers_ratio": 55.0,
            "volatility_index": 40.0,
            "northbound_flow": 60.5,
        }
        items = transformer.transform(raw)
        assert len(items) == 5
        names = {item.name for item in items}
        assert names == {d["name"] for d in FEATURE_DEFINITIONS}

    def test_transform_assigns_metadata(self, transformer):
        raw = {
            "trend_strength": 80.0,
            "market_turnover": 75.0,
            "advancers_ratio": 55.0,
            "volatility_index": 40.0,
            "northbound_flow": 60.0,
        }
        items = transformer.transform(raw)
        for item in items:
            assert item.version == FEATURE_VERSION
            assert item.source == FEATURE_SOURCE
            assert item.confidence == FEATURE_CONFIDENCE
            assert item.timestamp is not None
            assert item.category in {"trend", "liquidity", "breadth", "volatility", "sentiment"}

    def test_transform_clips_out_of_range_values(self, transformer):
        raw = {
            "trend_strength": 150.0,
            "market_turnover": -10.0,
            "advancers_ratio": 55.0,
            "volatility_index": 40.0,
            "northbound_flow": 60.0,
        }
        items = transformer.transform(raw)
        trend_item = next(item for item in items if item.name == "trend_strength")
        turnover_item = next(item for item in items if item.name == "market_turnover")
        assert trend_item.value == 100.0
        assert turnover_item.value == 0.0

    def test_transform_rounds_values_to_2_decimals(self, transformer):
        raw = {
            "trend_strength": 65.555,
            "market_turnover": 72.301,
            "advancers_ratio": 55.0,
            "volatility_index": 40.0,
            "northbound_flow": 60.5,
        }
        items = transformer.transform(raw)
        trend_item = next(item for item in items if item.name == "trend_strength")
        turnover_item = next(item for item in items if item.name == "market_turnover")
        assert trend_item.value == 65.56
        assert turnover_item.value == 72.3

    def test_transform_missing_keys_default_to_zero(self, transformer):
        raw = {
            "trend_strength": 80.0,
        }
        items = transformer.transform(raw)
        assert len(items) == 5
        missing_item = next(item for item in items if item.name == "market_turnover")
        assert missing_item.value == 0.0

    def test_transform_all_items_are_feature_item(self, transformer):
        raw = {
            "trend_strength": 50.0,
            "market_turnover": 50.0,
            "advancers_ratio": 50.0,
            "volatility_index": 50.0,
            "northbound_flow": 50.0,
        }
        items = transformer.transform(raw)
        for item in items:
            assert isinstance(item, FeatureItem)

    def test_transform_correct_category_mapping(self, transformer):
        raw = {
            "trend_strength": 50.0,
            "market_turnover": 50.0,
            "advancers_ratio": 50.0,
            "volatility_index": 50.0,
            "northbound_flow": 50.0,
        }
        items = transformer.transform(raw)
        categories = {item.name: item.category for item in items}
        assert categories["trend_strength"] == "trend"
        assert categories["market_turnover"] == "liquidity"
        assert categories["advancers_ratio"] == "breadth"
        assert categories["volatility_index"] == "volatility"
        assert categories["northbound_flow"] == "sentiment"

    def test_transform_with_custom_metadata(self):
        custom = DataTransformer(version="2.0.0", source="test_source", confidence=0.5)
        raw = {
            "trend_strength": 50.0,
            "market_turnover": 50.0,
            "advancers_ratio": 50.0,
            "volatility_index": 50.0,
            "northbound_flow": 50.0,
        }
        items = custom.transform(raw)
        for item in items:
            assert item.version == "2.0.0"
            assert item.source == "test_source"
            assert item.confidence == 0.5
