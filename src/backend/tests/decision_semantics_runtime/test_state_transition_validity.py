import pytest

from app.decision_semantics.runtime.state_transition_model import (
    StateTransitionModel,
    StateTransition,
    SemanticLifecycleState,
    TransitionEvent,
)


class TestStateTransitionValidity:

    def setup_method(self):
        self._model = StateTransitionModel()

    def test_valid_initialized_to_active(self):
        assert self._model.validate_transition(
            SemanticLifecycleState.INITIALIZED,
            SemanticLifecycleState.ACTIVE,
        )

    def test_valid_initialized_to_archived(self):
        assert self._model.validate_transition(
            SemanticLifecycleState.INITIALIZED,
            SemanticLifecycleState.ARCHIVED,
        )

    def test_valid_active_to_superseded(self):
        assert self._model.validate_transition(
            SemanticLifecycleState.ACTIVE,
            SemanticLifecycleState.SUPERSEDED,
        )

    def test_valid_active_to_archived(self):
        assert self._model.validate_transition(
            SemanticLifecycleState.ACTIVE,
            SemanticLifecycleState.ARCHIVED,
        )

    def test_valid_superseded_to_archived(self):
        assert self._model.validate_transition(
            SemanticLifecycleState.SUPERSEDED,
            SemanticLifecycleState.ARCHIVED,
        )

    def test_invalid_archived_to_active(self):
        assert not self._model.validate_transition(
            SemanticLifecycleState.ARCHIVED,
            SemanticLifecycleState.ACTIVE,
        )

    def test_invalid_archived_to_superseded(self):
        assert not self._model.validate_transition(
            SemanticLifecycleState.ARCHIVED,
            SemanticLifecycleState.SUPERSEDED,
        )

    def test_invalid_archived_to_initialized(self):
        assert not self._model.validate_transition(
            SemanticLifecycleState.ARCHIVED,
            SemanticLifecycleState.INITIALIZED,
        )

    def test_invalid_active_to_initialized(self):
        assert not self._model.validate_transition(
            SemanticLifecycleState.ACTIVE,
            SemanticLifecycleState.INITIALIZED,
        )

    def test_valid_superseded_to_active(self):
        assert self._model.validate_transition(
            SemanticLifecycleState.SUPERSEDED,
            SemanticLifecycleState.ACTIVE,
        )

    def test_invalid_superseded_to_initialized(self):
        assert not self._model.validate_transition(
            SemanticLifecycleState.SUPERSEDED,
            SemanticLifecycleState.INITIALIZED,
        )

    def test_record_valid_transition(self):
        transition = self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        assert isinstance(transition, StateTransition)
        assert transition.from_state == SemanticLifecycleState.INITIALIZED
        assert transition.to_state == SemanticLifecycleState.ACTIVE
        assert transition.symbol == "AAPL"
        assert transition.semantic_version == "1.0.0"
        assert transition.sequence_number == 1
        assert len(transition.transition_id) == 16

    def test_record_invalid_transition_raises(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ARCHIVED,
            event=TransitionEvent.ARCHIVE,
            semantic_version="1.0.0",
        )

        with pytest.raises(ValueError, match="Invalid transition"):
            self._model.record_transition(
                symbol="AAPL",
                to_state=SemanticLifecycleState.ACTIVE,
                event=TransitionEvent.ACTIVATE,
                semantic_version="1.0.0",
            )

    def test_get_current_state(self):
        assert self._model.get_current_state("AAPL") is None

        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        assert self._model.get_current_state("AAPL") == SemanticLifecycleState.ACTIVE

    def test_get_transition_history(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.SUPERSEDED,
            event=TransitionEvent.SUPERSEDE,
            semantic_version="1.0.0",
        )

        history = self._model.get_transition_history("AAPL")
        assert len(history) == 2
        assert history[0].to_state == SemanticLifecycleState.ACTIVE
        assert history[1].to_state == SemanticLifecycleState.SUPERSEDED

    def test_get_transitions_by_event(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.SUPERSEDED,
            event=TransitionEvent.DELTA_UPDATE,
            semantic_version="1.0.0",
        )

        activations = self._model.get_transitions_by_event(
            "AAPL", TransitionEvent.ACTIVATE
        )
        assert len(activations) == 1
        assert activations[0].event == TransitionEvent.ACTIVATE

    def test_sequence_counter_increments(self):
        assert self._model.get_sequence_counter("AAPL") == 0

        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )
        assert self._model.get_sequence_counter("AAPL") == 1

        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.SUPERSEDED,
            event=TransitionEvent.SUPERSEDE,
            semantic_version="1.0.0",
        )
        assert self._model.get_sequence_counter("AAPL") == 2

    def test_isolation_between_symbols(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        self._model.record_transition(
            symbol="TSLA",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        assert self._model.get_current_state("AAPL") == SemanticLifecycleState.ACTIVE
        assert self._model.get_current_state("TSLA") == SemanticLifecycleState.ACTIVE
        assert self._model.get_sequence_counter("AAPL") == 1
        assert self._model.get_sequence_counter("TSLA") == 1

    def test_get_all_active_symbols(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        self._model.record_transition(
            symbol="MSFT",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        active = self._model.get_all_active_symbols()
        assert "AAPL" in active
        assert "MSFT" in active
        assert len(active) == 2

    def test_deterministic_transition_id(self):
        transitions = []
        for _ in range(5):
            model = StateTransitionModel()
            t = model.record_transition(
                symbol="AAPL",
                to_state=SemanticLifecycleState.ACTIVE,
                event=TransitionEvent.ACTIVATE,
                semantic_version="1.0.0",
            )
            transitions.append(t.transition_id)

        for i in range(1, len(transitions)):
            assert transitions[i] == transitions[0]

    def test_valid_transitions_property(self):
        valid = self._model.valid_transitions
        assert "initialized" in valid
        assert "active" in valid["initialized"]
        assert "archived" in valid["initialized"]
        assert "superseded" in valid["active"]
        assert "archived" in valid["active"]

    def test_reset_symbol(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
        )

        self._model.reset_symbol("AAPL")
        assert self._model.get_current_state("AAPL") is None
        assert len(self._model.get_transition_history("AAPL")) == 0
        assert self._model.get_sequence_counter("AAPL") == 0

    def test_metadata_preserved(self):
        self._model.record_transition(
            symbol="AAPL",
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version="1.0.0",
            metadata={"pipeline": "prod_v1", "strategy": "momentum"},
        )

        history = self._model.get_transition_history("AAPL")
        assert history[0].metadata == {"pipeline": "prod_v1", "strategy": "momentum"}
