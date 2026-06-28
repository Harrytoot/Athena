import pytest

from app.decision_semantics.runtime.semantic_delta_engine import (
    SemanticDeltaEngine,
)
from app.decision_semantics.runtime.semantic_runtime_engine import (
    SemanticRuntimeEngine,
)
from app.decision_semantics.runtime.state_transition_model import (
    SemanticLifecycleState,
    TransitionEvent,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)


def _make_semantic(symbol: str = "AAPL", action: str = "APPROVE") -> DecisionSemantic:
    return DecisionSemantic(
        symbol=symbol,
        name="Test Stock",
        signal=SignalSemantic(
            direction="LONG" if action == "APPROVE" else "NEUTRAL",
            direction_label="看多" if action == "APPROVE" else "中性",
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
            entries=[{"name": "crash", "impact": "medium"}],
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action=action,
        action_label="执行买入" if action == "APPROVE" else "等待",
        summary="Test summary",
        semantic_version="1.0.0",
    )


class TestSemanticStateEvolution:

    def setup_method(self):
        self._engine = SemanticRuntimeEngine()
        self._delta_engine = SemanticDeltaEngine()

    def test_initialization_creates_active_state(self):
        s1 = _make_semantic("AAPL")
        result = self._engine.initialize("AAPL", s1)

        assert result.snapshot.lifecycle_state == SemanticLifecycleState.ACTIVE
        assert result.transition.from_state == SemanticLifecycleState.INITIALIZED
        assert result.transition.to_state == SemanticLifecycleState.ACTIVE
        assert self._engine.get_state("AAPL") == SemanticLifecycleState.ACTIVE

    def test_update_supersedes_previous_state(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.90
        result = self._engine.update("AAPL", s2)

        transitions = self._engine.get_transitions("AAPL")
        states_seen = [(t.from_state, t.to_state) for t in transitions]

        assert (SemanticLifecycleState.INITIALIZED, SemanticLifecycleState.ACTIVE) in states_seen
        assert (SemanticLifecycleState.ACTIVE, SemanticLifecycleState.SUPERSEDED) in states_seen

        assert result.snapshot.lifecycle_state == SemanticLifecycleState.ACTIVE
        assert self._engine.get_state("AAPL") == SemanticLifecycleState.ACTIVE

    def test_delta_update_evolves_state(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.signal.strength = 0.90
        s2.confidence_score = 0.88
        delta = self._delta_engine.compute_delta(s1, s2)

        result = self._engine.apply_delta("AAPL", delta)

        active = self._engine.get_active("AAPL")
        assert active.signal.strength == 0.90
        assert active.confidence_score == 0.88

        assert result.transition.event == TransitionEvent.DELTA_UPDATE

    def test_state_evolution_chain_initialized_active_superseded_archived(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.90
        self._engine.update("AAPL", s2)

        s3 = _make_semantic("AAPL")
        s3.confidence_score = 0.95
        self._engine.update("AAPL", s3)

        self._engine.archive("AAPL")

        history = self._engine.get_history("AAPL")
        assert history.snapshot_count == 3

        lifecycle_states = [s.lifecycle_state for s in history.snapshots]
        assert lifecycle_states == [
            SemanticLifecycleState.SUPERSEDED,
            SemanticLifecycleState.SUPERSEDED,
            SemanticLifecycleState.ARCHIVED,
        ]

        assert self._engine.get_state("AAPL") == SemanticLifecycleState.ARCHIVED

    def test_active_semantic_is_latest(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.85
        self._engine.update("AAPL", s2)

        s3 = _make_semantic("AAPL")
        s3.confidence_score = 0.90
        self._engine.update("AAPL", s3)

        active = self._engine.get_active("AAPL")
        assert active.confidence_score == 0.90

    def test_multiple_symbols_independent_evolution(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("TSLA")
        self._engine.initialize("TSLA", s2)

        s1_updated = _make_semantic("AAPL")
        s1_updated.confidence_score = 0.90
        self._engine.update("AAPL", s1_updated)

        s2_updated = _make_semantic("TSLA")
        s2_updated.confidence_score = 0.70
        self._engine.update("TSLA", s2_updated)

        active = self._engine.get_active_semantics()
        assert active["AAPL"].confidence_score == 0.90
        assert active["TSLA"].confidence_score == 0.70

    def test_get_active_returns_none_for_unknown_symbol(self):
        assert self._engine.get_active("UNKNOWN") is None

    def test_apply_delta_on_nonexistent_symbol_raises(self):
        s1 = _make_semantic("AAPL")
        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.90
        delta = self._delta_engine.compute_delta(s1, s2)

        with pytest.raises(ValueError, match="No active semantic"):
            self._engine.apply_delta("UNKNOWN", delta)

    def test_event_log_records_operations(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.90
        self._engine.update("AAPL", s2)

        self._engine.archive("AAPL")

        event_log = self._engine.get_event_log()
        assert len(event_log) >= 3

        event_types = [e.event_type for e in event_log]
        assert TransitionEvent.ACTIVATE in event_types
        assert TransitionEvent.ARCHIVE in event_types

    def test_reset_clears_all_state(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        self._engine.reset()

        assert self._engine.get_active("AAPL") is None
        assert self._engine.get_state("AAPL") is None
        assert self._engine.get_history("AAPL").snapshot_count == 0

    def test_history_preserves_full_evolution(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.85
        self._engine.update("AAPL", s2)

        s3 = _make_semantic("AAPL")
        s3.confidence_score = 0.90
        self._engine.update("AAPL", s3)

        history = self._engine.get_history("AAPL")
        assert history.snapshot_count == 3

        confidences = [s.semantic.confidence_score for s in history.snapshots]
        assert confidences == [0.82, 0.85, 0.90]

    def test_delta_captures_only_changed_features(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.factors[0].value = 75.0
        result = self._engine.update("AAPL", s2)

        assert result.delta is not None
        changed = result.delta.changed_field_paths()
        assert "factors.0.value" in changed

        unchanged_should_not_appear = [
            "symbol", "name", "factors.0.name", "risk.overall_level"
        ]
        for path in unchanged_should_not_appear:
            assert path not in changed

    def test_sequence_numbers_monotonic(self):
        s1 = _make_semantic("AAPL")
        self._engine.initialize("AAPL", s1)

        s2 = _make_semantic("AAPL")
        s2.confidence_score = 0.85
        self._engine.update("AAPL", s2)

        s3 = _make_semantic("AAPL")
        s3.confidence_score = 0.90
        self._engine.update("AAPL", s3)

        history = self._engine.get_history("AAPL")
        seqs = [s.sequence_number for s in history.snapshots]
        assert seqs == [1, 2, 3]

    def test_state_evolution_is_deterministic(self):
        def run_evolution():
            engine = SemanticRuntimeEngine()

            s1 = _make_semantic("AAPL")
            engine.initialize("AAPL", s1)

            s2 = _make_semantic("AAPL")
            s2.confidence_score = 0.90
            engine.update("AAPL", s2)

            s3 = _make_semantic("AAPL")
            s3.confidence_score = 0.95
            s3.signal.strength = 0.92
            engine.update("AAPL", s3)

            engine.archive("AAPL")

            active = engine.get_active("AAPL")
            state = engine.get_state("AAPL")
            history = engine.get_history("AAPL")

            return {
                "active_action": active.action if active else None,
                "active_confidence": active.confidence_score if active else None,
                "state": state,
                "snapshot_count": history.snapshot_count,
            }

        results = [run_evolution() for _ in range(5)]

        for i in range(1, len(results)):
            assert results[i] == results[0]
