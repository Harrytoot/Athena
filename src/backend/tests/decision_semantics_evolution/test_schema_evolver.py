import pytest

from app.decision_semantics.evolution.schema_evolver import (
    SchemaEvolver,
    UpgradeResult,
    DowngradeResult,
)
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
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action="APPROVE",
        action_label="执行买入",
        summary="基于趋势和流动性因子的看多信号",
        semantic_version=SCHEMA_V1_0,
    )


class TestSchemaEvolverUpgrade:

    def setup_method(self):
        self._evolver = SchemaEvolver()

    def test_upgrade_v1_0_to_v1_1(self):
        v1 = _make_v1_semantic()
        result = self._evolver.upgrade(v1, SCHEMA_V1_1)

        assert isinstance(result, UpgradeResult)
        assert result.from_version == SCHEMA_V1_0
        assert result.to_version == SCHEMA_V1_1
        assert len(result.applied_rules) == 2
        assert result.result.semantic_version == SCHEMA_V1_1
        assert result.result.symbol == "AAPL"
        assert result.result.signal.direction == "LONG"
        assert result.result.confidence_score == 0.82
        assert hasattr(result.result, "strategy_id")
        assert result.result.strategy_id == ""
        assert hasattr(result.result, "source_pipeline")
        assert result.result.source_pipeline == ""

    def test_upgrade_v1_0_to_v1_1_preserves_core_data(self):
        v1 = _make_v1_semantic()
        result = self._evolver.upgrade(v1, SCHEMA_V1_1)

        assert result.result.symbol == v1.symbol
        assert result.result.name == v1.name
        assert result.result.signal.direction == v1.signal.direction
        assert len(result.result.factors) == len(v1.factors)
        assert result.result.risk.overall_level == v1.risk.overall_level
        assert result.result.scenario.stability_score == v1.scenario.stability_score
        assert result.result.consistency.consistency_score == pytest.approx(0.95)

    def test_upgrade_v1_1_to_v2_0(self):
        v1 = _make_v1_semantic()
        v1_1_result = self._evolver.upgrade_to_target(v1, SCHEMA_V1_1)
        v1_1_result.strategy_id = "strat_001"
        v1_1_result.source_pipeline = "pipeline_v2"

        v2_result = self._evolver.upgrade(v1_1_result, SCHEMA_V2_0)

        assert isinstance(v2_result, UpgradeResult)
        assert v2_result.from_version == SCHEMA_V1_1
        assert v2_result.to_version == SCHEMA_V2_0
        assert v2_result.result.semantic_version == SCHEMA_V2_0
        assert hasattr(v2_result.result, "decision_id")
        assert len(v2_result.result.decision_id) > 0
        assert hasattr(v2_result.result, "tags")
        assert v2_result.result.tags == []
        assert hasattr(v2_result.result, "narrative")
        assert v2_result.result.narrative == v1_1_result.summary

    def test_upgrade_v1_0_to_v2_0_direct(self):
        v1 = _make_v1_semantic()
        result = self._evolver.upgrade(v1, SCHEMA_V2_0)

        assert result.to_version == SCHEMA_V2_0
        assert result.result.semantic_version == SCHEMA_V2_0
        assert hasattr(result.result, "decision_id")
        assert hasattr(result.result, "tags")
        assert hasattr(result.result, "narrative")
        assert len(result.applied_rules) == 5

    def test_upgrade_same_version_noop(self):
        v1 = _make_v1_semantic()
        result = self._evolver.upgrade(v1, SCHEMA_V1_0)

        assert result.from_version == SCHEMA_V1_0
        assert result.to_version == SCHEMA_V1_0
        assert len(result.applied_rules) == 0
        assert result.result is v1

    def test_upgrade_to_v1_1_with_strategy_data(self):
        v1 = _make_v1_semantic()
        upgraded = self._evolver.to_v1_1(
            v1,
            strategy_id="momentum_strat_v3",
            source_pipeline="production_pipeline_1",
        )

        assert upgraded.semantic_version == SCHEMA_V1_1
        assert upgraded.strategy_id == "momentum_strat_v3"
        assert upgraded.source_pipeline == "production_pipeline_1"

    def test_upgrade_to_v2_0_with_full_data(self):
        v1 = _make_v1_semantic()
        upgraded = self._evolver.to_v2_0(
            v1,
            decision_id="d_abc123",
            tags=["momentum", "trend"],
            narrative="Strong bullish signal based on trend and liquidity",
        )

        assert upgraded.semantic_version == SCHEMA_V2_0
        assert upgraded.decision_id == "d_abc123"
        assert upgraded.tags == ["momentum", "trend"]
        assert upgraded.narrative == "Strong bullish signal based on trend and liquidity"

    def test_upgrade_no_path_raises(self):
        v2 = _make_v1_semantic()
        v2.semantic_version = SCHEMA_V2_0
        with pytest.raises(ValueError, match="No upgrade path"):
            self._evolver.upgrade(v2, SCHEMA_V1_0)


class TestSchemaEvolverDowngrade:

    def setup_method(self):
        self._evolver = SchemaEvolver()

    def test_downgrade_v1_1_to_v1_0(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(
            v1, strategy_id="s1", source_pipeline="p1"
        )

        result = self._evolver.downgrade(v1_1, SCHEMA_V1_0)

        assert isinstance(result, DowngradeResult)
        assert result.from_version == SCHEMA_V1_1
        assert result.to_version == SCHEMA_V1_0
        assert result.result.semantic_version == SCHEMA_V1_0
        assert "strategy_id" in result.dropped_fields
        assert "source_pipeline" in result.dropped_fields

    def test_downgrade_v1_1_to_v1_0_preserves_core_data(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(
            v1, strategy_id="s1", source_pipeline="p1"
        )

        result = self._evolver.downgrade(v1_1, SCHEMA_V1_0)

        assert result.result.symbol == "AAPL"
        assert result.result.signal.direction == "LONG"
        assert result.result.confidence_score == 0.82
        assert len(result.result.factors) == 2
        assert result.result.risk.overall_level == "MODERATE"
        assert result.result.summary == v1.summary

    def test_downgrade_v2_0_to_v1_1(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, tags=["tag1"], narrative="Test narrative")

        result = self._evolver.downgrade(v2, SCHEMA_V1_1)

        assert result.to_version == SCHEMA_V1_1
        assert result.result.semantic_version == SCHEMA_V1_1
        assert "decision_id" in result.dropped_fields
        assert "tags" in result.dropped_fields
        assert result.result.summary == "Test narrative"

    def test_downgrade_v2_0_to_v1_0(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, tags=["tag1"], narrative="Narrative text")

        result = self._evolver.downgrade(v2, SCHEMA_V1_0)

        assert result.to_version == SCHEMA_V1_0
        assert result.result.semantic_version == SCHEMA_V1_0
        assert result.result.summary == "Narrative text"
        assert len(result.dropped_fields) >= 2
        assert len(result.mapped_fields) >= 1

    def test_downgrade_same_version_noop(self):
        v1 = _make_v1_semantic()
        result = self._evolver.downgrade(v1, SCHEMA_V1_0)

        assert result.from_version == SCHEMA_V1_0
        assert result.to_version == SCHEMA_V1_0
        assert len(result.dropped_fields) == 0
        assert result.result is v1

    def test_downgrade_no_path_raises(self):
        v1 = _make_v1_semantic()
        with pytest.raises(ValueError, match="No downgrade path"):
            self._evolver.downgrade(v1, SCHEMA_V2_0)


class TestVersionMigrationFullCycle:

    def setup_method(self):
        self._evolver = SchemaEvolver()

    def test_full_cycle_v1_to_v2_and_back(self):
        v1 = _make_v1_semantic()

        v2 = self._evolver.upgrade_to_target(v1, SCHEMA_V2_0)
        v2.decision_id = "d_test123"
        v2.tags = ["test"]
        v2.narrative = v1.summary + " (v2)"

        downgraded = self._evolver.downgrade_to_target(v2, SCHEMA_V1_0)

        assert downgraded.semantic_version == SCHEMA_V1_0
        assert downgraded.symbol == v1.symbol
        assert downgraded.signal.direction == v1.signal.direction
        assert downgraded.confidence_score == v1.confidence_score
        assert downgraded.summary == "基于趋势和流动性因子的看多信号 (v2)"

    def test_deterministic_upgrade_v1_0_to_v1_1(self):
        v1 = _make_v1_semantic()

        results = []
        for _ in range(5):
            r = self._evolver.upgrade(v1, SCHEMA_V1_1)
            results.append(f"{r.result.strategy_id}|{r.result.source_pipeline}")

        for i in range(1, len(results)):
            assert results[i] == results[0]

    def test_deterministic_upgrade_v1_0_to_v2_0(self):
        v1 = _make_v1_semantic()

        results = []
        for _ in range(5):
            v2 = self._evolver.upgrade_to_target(v1, SCHEMA_V2_0)
            results.append(v2.decision_id)

        for i in range(1, len(results)):
            assert results[i] == results[0]

    def test_v1_1_to_v1_0_roundtrip(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(
            v1, strategy_id="s1", source_pipeline="p1"
        )
        v1_0_downgraded = self._evolver.downgrade_to_target(v1_1, SCHEMA_V1_0)

        assert v1_0_downgraded.symbol == v1.symbol
        assert v1_0_downgraded.signal.direction == v1.signal.direction
        assert v1_0_downgraded.confidence_score == v1.confidence_score
        assert v1_0_downgraded.summary == v1.summary

    def test_all_versions_chain(self):
        v1 = _make_v1_semantic()

        v1_1 = self._evolver.upgrade_to_target(
            v1, SCHEMA_V1_1
        )
        v1_1.strategy_id = "strat_chain"

        v2 = self._evolver.upgrade_to_target(
            v1_1, SCHEMA_V2_0
        )
        v2.tags = ["chain_test"]

        v1_1_back = self._evolver.downgrade_to_target(
            v2, SCHEMA_V1_1
        )
        v1_0_back = self._evolver.downgrade_to_target(
            v1_1_back, SCHEMA_V1_0
        )

        assert v1_0_back.symbol == v1.symbol
        assert v1_0_back.semantic_version == SCHEMA_V1_0
        assert v1_1_back.semantic_version == SCHEMA_V1_1
        assert v1_1_back.strategy_id == "strat_chain"

    def test_upgrade_to_v1_1_downgrade_to_v1_0_idempotent(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(v1, strategy_id="s", source_pipeline="p")
        v1_0 = self._evolver.downgrade_to_target(v1_1, SCHEMA_V1_0)

        assert v1_0.symbol == v1.symbol
        assert v1_0.name == v1.name
        assert v1_0.signal.direction == v1.signal.direction
        assert v1_0.confidence_score == v1.confidence_score
        assert v1_0.semantic_version == SCHEMA_V1_0
