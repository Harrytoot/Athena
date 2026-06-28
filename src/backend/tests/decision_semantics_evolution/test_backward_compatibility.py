import pytest

from app.decision_semantics.evolution.backward_compatibility import (
    BackwardCompatibility,
    is_backward_compatible,
)
from app.decision_semantics.evolution.schema_evolver import SchemaEvolver
from app.decision_semantics.evolution.version_manager import (
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ConsistencyReport,
)


def _make_v1_semantic() -> DecisionSemantic:
    return DecisionSemantic(
        symbol="AAPL",
        name="Apple Inc.",
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
                assessment="强看多",
            ),
        ],
        risk=RiskSemantic(
            overall_level="LOW",
            drawdown_risk=0.1,
            volatility_risk=0.2,
            correlation_risk=0.1,
            scenario_vulnerability=0.15,
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action="APPROVE",
        action_label="执行买入",
        summary="基于趋势因子的看多信号",
        semantic_version=SCHEMA_V1_0,
    )


class TestBackwardCompatibility:

    def setup_method(self):
        self._compat = BackwardCompatibility()
        self._evolver = SchemaEvolver()

    def test_can_serve_same_version(self):
        v1 = _make_v1_semantic()
        assert self._compat.can_serve(v1, SCHEMA_V1_0)

    def test_can_serve_v1_1_to_v1_0(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(v1)
        assert self._compat.can_serve(v1_1, SCHEMA_V1_0)

    def test_can_serve_v2_0_to_v1_0(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1)
        assert self._compat.can_serve(v2, SCHEMA_V1_0)

    def test_cannot_serve_downward(self):
        v1 = _make_v1_semantic()
        assert not self._compat.can_serve(v1, SCHEMA_V2_0)

    def test_serve_to_consumer_v1_1_to_v1_0(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(v1, strategy_id="s1")

        served = self._compat.serve_to_consumer(v1_1, SCHEMA_V1_0)

        assert served.semantic_version == SCHEMA_V1_0
        assert served.symbol == v1.symbol
        assert served.signal.direction == v1.signal.direction

    def test_serve_to_consumer_v2_0_to_v1_0(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, narrative="V2 narrative", tags=["tag"])

        served = self._compat.serve_to_consumer(v2, SCHEMA_V1_0)

        assert served.semantic_version == SCHEMA_V1_0
        assert served.summary == "V2 narrative"

    def test_serve_to_consumer_same_version_returns_original(self):
        v1 = _make_v1_semantic()
        served = self._compat.serve_to_consumer(v1, SCHEMA_V1_0)
        assert served is v1

    def test_validate_no_breaking_changes_same(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()
        issues = self._compat.validate_no_breaking_changes(v1, v2)
        assert len(issues) == 0

    def test_core_fields_present_in_upgraded(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, narrative="Test")
        v2.summary = v1.summary

        issues = self._compat.validate_no_breaking_changes(v1, v2)
        assert len(issues) == 0

    def test_get_mapping_v1_1_to_v1_0(self):
        mapping = self._compat.get_mapping(SCHEMA_V1_1, SCHEMA_V1_0)
        assert mapping is not None
        assert mapping.original_version == SCHEMA_V1_1
        assert mapping.target_version == SCHEMA_V1_0
        assert "strategy_id" in mapping.dropped_fields

    def test_get_mapping_v2_0_to_v1_0(self):
        mapping = self._compat.get_mapping(SCHEMA_V2_0, SCHEMA_V1_0)
        assert mapping is not None
        assert mapping.field_mappings.get("narrative") == "summary"

    def test_register_custom_mapping(self):
        from app.decision_semantics.evolution.backward_compatibility import (
            DowngradeMapping,
        )
        custom = DowngradeMapping(
            original_version="3.0.0",
            target_version="2.0.0",
            dropped_fields=["custom_field"],
        )
        self._compat.register_mapping("3.0.0", "2.0.0", custom)
        assert self._compat.get_mapping("3.0.0", "2.0.0") is custom


class TestStandaloneBackwardCompatibility:

    def test_is_backward_compatible_function(self):
        v1 = _make_v1_semantic()
        evolver = SchemaEvolver()
        v1_1 = evolver.to_v1_1(v1)

        assert is_backward_compatible(v1_1, SCHEMA_V1_0)

    def test_is_backward_compatible_function_false(self):
        v1 = _make_v1_semantic()
        assert not is_backward_compatible(v1, SCHEMA_V2_0)


class TestBackwardCompatibilityWithConsumer:

    def setup_method(self):
        self._compat = BackwardCompatibility()
        self._evolver = SchemaEvolver()

    def test_old_consumer_works_with_v1_1(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(
            v1, strategy_id="strat_v3", source_pipeline="prod"
        )

        v1_0_output = self._compat.serve_to_consumer(v1_1, SCHEMA_V1_0)

        assert v1_0_output.symbol == "AAPL"
        assert v1_0_output.signal.direction == "LONG"
        assert v1_0_output.confidence_score == 0.82
        assert v1_0_output.semantic_version == SCHEMA_V1_0

    def test_old_consumer_works_with_v2_0(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1, tags=["prod"], narrative="Updated narrative"
        )

        v1_0_output = self._compat.serve_to_consumer(v2, SCHEMA_V1_0)

        assert v1_0_output.symbol == "AAPL"
        assert v1_0_output.summary == "Updated narrative"
        assert v1_0_output.semantic_version == SCHEMA_V1_0

    def test_v1_1_consumer_works_with_v2_0(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1, tags=["test"], narrative="V2 narrative"
        )

        v1_1_output = self._compat.serve_to_consumer(v2, SCHEMA_V1_1)

        assert v1_1_output.semantic_version == SCHEMA_V1_1
        assert v1_1_output.summary == "V2 narrative"

    def test_multiple_consumers_different_versions(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1, tags=["multi"], narrative="Multi-version test"
        )

        v1_0_out = self._compat.serve_to_consumer(v2, SCHEMA_V1_0)
        v1_1_out = self._compat.serve_to_consumer(v2, SCHEMA_V1_1)

        assert v1_0_out.semantic_version == SCHEMA_V1_0
        assert v1_1_out.semantic_version == SCHEMA_V1_1
        assert v1_0_out.symbol == v1_1_out.symbol
