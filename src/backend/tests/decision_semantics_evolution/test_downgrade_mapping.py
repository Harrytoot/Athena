import pytest

from app.decision_semantics.evolution.backward_compatibility import (
    BackwardCompatibility,
    DowngradeMapping,
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
    ScenarioSemantic,
    ExecutionSemantic,
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
            FactorSemantic(
                name="liquidity",
                label="流动性",
                value=72.0,
                weight=0.25,
                contribution=18.0,
                is_bullish=True,
                assessment="偏多",
            ),
        ],
        risk=RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.35,
            warnings=["波动率偏高"],
        ),
        scenario=ScenarioSemantic(
            stability_score=0.75,
            worst_case_score_change=-18.0,
            state_change_count=1,
            entries=[
                {
                    "name": "crash",
                    "original_score": 78.0,
                    "simulated_score": 60.0,
                    "score_change": -18.0,
                    "state_changed": False,
                    "impact": "medium",
                }
            ],
        ),
        execution=ExecutionSemantic(
            feasibility=0.92,
            estimated_slippage_bps=5.0,
            estimated_fill_rate=0.98,
            quality_grade="A",
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action="APPROVE",
        action_label="执行买入",
        summary="Based on trend and liquidity factors",
        semantic_version=SCHEMA_V1_0,
    )


class TestDowngradeMappingValidation:

    def setup_method(self):
        self._compat = BackwardCompatibility()
        self._evolver = SchemaEvolver()

    def test_downgrade_v1_1_to_v1_0_drops_correct_fields(self):
        result = self._compat.get_mapping(SCHEMA_V1_1, SCHEMA_V1_0)
        assert result is not None
        assert "strategy_id" in result.dropped_fields
        assert "source_pipeline" in result.dropped_fields
        assert len(result.dropped_fields) == 2
        assert len(result.field_mappings) == 0

    def test_downgrade_v2_0_to_v1_1_maps_narrative_to_summary(self):
        result = self._compat.get_mapping(SCHEMA_V2_0, SCHEMA_V1_1)
        assert result is not None
        assert result.field_mappings.get("narrative") == "summary"
        assert "decision_id" in result.dropped_fields
        assert "tags" in result.dropped_fields

    def test_downgrade_v2_0_to_v1_0_maps_correctly(self):
        result = self._compat.get_mapping(SCHEMA_V2_0, SCHEMA_V1_0)
        assert result is not None
        assert result.field_mappings.get("narrative") == "summary"
        assert "decision_id" in result.dropped_fields
        assert "tags" in result.dropped_fields
        assert "strategy_id" in result.dropped_fields
        assert "source_pipeline" in result.dropped_fields

    def test_v1_1_to_v1_0_value_preservation(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(
            v1, strategy_id="strat_abc", source_pipeline="pipe_xyz"
        )

        downgraded = self._evolver.downgrade_to_target(v1_1, SCHEMA_V1_0)

        assert downgraded.symbol == v1.symbol
        assert downgraded.name == v1.name
        assert downgraded.signal.direction == v1.signal.direction
        assert downgraded.signal.strength == v1.signal.strength
        assert downgraded.confidence_score == v1.confidence_score
        assert downgraded.action == v1.action
        assert downgraded.summary == v1.summary
        assert downgraded.risk.overall_level == v1.risk.overall_level
        assert downgraded.scenario.stability_score == v1.scenario.stability_score
        assert downgraded.execution.feasibility == v1.execution.feasibility

    def test_v2_0_to_v1_0_value_preservation(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1,
            tags=["momentum", "trend_following"],
            narrative="V2 enhanced narrative text",
        )

        downgraded = self._evolver.downgrade_to_target(v2, SCHEMA_V1_0)

        assert downgraded.symbol == v1.symbol
        assert downgraded.name == v1.name
        assert downgraded.signal.direction == v1.signal.direction
        assert downgraded.confidence_score == v1.confidence_score
        assert downgraded.action == v1.action
        assert downgraded.summary == "V2 enhanced narrative text"

    def test_v2_0_to_v1_1_maps_back_summary(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1,
            tags=["value", "quality"],
            narrative="V2 narrative for v1.1 mapping test",
        )

        downgraded = self._evolver.downgrade_to_target(v2, SCHEMA_V1_1)

        assert downgraded.summary == "V2 narrative for v1.1 mapping test"
        assert downgraded.semantic_version == SCHEMA_V1_1

    def test_v2_0_to_v1_1_to_v1_0_chain(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1,
            tags=["chain_test"],
            narrative="Chain test narrative",
        )

        v1_1 = self._evolver.downgrade_to_target(v2, SCHEMA_V1_1)
        v1_0 = self._evolver.downgrade_to_target(v1_1, SCHEMA_V1_0)

        assert v1_1.summary == "Chain test narrative"
        assert v1_0.summary == "Chain test narrative"
        assert v1_0.symbol == v1.symbol


class TestDowngradeMappingEdgeCases:

    def setup_method(self):
        self._evolver = SchemaEvolver()

    def test_downgrade_v1_1_with_empty_extensions(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(v1)

        downgraded = self._evolver.downgrade_to_target(v1_1, SCHEMA_V1_0)

        assert downgraded.semantic_version == SCHEMA_V1_0
        assert downgraded.signal.direction == "LONG"

    def test_downgrade_v2_0_with_empty_optional_fields(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1)

        downgraded = self._evolver.downgrade_to_target(v2, SCHEMA_V1_0)

        assert downgraded.semantic_version == SCHEMA_V1_0
        assert downgraded.summary == v1.summary

    def test_downgrade_v2_0_minimal_data(self):
        minimal = DecisionSemantic(
            symbol="TEST",
            name="Test",
            signal=SignalSemantic(
                direction="NEUTRAL",
                direction_label="中性",
                strength=0.0,
                base_confidence=50.0,
            ),
            confidence_score=0.5,
            semantic_version=SCHEMA_V2_0,
        )
        evolver = SchemaEvolver()
        downgraded = evolver.downgrade_to_target(minimal, SCHEMA_V1_0)

        assert downgraded.semantic_version == SCHEMA_V1_0
        assert downgraded.symbol == "TEST"

    def test_downgrade_does_not_introduce_data_loss(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1,
            tags=["critical_data"],
            narrative="Important narrative that must be preserved",
        )

        v1_0 = self._evolver.downgrade_to_target(v2, SCHEMA_V1_0)

        assert v1_0.symbol == v1.symbol
        assert v1_0.signal.direction == v1.signal.direction
        assert v1_0.confidence_score == v1.confidence_score
        assert v1_0.summary == "Important narrative that must be preserved"
        assert v1_0.risk is not None
        assert v1_0.risk.overall_level == v1.risk.overall_level
        assert v1_0.scenario is not None
        assert v1_0.scenario.stability_score == v1.scenario.stability_score
        assert v1_0.execution is not None
        assert v1_0.execution.quality_grade == v1.execution.quality_grade
        assert v1_0.consistency is not None
        assert v1_0.consistency.consistency_score == pytest.approx(
            v1.consistency.consistency_score
        )
        assert v1_0.factors[0].name == v1.factors[0].name
        assert v1_0.factors[0].value == v1.factors[0].value

    def test_downgrade_mapping_correctness_across_roundtrip(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(
            v1,
            decision_id="d_roundtrip_001",
            tags=["roundtrip", "validation"],
            narrative="Roundtrip narrative test",
        )

        v1_0 = self._evolver.downgrade_to_target(v2, SCHEMA_V1_0)

        v2_again = self._evolver.to_v2_0(
            v1_0,
            tags=["roundtrip", "validation"],
            narrative="Roundtrip narrative test",
        )

        assert v2_again.narrative == "Roundtrip narrative test"
        assert v2_again.semantic_version == SCHEMA_V2_0
