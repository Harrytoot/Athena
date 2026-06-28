import pytest

from app.decision_semantics.runtime.semantic_delta_engine import (
    SemanticDeltaEngine,
)
from app.decision_semantics.runtime.semantic_runtime_engine import (
    SemanticRuntimeEngine,
    RuntimeEventRecord,
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
        ],
        risk=RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.35,
            warnings=[],
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
        action=action,
        action_label="执行买入" if action == "APPROVE" else "等待",
        summary="Test summary",
        semantic_version="1.0.0",
    )


class TestDeterministicReplay:

    def setup_method(self):
        self._engine = SemanticRuntimeEngine()
        self._delta_engine = SemanticDeltaEngine()

    def _build_replay_events(
        self, symbol: str = "AAPL"
    ) -> list[RuntimeEventRecord]:
        s1 = _make_semantic(symbol, "APPROVE")

        events = [
            RuntimeEventRecord(
                event_type=TransitionEvent.ACTIVATE,
                symbol=symbol,
                payload={"semantic": s1},
                sequence_number=1,
            ),
        ]

        s2 = _make_semantic(symbol, "APPROVE")
        s2.confidence_score = 0.90
        s2.risk.overall_level = "LOW"

        events.append(RuntimeEventRecord(
            event_type=TransitionEvent.ACTIVATE,
            symbol=symbol,
            payload={"semantic": s2},
            sequence_number=2,
        ))

        s3 = _make_semantic(symbol, "APPROVE")
        s3.signal.strength = 0.92
        s3.confidence_score = 0.95

        events.append(RuntimeEventRecord(
            event_type=TransitionEvent.ACTIVATE,
            symbol=symbol,
            payload={"semantic": s3},
            sequence_number=3,
        ))

        events.append(RuntimeEventRecord(
            event_type=TransitionEvent.ARCHIVE,
            symbol=symbol,
            sequence_number=4,
        ))

        return events

    def test_replay_produces_identical_results(self):
        events = self._build_replay_events("AAPL")

        results_runs = []
        for run in range(3):
            engine = SemanticRuntimeEngine()
            results = engine.replay_events(events)
            results_runs.append(results)

        for run_idx in range(1, len(results_runs)):
            r1 = results_runs[0]
            r2 = results_runs[run_idx]
            assert set(r1.keys()) == set(r2.keys())

            for symbol in r1:
                assert len(r1[symbol]) == len(r2[symbol])
                for i in range(len(r1[symbol])):
                    res1 = r1[symbol][i]
                    res2 = r2[symbol][i]
                    assert res1.symbol == res2.symbol
                    assert res1.is_new == res2.is_new
                    if res1.snapshot and res2.snapshot:
                        assert res1.snapshot.semantic.action == res2.snapshot.semantic.action
                        assert res1.snapshot.semantic.semantic_version == res2.snapshot.semantic.semantic_version
                        assert res1.snapshot.lifecycle_state == res2.snapshot.lifecycle_state
                    if res1.transition and res2.transition:
                        assert res1.transition.from_state == res2.transition.from_state
                        assert res1.transition.to_state == res2.transition.to_state

    def test_replay_same_event_stream_same_state(self):
        events = self._build_replay_events("TSLA")

        engine1 = SemanticRuntimeEngine()
        engine2 = SemanticRuntimeEngine()

        engine1.replay_events(events)
        engine2.replay_events(events)

        for symbol in ["TSLA"]:
            h1 = engine1.get_history(symbol)
            h2 = engine2.get_history(symbol)

            assert h1.snapshot_count == h2.snapshot_count
            for i in range(h1.snapshot_count):
                s1 = h1.snapshots[i]
                s2 = h2.snapshots[i]
                assert s1.semantic.action == s2.semantic.action
                assert s1.semantic.confidence_score == s2.semantic.confidence_score
                assert s1.lifecycle_state == s2.lifecycle_state
                assert s1.sequence_number == s2.sequence_number

    def test_replay_produces_deterministic_transitions(self):
        events = self._build_replay_events("MSFT")

        transition_histories = []
        for _ in range(3):
            engine = SemanticRuntimeEngine()
            engine.replay_events(events)
            transitions = engine.get_transitions("MSFT")
            transition_histories.append([
                (t.from_state, t.to_state, t.event, t.sequence_number)
                for t in transitions
            ])

        for i in range(1, len(transition_histories)):
            assert transition_histories[i] == transition_histories[0]

    def test_replay_with_delta_updates(self):
        s1 = _make_semantic("DELTA", "APPROVE")

        s2 = _make_semantic("DELTA", "APPROVE")
        s2.confidence_score = 0.88
        delta = self._delta_engine.compute_delta(s1, s2)

        events = [
            RuntimeEventRecord(
                event_type=TransitionEvent.ACTIVATE,
                symbol="DELTA",
                payload={"semantic": s1},
                sequence_number=1,
            ),
            RuntimeEventRecord(
                event_type=TransitionEvent.DELTA_UPDATE,
                symbol="DELTA",
                payload={"delta": delta},
                sequence_number=2,
            ),
        ]

        results_runs = []
        for _ in range(3):
            engine = SemanticRuntimeEngine()
            results = engine.replay_events(events)
            results_runs.append(results)

        for run_idx in range(1, len(results_runs)):
            r1 = results_runs[0]
            r2 = results_runs[run_idx]

            for symbol in r1:
                for i in range(len(r1[symbol])):
                    if r1[symbol][i].snapshot and r2[symbol][i].snapshot:
                        s1_snap = r1[symbol][i].snapshot
                        s2_snap = r2[symbol][i].snapshot
                        assert s1_snap.semantic.confidence_score == s2_snap.semantic.confidence_score

    def test_replay_is_idempotent(self):
        events = self._build_replay_events("NDX")

        engine = SemanticRuntimeEngine()
        first_results = engine.replay_events(events)

        engine.reset()
        second_results = engine.replay_events(events)

        for symbol in first_results:
            assert symbol in second_results
            assert len(first_results[symbol]) == len(second_results[symbol])

    def test_replay_empty_events(self):
        engine = SemanticRuntimeEngine()
        results = engine.replay_events([])
        assert results == {}

    def test_replay_multiple_symbols(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        events = [
            RuntimeEventRecord(
                event_type=TransitionEvent.ACTIVATE,
                symbol="AAPL",
                payload={"semantic": s_aapl},
                sequence_number=1,
            ),
            RuntimeEventRecord(
                event_type=TransitionEvent.ACTIVATE,
                symbol="MSFT",
                payload={"semantic": s_msft},
                sequence_number=2,
            ),
        ]

        run_states = []
        for _ in range(3):
            engine = SemanticRuntimeEngine()
            engine.replay_events(events)
            state = {
                "AAPL": engine.get_active("AAPL").action if engine.get_active("AAPL") else None,
                "MSFT": engine.get_active("MSFT").action if engine.get_active("MSFT") else None,
            }
            run_states.append(state)

        for i in range(1, len(run_states)):
            assert run_states[i] == run_states[0]
