import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.runtime.state_transition_model import (
    SemanticLifecycleState,
)
from app.decision_semantics.schema import DecisionSemantic


@dataclass
class SemanticStateSnapshot:
    semantic: DecisionSemantic
    lifecycle_state: SemanticLifecycleState
    sequence_number: int
    snapshot_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    snapshot_id: str = ""
    parent_snapshot_id: str | None = None

    def __post_init__(self):
        if not self.snapshot_id:
            self.snapshot_id = self._compute_id()

    def _compute_id(self) -> str:
        payload = {
            "symbol": self.semantic.symbol,
            "semantic_version": self.semantic.semantic_version,
            "sequence_number": self.sequence_number,
            "lifecycle_state": self.lifecycle_state.value,
            "action": self.semantic.action,
            "confidence_score": self.semantic.confidence_score,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class SymbolStateHistory:
    symbol: str
    snapshots: list[SemanticStateSnapshot] = field(default_factory=list)
    active_snapshot_index: int = -1

    @property
    def active_snapshot(self) -> SemanticStateSnapshot | None:
        if 0 <= self.active_snapshot_index < len(self.snapshots):
            return self.snapshots[self.active_snapshot_index]
        return None

    @property
    def latest_snapshot(self) -> SemanticStateSnapshot | None:
        if self.snapshots:
            return self.snapshots[-1]
        return None

    @property
    def snapshot_count(self) -> int:
        return len(self.snapshots)


class SemanticStateStore:

    def __init__(self):
        self._histories: dict[str, SymbolStateHistory] = {}
        self._sequence_counters: dict[str, int] = {}

    def put(self, symbol: str, semantic: DecisionSemantic) -> SemanticStateSnapshot:
        self._sequence_counters.setdefault(symbol, 0)
        self._sequence_counters[symbol] += 1
        seq = self._sequence_counters[symbol]

        history = self._histories.setdefault(symbol, SymbolStateHistory(symbol=symbol))

        parent_id = None
        if history.active_snapshot:
            parent_id = history.active_snapshot.snapshot_id

        snapshot = SemanticStateSnapshot(
            semantic=deepcopy(semantic),
            lifecycle_state=SemanticLifecycleState.INITIALIZED,
            sequence_number=seq,
            parent_snapshot_id=parent_id,
        )

        history.snapshots.append(snapshot)
        return snapshot

    def activate(self, symbol: str) -> SemanticStateSnapshot | None:
        history = self._histories.get(symbol)
        if history is None:
            return None

        latest = history.latest_snapshot
        if latest is None:
            return None

        latest.lifecycle_state = SemanticLifecycleState.ACTIVE
        history.active_snapshot_index = len(history.snapshots) - 1
        return latest

    def supersede(self, symbol: str) -> SemanticStateSnapshot | None:
        history = self._histories.get(symbol)
        if history is None or history.active_snapshot is None:
            return None

        active = history.active_snapshot
        active.lifecycle_state = SemanticLifecycleState.SUPERSEDED
        return active

    def archive(self, symbol: str) -> SemanticStateSnapshot | None:
        history = self._histories.get(symbol)
        if history is None or history.active_snapshot is None:
            return None

        active = history.active_snapshot
        active.lifecycle_state = SemanticLifecycleState.ARCHIVED
        return active

    def get_active(self, symbol: str) -> SemanticStateSnapshot | None:
        history = self._histories.get(symbol)
        if history is None:
            return None
        return history.active_snapshot

    def get_latest(self, symbol: str) -> SemanticStateSnapshot | None:
        history = self._histories.get(symbol)
        if history is None:
            return None
        return history.latest_snapshot

    def get_snapshot(self, symbol: str, sequence_number: int) -> SemanticStateSnapshot | None:
        history = self._histories.get(symbol)
        if history is None:
            return None
        for snap in history.snapshots:
            if snap.sequence_number == sequence_number:
                return snap
        return None

    def get_history(self, symbol: str) -> SymbolStateHistory:
        return self._histories.get(
            symbol, SymbolStateHistory(symbol=symbol)
        )

    def get_by_version(self, symbol: str, semantic_version: str) -> list[SemanticStateSnapshot]:
        history = self._histories.get(symbol)
        if history is None:
            return []
        return [
            s for s in history.snapshots
            if s.semantic.semantic_version == semantic_version
        ]

    def get_by_lifecycle_state(
        self, symbol: str, lifecycle_state: SemanticLifecycleState
    ) -> list[SemanticStateSnapshot]:
        history = self._histories.get(symbol)
        if history is None:
            return []
        return [
            s for s in history.snapshots
            if s.lifecycle_state == lifecycle_state
        ]

    def get_all_symbols(self) -> list[str]:
        return list(self._histories.keys())

    def get_active_semantics(self) -> dict[str, DecisionSemantic]:
        result = {}
        for symbol, history in self._histories.items():
            if history.active_snapshot:
                result[symbol] = history.active_snapshot.semantic
        return result

    def reset(self) -> None:
        self._histories.clear()
        self._sequence_counters.clear()
