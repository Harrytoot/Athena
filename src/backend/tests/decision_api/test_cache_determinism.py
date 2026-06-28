import pytest

from app.decision_api.semantic_cache import SemanticCache, _make_hash
from app.decision_semantics.registry import DEFAULT_SEMANTIC_VERSION
from app.decision_semantics.schema import (
    DecisionSemantic,
    FactorSemantic,
    SignalSemantic,
)


class TestCacheDeterminism:

    def setup_method(self):
        self._cache = SemanticCache()
        self._cache.clear()

    def teardown_method(self):
        self._cache.clear()

    def _make_semantic(self, symbol: str = "TEST") -> DecisionSemantic:
        return DecisionSemantic(
            symbol=symbol,
            name="Test Stock",
            signal=SignalSemantic(direction="LONG", direction_label="看多", strength=0.8, base_confidence=85.0),
            factors=[FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强")],
            confidence_score=0.75,
            semantic_version=DEFAULT_SEMANTIC_VERSION,
        )

    def test_cache_key_deterministic(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}

        key1 = _make_hash("AAPL", score_values, "1.0.0", "2024-01-01T10")
        key2 = _make_hash("AAPL", score_values, "1.0.0", "2024-01-01T10")
        assert key1 == key2

    def test_cache_key_varies_by_symbol(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}

        key1 = _make_hash("AAPL", score_values, "1.0.0", "2024-01-01T10")
        key2 = _make_hash("600519", score_values, "1.0.0", "2024-01-01T10")
        assert key1 != key2

    def test_cache_key_varies_by_scores(self):
        scores1 = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}
        scores2 = {"trend": 20.0, "liquidity": 30.0, "breadth": 40.0, "volatility": 50.0, "sentiment": 60.0}

        key1 = _make_hash("AAPL", scores1, "1.0.0", "2024-01-01T10")
        key2 = _make_hash("AAPL", scores2, "1.0.0", "2024-01-01T10")
        assert key1 != key2

    def test_cache_key_varies_by_version(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}

        key1 = _make_hash("AAPL", score_values, "1.0.0", "2024-01-01T10")
        key2 = _make_hash("AAPL", score_values, "2.0.0", "2024-01-01T10")
        assert key1 != key2

    def test_cache_key_varies_by_time_bucket(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}

        key1 = _make_hash("AAPL", score_values, "1.0.0", "2024-01-01T10")
        key2 = _make_hash("AAPL", score_values, "1.0.0", "2024-01-01T11")
        assert key1 != key2

    def test_cache_get_returns_none_when_empty(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}
        result = self._cache.get("AAPL", score_values)
        assert result is None

    def test_cache_set_and_get(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}
        semantic = self._make_semantic("AAPL")

        key = self._cache.set("AAPL", score_values, semantic)
        assert key is not None

        cached = self._cache.get("AAPL", score_values)
        assert cached is not None
        assert cached.symbol == "AAPL"
        assert cached.signal.direction == "LONG"

    def test_cache_same_returns_identical_object(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}
        semantic = self._make_semantic("AAPL")

        self._cache.set("AAPL", score_values, semantic)

        result1 = self._cache.get("AAPL", score_values)
        result2 = self._cache.get("AAPL", score_values)
        assert result1 is result2

    def test_cache_clear(self):
        score_values = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}
        self._cache.set("AAPL", score_values, self._make_semantic("AAPL"))
        assert self._cache.size == 1

        self._cache.clear()
        assert self._cache.size == 0

    def test_cache_different_scores_different_keys(self):
        scores1 = {"trend": 80.0, "liquidity": 70.0, "breadth": 60.0, "volatility": 50.0, "sentiment": 40.0}
        scores2 = {"trend": 20.0, "liquidity": 30.0, "breadth": 40.0, "volatility": 50.0, "sentiment": 60.0}

        sem1 = self._make_semantic("AAPL")
        sem2 = self._make_semantic("AAPL")

        self._cache.set("AAPL", scores1, sem1)
        self._cache.set("AAPL", scores2, sem2)
        assert self._cache.size == 2

        cached1 = self._cache.get("AAPL", scores1)
        cached2 = self._cache.get("AAPL", scores2)
        assert cached1 is sem1
        assert cached2 is sem2
        assert cached1 is not cached2
