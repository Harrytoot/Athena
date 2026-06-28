import pytest

from app.decision_semantics.evolution.version_manager import (
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
)
from app.decision_semantics.runtime.semantic_runtime_engine import (
    SemanticRuntimeEngine,
)
from app.decision_semantics.runtime.state_transition_model import (
    SemanticLifecycleState,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)


def _make_v1_semantic(symbol: str = "AAPL") -> DecisionSemantic:
    return DecisionSemantic(
        symbol=symbol,
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
            entries=[],
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


class TestVersionAwareRuntime:

    def setup_method(self):
        self._engine = SemanticRuntimeEngine()

    def test_supports_all_defined_versions(self):
        assert self._engine.supports_version(SCHEMA_V1_0)
        assert self._engine.supports_version(SCHEMA_V1_1)
        assert self._engine.supports_version(SCHEMA_V2_0)

    def test_initialize_with_v1_0(self):
        semantic = _make_v1_semantic()
        result = self._engine.initialize("AAPL", semantic)

        assert result.is_new
        assert result.snapshot is not None
        assert result.snapshot.semantic.semantic_version == SCHEMA_V1_0
        assert result.snapshot.lifecycle_state == SemanticLifecycleState.ACTIVE

        active = self._engine.get_active("AAPL")
        assert active is not None
        assert active.semantic_version == SCHEMA_V1_0
        assert active.symbol == "AAPL"

    def test_upgrade_from_v1_0_to_v1_1(self):
        semantic = _make_v1_semantic()
        self._engine.initialize("AAPL", semantic)

        result = self._engine.upgrade_version("AAPL", SCHEMA_V1_1)

        assert result.snapshot is not None
        assert result.snapshot.semantic.semantic_version == SCHEMA_V1_1

        active = self._engine.get_active("AAPL")
        assert active.semantic_version == SCHEMA_V1_1
        assert hasattr(active, "strategy_id")

    def test_upgrade_from_v1_0_to_v2_0(self):
        semantic = _make_v1_semantic()
        self._engine.initialize("AAPL", semantic)

        result = self._engine.upgrade_version("AAPL", SCHEMA_V2_0)

        active = self._engine.get_active("AAPL")
        assert active.semantic_version == SCHEMA_V2_0
        assert hasattr(active, "decision_id")
        assert hasattr(active, "tags")
        assert hasattr(active, "narrative")

    def test_upgrade_to_same_version_noop(self):
        semantic = _make_v1_semantic()
        self._engine.initialize("AAPL", semantic)

        result = self._engine.upgrade_version("AAPL", SCHEMA_V1_0)
        assert result.transition is None

        active = self._engine.get_active("AAPL")
        assert active.semantic_version == SCHEMA_V1_0

    def test_multiple_versions_coexist(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_v1_semantic("TSLA")
        self._engine.initialize("TSLA", s2)

        self._engine.upgrade_version("AAPL", SCHEMA_V1_1)
        self._engine.upgrade_version("TSLA", SCHEMA_V2_0)

        active_all = self._engine.get_active_semantics()
        assert active_all["AAPL"].semantic_version == SCHEMA_V1_1
        assert active_all["TSLA"].semantic_version == SCHEMA_V2_0

    def test_get_by_version_retrieves_correct_snapshots(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        self._engine.upgrade_version("AAPL", SCHEMA_V1_1)
        self._engine.upgrade_version("AAPL", SCHEMA_V2_0)

        v1_snapshots = self._engine.get_by_version("AAPL", SCHEMA_V1_0)
        v1_1_snapshots = self._engine.get_by_version("AAPL", SCHEMA_V1_1)
        v2_snapshots = self._engine.get_by_version("AAPL", SCHEMA_V2_0)

        assert len(v1_snapshots) == 1
        assert len(v1_1_snapshots) == 1
        assert len(v2_snapshots) == 1

        assert v1_snapshots[0].semantic_version == SCHEMA_V1_0
        assert v1_1_snapshots[0].semantic_version == SCHEMA_V1_1
        assert v2_snapshots[0].semantic_version == SCHEMA_V2_0

    def test_state_transitions_through_version_chain(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        self._engine.upgrade_version("AAPL", SCHEMA_V1_1)
        self._engine.upgrade_version("AAPL", SCHEMA_V2_0)

        history = self._engine.get_history("AAPL")
        assert history.snapshot_count == 3

        versions = [s.semantic.semantic_version for s in history.snapshots]
        assert versions == [SCHEMA_V1_0, SCHEMA_V1_1, SCHEMA_V2_0]

    def test_transitions_track_version_correctly(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        self._engine.upgrade_version("AAPL", SCHEMA_V2_0)

        transitions = self._engine.get_transitions("AAPL")
        assert len(transitions) >= 3

        versions_in_transitions = [t.semantic_version for t in transitions]
        assert SCHEMA_V1_0 in versions_in_transitions
        assert SCHEMA_V2_0 in versions_in_transitions

    def test_core_data_preserved_across_version_upgrades(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        self._engine.upgrade_version("AAPL", SCHEMA_V2_0)

        active = self._engine.get_active("AAPL")
        assert active.symbol == "AAPL"
        assert active.signal.direction == "LONG"
        assert active.signal.strength == 0.85
        assert active.confidence_score == 0.82
        assert active.action == "APPROVE"
        assert len(active.factors) == 1
        assert active.factors[0].name == "trend"
        assert active.risk.overall_level == "MODERATE"

    def test_update_preserves_version(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_v1_semantic("AAPL")
        s2.semantic_version = SCHEMA_V1_1
        s2.signal.strength = 0.90
        s2.strategy_id = "strat_001"
        s2.source_pipeline = "pipe_001"

        self._engine.update("AAPL", s2)
        active = self._engine.get_active("AAPL")
        assert active.semantic_version == SCHEMA_V1_1
        assert active.signal.strength == 0.90

    def test_archive_and_version_retrieval(self):
        s1 = _make_v1_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        self._engine.upgrade_version("AAPL", SCHEMA_V2_0)
        self._engine.archive("AAPL")

        v1_list = self._engine.get_by_version("AAPL", SCHEMA_V1_0)
        v2_list = self._engine.get_by_version("AAPL", SCHEMA_V2_0)

        assert len(v1_list) == 1
        assert len(v2_list) == 1
