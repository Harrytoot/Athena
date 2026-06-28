import pytest

from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ConsistencyReport,
)
from app.decision_semantics.evolution.schema_evolver import SchemaEvolver
from app.decision_semantics.evolution.version_manager import (
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
)
from app.decision_api.semantic_cache import SemanticCache
from app.decision_semantics.registry import SemanticRegistry


def _make_v1_semantic(symbol: str = "AAPL") -> DecisionSemantic:
    return DecisionSemantic(
        symbol=symbol,
        name="Test Stock",
        signal=SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.85,
            base_confidence=82.0,
        ),
        factors=[
            FactorSemantic(
                name="trend",
                label="趋势",
                value=88.0,
                weight=0.30,
                contribution=26.4,
                is_bullish=True,
                assessment="强",
            ),
        ],
        risk=RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.35,
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            consistency_score=0.95,
        ),
        action="APPROVE",
        action_label="执行买入",
        summary="Test summary",
        semantic_version=SCHEMA_V1_0,
    )


class TestCacheVersionAwareness:

    def setup_method(self):
        self._cache = SemanticCache()
        self._cache.clear()
        self._evolver = SchemaEvolver()
        self._registry = SemanticRegistry()

    def test_cache_key_differs_by_version(self):
        v1 = _make_v1_semantic("AAPL")
        score_values = {"trend": 88.0, "liquidity": 72.0}

        key_v1_0 = self._cache.set(
            "AAPL",
            score_values,
            v1,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )

        v1_1 = self._evolver.to_v1_1(v1, strategy_id="s1")
        key_v1_1 = self._cache.set(
            "AAPL",
            score_values,
            v1_1,
            registry_version=SCHEMA_V1_1,
            timestamp_bucket="2025-01-01T00",
        )

        assert key_v1_0 != key_v1_1

    def test_cache_invalidation_on_version_bump(self):
        v1 = _make_v1_semantic("MSFT")
        score_values = {"trend": 75.0}

        cache_key = self._cache.set(
            "MSFT",
            score_values,
            v1,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )

        cached = self._cache.get(
            "MSFT",
            score_values,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )
        assert cached is not None

        miss_different_version = self._cache.get(
            "MSFT",
            score_values,
            registry_version=SCHEMA_V1_1,
            timestamp_bucket="2025-01-01T00",
        )
        assert miss_different_version is None

    def test_cache_retrieval_respects_version(self):
        v1_v1_0 = _make_v1_semantic("TSLA")
        v1_v1_1 = self._evolver.to_v1_1(
            _make_v1_semantic("TSLA"), strategy_id="s1"
        )
        score_values = {"trend": 90.0}

        self._cache.set(
            "TSLA",
            score_values,
            v1_v1_0,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )
        self._cache.set(
            "TSLA",
            score_values,
            v1_v1_1,
            registry_version=SCHEMA_V1_1,
            timestamp_bucket="2025-01-01T00",
        )

        cached_v1_0 = self._cache.get(
            "TSLA",
            score_values,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )
        cached_v1_1 = self._cache.get(
            "TSLA",
            score_values,
            registry_version=SCHEMA_V1_1,
            timestamp_bucket="2025-01-01T00",
        )

        assert cached_v1_0 is not None
        assert cached_v1_0.semantic_version == SCHEMA_V1_0
        assert cached_v1_1 is not None
        assert cached_v1_1.semantic_version == SCHEMA_V1_1

    def test_cache_clear_affects_all_versions(self):
        v1 = _make_v1_semantic("GOOG")
        score_values = {"trend": 80.0}

        self._cache.set(
            "GOOG",
            score_values,
            v1,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )
        self._cache.set(
            "GOOG",
            score_values,
            self._evolver.to_v1_1(_make_v1_semantic("GOOG")),
            registry_version=SCHEMA_V1_1,
            timestamp_bucket="2025-01-01T00",
        )

        assert self._cache.size == 2

        self._cache.clear()

        assert self._cache.size == 0

    def test_cache_size_tracks_versioned_entries(self):
        symbols = ["A", "B", "C"]
        for sym in symbols:
            v = _make_v1_semantic(sym)
            self._cache.set(
                sym,
                {"trend": 50.0},
                v,
                registry_version=SCHEMA_V1_0,
                timestamp_bucket="2025-01-01T00",
            )

        assert self._cache.size == 3

        for sym in symbols:
            v1_1 = self._evolver.to_v1_1(
                _make_v1_semantic(sym), strategy_id="s"
            )
            self._cache.set(
                sym,
                {"trend": 50.0},
                v1_1,
                registry_version=SCHEMA_V1_1,
                timestamp_bucket="2025-01-01T00",
            )

        assert self._cache.size == 6


class TestCacheVersionWithMultipleSymbols:

    def setup_method(self):
        self._cache = SemanticCache()
        self._cache.clear()
        self._evolver = SchemaEvolver()

    def test_different_symbols_same_version_different_keys(self):
        v1_aapl = _make_v1_semantic("AAPL")
        v1_msft = _make_v1_semantic("MSFT")
        score_values = {"trend": 88.0}

        key_aapl = self._cache.set(
            "AAPL",
            score_values,
            v1_aapl,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )
        key_msft = self._cache.set(
            "MSFT",
            score_values,
            v1_msft,
            registry_version=SCHEMA_V1_0,
            timestamp_bucket="2025-01-01T00",
        )

        assert key_aapl != key_msft

    def test_same_symbol_different_versions_separate_cache_entries(self):
        v1_0 = _make_v1_semantic("AAPL")
        v1_1 = self._evolver.to_v1_1(_make_v1_semantic("AAPL"), strategy_id="s1")
        v2_0 = self._evolver.to_v2_0(_make_v1_semantic("AAPL"))
        score_values = {"trend": 88.0}

        self._cache.set("AAPL", score_values, v1_0, registry_version=SCHEMA_V1_0)
        self._cache.set("AAPL", score_values, v1_1, registry_version=SCHEMA_V1_1)
        self._cache.set("AAPL", score_values, v2_0, registry_version=SCHEMA_V2_0)

        assert self._cache.size == 3
        assert self._cache.get("AAPL", score_values, registry_version=SCHEMA_V1_0) is not None
        assert self._cache.get("AAPL", score_values, registry_version=SCHEMA_V1_1) is not None
        assert self._cache.get("AAPL", score_values, registry_version=SCHEMA_V2_0) is not None


class TestCacheInvalidationCorrectness:

    def setup_method(self):
        self._cache = SemanticCache()
        self._cache.clear()
        self._evolver = SchemaEvolver()

    def test_updated_semantic_creates_new_key(self):
        symbol = "NVDA"
        score_values = {"trend": 92.0}
        bucket = "2025-06-01T00"

        v1 = _make_v1_semantic(symbol)
        key_old = self._cache.set(
            symbol, score_values, v1, registry_version=SCHEMA_V1_0, timestamp_bucket=bucket
        )

        v2 = _make_v1_semantic(symbol)
        v2.confidence_score = 0.99
        key_new = self._cache.set(
            symbol, score_values, v2, registry_version=SCHEMA_V1_0, timestamp_bucket=bucket
        )

        assert key_old == key_new

        assert self._cache.size == 1

    def test_different_timestamp_buckets_create_different_keys(self):
        symbol = "META"
        score_values = {"trend": 70.0}
        v1 = _make_v1_semantic(symbol)

        key_t1 = self._cache.set(
            symbol, score_values, v1,
            registry_version=SCHEMA_V1_0, timestamp_bucket="2025-01-01T00",
        )
        key_t2 = self._cache.set(
            symbol, score_values, v1,
            registry_version=SCHEMA_V1_0, timestamp_bucket="2025-01-01T01",
        )

        assert key_t1 != key_t2
