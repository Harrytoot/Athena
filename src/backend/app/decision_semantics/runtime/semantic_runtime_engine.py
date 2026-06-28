import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.evolution.schema_evolver import SchemaEvolver
from app.decision_semantics.evolution.version_manager import (
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
    ALL_SUPPORTED_VERSIONS,
)
from app.decision_semantics.runtime.semantic_delta_engine import (
    SemanticDelta,
    SemanticDeltaEngine,
)
from app.decision_semantics.runtime.semantic_state_store import (
    SemanticStateSnapshot,
    SemanticStateStore,
    SymbolStateHistory,
)
from app.decision_semantics.runtime.state_transition_model import (
    SemanticLifecycleState,
    StateTransition,
    StateTransitionModel,
    TransitionEvent,
)
from app.decision_semantics.schema import DecisionSemantic


@dataclass
class RuntimeEventRecord:
    event_type: TransitionEvent
    symbol: str
    payload: dict = field(default_factory=dict)
    event_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = ""
    sequence_number: int = 0

    def __post_init__(self):
        if not self.event_id:
            self.event_id = self._compute_id()

    def _compute_id(self) -> str:
        raw = json.dumps({
            "event_type": self.event_type.value,
            "symbol": self.symbol,
            "sequence_number": self.sequence_number,
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class RuntimeUpdateResult:
    symbol: str
    is_new: bool
    delta: SemanticDelta | None
    snapshot: SemanticStateSnapshot | None
    transition: StateTransition | None


class SemanticRuntimeEngine:

    def __init__(self):
        self._state_store = SemanticStateStore()
        self._transition_model = StateTransitionModel()
        self._delta_engine = SemanticDeltaEngine()
        self._schema_evolver = SchemaEvolver()
        self._event_log: list[RuntimeEventRecord] = []
        self._event_counter: dict[str, int] = {}
        self._active_versions: set[str] = set(ALL_SUPPORTED_VERSIONS)

    def initialize(self, symbol: str, semantic: DecisionSemantic) -> RuntimeUpdateResult:
        snapshot = self._state_store.put(symbol, semantic)
        snapshot.lifecycle_state = SemanticLifecycleState.ACTIVE

        history = self._state_store.get_history(symbol)
        history.active_snapshot_index = len(history.snapshots) - 1

        transition = self._transition_model.record_transition(
            symbol=symbol,
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version=semantic.semantic_version,
        )

        self._record_event(
            event_type=TransitionEvent.ACTIVATE,
            symbol=symbol,
            payload={"semantic_version": semantic.semantic_version},
        )

        return RuntimeUpdateResult(
            symbol=symbol,
            is_new=True,
            delta=None,
            snapshot=snapshot,
            transition=transition,
        )

    def update(self, symbol: str, new_semantic: DecisionSemantic) -> RuntimeUpdateResult:
        old_active = self._state_store.get_active(symbol)

        delta = None
        if old_active is not None:
            old_semantic = old_active.semantic
            delta = self._delta_engine.compute_delta(old_semantic, new_semantic)

        self._state_store.supersede(symbol)
        self._transition_model.record_transition(
            symbol=symbol,
            to_state=SemanticLifecycleState.SUPERSEDED,
            event=TransitionEvent.SUPERSEDE,
            semantic_version=old_active.semantic.semantic_version if old_active else SCHEMA_V1_0,
        )

        snapshot = self._state_store.put(symbol, new_semantic)
        snapshot.lifecycle_state = SemanticLifecycleState.ACTIVE
        history = self._state_store.get_history(symbol)
        history.active_snapshot_index = len(history.snapshots) - 1

        transition = self._transition_model.record_transition(
            symbol=symbol,
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.ACTIVATE,
            semantic_version=new_semantic.semantic_version,
        )

        self._record_event(
            event_type=TransitionEvent.ACTIVATE,
            symbol=symbol,
            payload={
                "semantic_version": new_semantic.semantic_version,
                "has_delta": delta is not None and not delta.is_empty,
            },
        )

        return RuntimeUpdateResult(
            symbol=symbol,
            is_new=(old_active is None),
            delta=delta,
            snapshot=snapshot,
            transition=transition,
        )

    def apply_delta(self, symbol: str, delta: SemanticDelta) -> RuntimeUpdateResult:
        active = self._state_store.get_active(symbol)
        if active is None:
            raise ValueError(f"No active semantic for symbol {symbol}")

        if not self._delta_engine.is_delta_applicable(active.semantic, delta):
            raise ValueError(f"Delta not applicable to current state for {symbol}")

        new_semantic = self._delta_engine.apply_delta(active.semantic, delta)

        self._state_store.supersede(symbol)
        self._transition_model.record_transition(
            symbol=symbol,
            to_state=SemanticLifecycleState.SUPERSEDED,
            event=TransitionEvent.DELTA_UPDATE,
            semantic_version=active.semantic.semantic_version,
        )

        snapshot = self._state_store.put(symbol, new_semantic)
        snapshot.lifecycle_state = SemanticLifecycleState.ACTIVE
        history = self._state_store.get_history(symbol)
        history.active_snapshot_index = len(history.snapshots) - 1

        transition = self._transition_model.record_transition(
            symbol=symbol,
            to_state=SemanticLifecycleState.ACTIVE,
            event=TransitionEvent.DELTA_UPDATE,
            semantic_version=new_semantic.semantic_version,
        )

        self._record_event(
            event_type=TransitionEvent.DELTA_UPDATE,
            symbol=symbol,
            payload={
                "delta_id": delta.delta_id,
                "change_count": delta.change_count,
            },
        )

        return RuntimeUpdateResult(
            symbol=symbol,
            is_new=False,
            delta=delta,
            snapshot=snapshot,
            transition=transition,
        )

    def get_active(self, symbol: str) -> DecisionSemantic | None:
        snapshot = self._state_store.get_active(symbol)
        if snapshot is None:
            return None
        return snapshot.semantic

    def get_state(self, symbol: str) -> SemanticLifecycleState | None:
        return self._transition_model.get_current_state(symbol)

    def get_history(self, symbol: str) -> SymbolStateHistory:
        return self._state_store.get_history(symbol)

    def get_transitions(self, symbol: str) -> list[StateTransition]:
        return self._transition_model.get_transition_history(symbol)

    def get_active_semantics(self) -> dict[str, DecisionSemantic]:
        return self._state_store.get_active_semantics()

    def archive(self, symbol: str) -> RuntimeUpdateResult:
        active = self._state_store.get_active(symbol)
        self._state_store.archive(symbol)

        transition = self._transition_model.record_transition(
            symbol=symbol,
            to_state=SemanticLifecycleState.ARCHIVED,
            event=TransitionEvent.ARCHIVE,
            semantic_version=active.semantic.semantic_version if active else SCHEMA_V1_0,
        )

        self._record_event(
            event_type=TransitionEvent.ARCHIVE,
            symbol=symbol,
        )

        return RuntimeUpdateResult(
            symbol=symbol,
            is_new=False,
            delta=None,
            snapshot=active,
            transition=transition,
        )

    def supports_version(self, version: str) -> bool:
        return version in self._active_versions

    def upgrade_version(self, symbol: str, target_version: str) -> RuntimeUpdateResult:
        active = self._state_store.get_active(symbol)
        if active is None:
            raise ValueError(f"No active semantic for symbol {symbol}")

        current_version = active.semantic.semantic_version
        if current_version == target_version:
            delta = SemanticDelta(
                from_snapshot_id=active.snapshot_id,
                to_snapshot_id=active.snapshot_id,
                symbol=symbol,
                changes=[],
            )
            return RuntimeUpdateResult(
                symbol=symbol,
                is_new=False,
                delta=delta,
                snapshot=active,
                transition=None,
            )

        upgraded = self._schema_evolver.upgrade_to_target(active.semantic, target_version)
        return self.update(symbol, upgraded)

    def get_by_version(self, symbol: str, version: str) -> list[DecisionSemantic]:
        snapshots = self._state_store.get_by_version(symbol, version)
        return [s.semantic for s in snapshots]

    def replay_events(
        self, events: list[RuntimeEventRecord]
    ) -> dict[str, list[RuntimeUpdateResult]]:
        original_engine_state = self._capture_state()

        self._state_store.reset()
        self._transition_model = StateTransitionModel()
        self._event_log.clear()
        self._event_counter.clear()

        results: dict[str, list[RuntimeUpdateResult]] = {}

        try:
            for event in events:
                result = self._dispatch_event(event)
                results.setdefault(event.symbol, []).append(result)
        finally:
            pass

        return results

    def get_event_log(self) -> list[RuntimeEventRecord]:
        return list(self._event_log)

    def reset(self) -> None:
        self._state_store.reset()
        self._transition_model = StateTransitionModel()
        self._event_log.clear()
        self._event_counter.clear()

    def _capture_state(self) -> dict:
        return {
            "active_semantics": {
                sym: self._state_store.get_active(sym).semantic
                if self._state_store.get_active(sym)
                else None
                for sym in self._state_store.get_all_symbols()
            },
        }

    def _dispatch_event(self, event: RuntimeEventRecord) -> RuntimeUpdateResult:
        if event.event_type == TransitionEvent.ACTIVATE:
            semantic_data = event.payload.get("semantic")
            if semantic_data is None:
                raise ValueError("ACTIVATE event requires 'semantic' in payload")
            if self._state_store.get_active(event.symbol) is not None:
                return self.update(event.symbol, semantic_data)
            return self.initialize(event.symbol, semantic_data)

        elif event.event_type == TransitionEvent.DELTA_UPDATE:
            delta = event.payload.get("delta")
            if delta is None:
                raise ValueError("DELTA_UPDATE event requires 'delta' in payload")
            return self.apply_delta(event.symbol, delta)

        elif event.event_type == TransitionEvent.FEATURE_UPDATE:
            delta = event.payload.get("delta")
            if delta is None:
                raise ValueError("FEATURE_UPDATE event requires 'delta' in payload")
            return self.apply_delta(event.symbol, delta)

        elif event.event_type == TransitionEvent.RISK_RECALIBRATE:
            delta = event.payload.get("delta")
            if delta is None:
                raise ValueError("RISK_RECALIBRATE event requires 'delta' in payload")
            return self.apply_delta(event.symbol, delta)

        elif event.event_type == TransitionEvent.MARKET_TICK:
            delta = event.payload.get("delta")
            if delta is None:
                raise ValueError("MARKET_TICK event requires 'delta' in payload")
            return self.apply_delta(event.symbol, delta)

        elif event.event_type == TransitionEvent.ARCHIVE:
            return self.archive(event.symbol)

        else:
            raise ValueError(f"Unknown event type: {event.event_type}")

    def _record_event(
        self,
        event_type: TransitionEvent,
        symbol: str,
        payload: dict | None = None,
    ) -> RuntimeEventRecord:
        self._event_counter.setdefault(event_type.value, 0)
        self._event_counter[event_type.value] += 1
        seq = self._event_counter[event_type.value]

        record = RuntimeEventRecord(
            event_type=event_type,
            symbol=symbol,
            payload=payload or {},
            sequence_number=seq,
        )
        self._event_log.append(record)
        return record
