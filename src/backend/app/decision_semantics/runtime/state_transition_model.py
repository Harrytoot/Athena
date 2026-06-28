import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SemanticLifecycleState(Enum):
    INITIALIZED = "initialized"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class TransitionEvent(Enum):
    ACTIVATE = "activate"
    SUPERSEDE = "supersede"
    ARCHIVE = "archive"
    REJECT = "reject"
    DELTA_UPDATE = "delta_update"
    FEATURE_UPDATE = "feature_update"
    RISK_RECALIBRATE = "risk_recalibrate"
    MARKET_TICK = "market_tick"


_VALID_TRANSITIONS: dict[SemanticLifecycleState, set[SemanticLifecycleState]] = {
    SemanticLifecycleState.INITIALIZED: {
        SemanticLifecycleState.ACTIVE,
        SemanticLifecycleState.ARCHIVED,
    },
    SemanticLifecycleState.ACTIVE: {
        SemanticLifecycleState.SUPERSEDED,
        SemanticLifecycleState.ARCHIVED,
    },
    SemanticLifecycleState.SUPERSEDED: {
        SemanticLifecycleState.ACTIVE,
        SemanticLifecycleState.ARCHIVED,
    },
    SemanticLifecycleState.ARCHIVED: set(),
}


@dataclass
class StateTransition:
    from_state: SemanticLifecycleState
    to_state: SemanticLifecycleState
    event: TransitionEvent
    symbol: str
    semantic_version: str
    sequence_number: int
    transition_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    transition_id: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.transition_id:
            self.transition_id = self._compute_id()

    def _compute_id(self) -> str:
        payload = {
            "symbol": self.symbol,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "event": self.event.value,
            "semantic_version": self.semantic_version,
            "sequence_number": self.sequence_number,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class StateTransitionModel:

    def __init__(self):
        self._transitions: dict[str, list[StateTransition]] = {}
        self._current_states: dict[str, SemanticLifecycleState] = {}
        self._sequence_counters: dict[str, int] = {}

    def validate_transition(
        self,
        from_state: SemanticLifecycleState,
        to_state: SemanticLifecycleState,
    ) -> bool:
        valid_targets = _VALID_TRANSITIONS.get(from_state, set())
        return to_state in valid_targets

    def record_transition(
        self,
        symbol: str,
        to_state: SemanticLifecycleState,
        event: TransitionEvent,
        semantic_version: str,
        metadata: dict | None = None,
    ) -> StateTransition:
        from_state = self._current_states.get(symbol, SemanticLifecycleState.INITIALIZED)

        if not self.validate_transition(from_state, to_state):
            raise ValueError(
                f"Invalid transition for {symbol}: "
                f"{from_state.value} -> {to_state.value}"
            )

        self._sequence_counters.setdefault(symbol, 0)
        self._sequence_counters[symbol] += 1
        seq = self._sequence_counters[symbol]

        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            event=event,
            symbol=symbol,
            semantic_version=semantic_version,
            sequence_number=seq,
            metadata=metadata or {},
        )

        self._transitions.setdefault(symbol, []).append(transition)
        self._current_states[symbol] = to_state

        return transition

    def get_current_state(self, symbol: str) -> SemanticLifecycleState | None:
        return self._current_states.get(symbol)

    def get_transition_history(self, symbol: str) -> list[StateTransition]:
        return list(self._transitions.get(symbol, []))

    def get_transitions_by_event(
        self, symbol: str, event: TransitionEvent
    ) -> list[StateTransition]:
        return [
            t for t in self.get_transition_history(symbol) if t.event == event
        ]

    def get_sequence_counter(self, symbol: str) -> int:
        return self._sequence_counters.get(symbol, 0)

    def reset_symbol(self, symbol: str) -> None:
        self._transitions.pop(symbol, None)
        self._current_states.pop(symbol, None)
        self._sequence_counters.pop(symbol, None)

    def get_all_active_symbols(self) -> list[str]:
        return [
            sym
            for sym, state in self._current_states.items()
            if state == SemanticLifecycleState.ACTIVE
        ]

    @property
    def valid_transitions(self) -> dict[str, list[str]]:
        return {
            k.value: [v.value for v in targets]
            for k, targets in _VALID_TRANSITIONS.items()
        }
