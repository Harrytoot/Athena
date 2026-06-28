import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.schema import DecisionSemantic


@dataclass
class CoordinatorEvent:
    symbol: str
    event_type: str
    semantic: DecisionSemantic | None = None
    conflict_targets: list[str] = field(default_factory=list)
    global_sequence_number: int = 0
    event_id: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        if not self.event_id:
            self.event_id = self._compute_id()

    def _compute_id(self) -> str:
        raw = json.dumps({
            "symbol": self.symbol,
            "event_type": self.event_type,
            "global_sequence_number": self.global_sequence_number,
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class CoordinatorState:
    active_semantics: dict[str, DecisionSemantic] = field(default_factory=dict)
    pending_updates: dict[str, list[DecisionSemantic]] = field(default_factory=dict)
    resolved_conflicts: list[dict] = field(default_factory=list)
    event_log: list[CoordinatorEvent] = field(default_factory=list)
    sequence_number: int = 0


class StreamingStateCoordinator:

    def __init__(self):
        self._state: dict[str, CoordinatorState] = {}
        self._global_sequence: int = 0
        self._event_log: list[CoordinatorEvent] = []

    def begin_update(
        self, symbol: str, semantic: DecisionSemantic
    ) -> CoordinatorEvent:
        self._global_sequence += 1

        event = CoordinatorEvent(
            symbol=symbol,
            event_type="begin_update",
            semantic=semantic,
            global_sequence_number=self._global_sequence,
        )
        self._event_log.append(event)

        self._ensure_state(symbol)
        st = self._state[symbol]

        if symbol not in st.pending_updates:
            st.pending_updates[symbol] = []
        st.pending_updates[symbol].append(semantic)

        return event

    def commit_updates(self) -> dict[str, DecisionSemantic]:
        result: dict[str, DecisionSemantic] = {}

        for symbol, st in self._state.items():
            pending = st.pending_updates.pop(symbol, [])
            if pending:
                latest = pending[-1]
                st.active_semantics[symbol] = latest
                result[symbol] = latest

        return result

    def resolve_conflicts(
        self, symbol_a: str, symbol_b: str, correlation: float
    ) -> dict:
        sem_a = self.get_active(symbol_a)
        sem_b = self.get_active(symbol_b)

        if sem_a is None or sem_b is None:
            return {"status": "no_conflict", "reason": "missing_semantics"}

        if sem_a.action == "HOLD" or sem_b.action == "HOLD":
            return {"status": "no_conflict", "reason": "hold_action"}

        if correlation > 0 and sem_a.action != sem_b.action:
            self._global_sequence += 1
            event = CoordinatorEvent(
                symbol=f"{symbol_a}::{symbol_b}",
                event_type="conflict_resolved",
                conflict_targets=[symbol_a, symbol_b],
                global_sequence_number=self._global_sequence,
            )
            self._event_log.append(event)

            return {
                "status": "conflict_detected",
                "symbol_a": symbol_a,
                "symbol_b": symbol_b,
                "action_a": sem_a.action,
                "action_b": sem_b.action,
                "correlation": correlation,
                "resolution": "flag_for_review",
            }

        if correlation < 0 and sem_a.action == sem_b.action:
            return {
                "status": "conflict_detected",
                "symbol_a": symbol_a,
                "symbol_b": symbol_b,
                "action_a": sem_a.action,
                "action_b": sem_b.action,
                "correlation": correlation,
                "resolution": "flag_for_review",
            }

        return {"status": "no_conflict", "reason": "actions_aligned"}

    def get_active(self, symbol: str) -> DecisionSemantic | None:
        st = self._state.get(symbol)
        if st is None:
            return None
        return st.active_semantics.get(symbol)

    def set_active(self, symbol: str, semantic: DecisionSemantic) -> None:
        self._ensure_state(symbol)
        st = self._state[symbol]
        st.active_semantics[symbol] = semantic

        self._global_sequence += 1
        event = CoordinatorEvent(
            symbol=symbol,
            event_type="set_active",
            semantic=semantic,
            global_sequence_number=self._global_sequence,
        )
        self._event_log.append(event)

    def get_all_active(self) -> dict[str, DecisionSemantic]:
        result: dict[str, DecisionSemantic] = {}
        for symbol, st in self._state.items():
            active = st.active_semantics.get(symbol)
            if active is not None:
                result[symbol] = active
        return result

    def get_pending(self, symbol: str) -> list[DecisionSemantic]:
        st = self._state.get(symbol)
        if st is None:
            return []
        return st.pending_updates.get(symbol, [])

    def has_pending(self) -> bool:
        for st in self._state.values():
            for updates in st.pending_updates.values():
                if updates:
                    return True
        return False

    def pending_count(self) -> int:
        total = 0
        for st in self._state.values():
            for updates in st.pending_updates.values():
                total += len(updates)
        return total

    def ensure_deterministic_ordering(self) -> list[str]:
        ordering: list[str] = []

        for symbol in sorted(self._state.keys()):
            pending = self._state[symbol].pending_updates.get(symbol, [])
            if pending:
                ordering.append(f"{symbol}_{len(pending)}")

        return ordering

    def get_event_log(self) -> list[CoordinatorEvent]:
        return list(self._event_log)

    def get_sequence(self) -> int:
        return self._global_sequence

    def reset(self) -> None:
        self._state.clear()
        self._global_sequence = 0
        self._event_log.clear()

    def _ensure_state(self, symbol: str) -> None:
        if symbol not in self._state:
            self._state[symbol] = CoordinatorState()
