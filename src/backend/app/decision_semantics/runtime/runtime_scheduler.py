import hashlib
import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Awaitable

from app.decision_semantics.runtime.semantic_delta_engine import SemanticDelta
from app.decision_semantics.runtime.state_transition_model import TransitionEvent


class SchedulerEventType(Enum):
    MARKET_TICK = "market_tick"
    FEATURE_UPDATE = "feature_update"
    RISK_RECALIBRATION = "risk_recalibration"


@dataclass
class ScheduledUpdate:
    event_type: SchedulerEventType
    symbol: str
    delta: SemanticDelta | None = None
    scheduled_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    run_at: str = ""
    schedule_id: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.schedule_id:
            self.schedule_id = self._compute_id()
        if not self.run_at:
            self.run_at = self.scheduled_at

    def _compute_id(self) -> str:
        payload = {
            "event_type": self.event_type.value,
            "symbol": self.symbol,
            "scheduled_at": self.scheduled_at,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


UpdateCallback = Callable[[str, TransitionEvent, SemanticDelta | None], Awaitable[None]]


class RuntimeScheduler:

    def __init__(self):
        self._callbacks: dict[SchedulerEventType, list[UpdateCallback]] = {
            SchedulerEventType.MARKET_TICK: [],
            SchedulerEventType.FEATURE_UPDATE: [],
            SchedulerEventType.RISK_RECALIBRATION: [],
        }
        self._pending: deque[ScheduledUpdate] = deque()

    def register_callback(
        self, event_type: SchedulerEventType, callback: UpdateCallback
    ) -> None:
        self._callbacks.setdefault(event_type, []).append(callback)

    def unregister_callback(
        self, event_type: SchedulerEventType, callback: UpdateCallback
    ) -> None:
        callbacks = self._callbacks.get(event_type, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def trigger(
        self,
        event_type: SchedulerEventType,
        symbol: str,
        delta: SemanticDelta | None = None,
        metadata: dict | None = None,
    ) -> ScheduledUpdate:
        return self.schedule(event_type, symbol, delta, metadata)

    def schedule(
        self,
        event_type: SchedulerEventType,
        symbol: str,
        delta: SemanticDelta | None = None,
        metadata: dict | None = None,
    ) -> ScheduledUpdate:
        update = ScheduledUpdate(
            event_type=event_type,
            symbol=symbol,
            delta=delta,
            metadata=metadata or {},
        )
        self._pending.append(update)
        return update

    async def process_pending(self) -> list[tuple[ScheduledUpdate, TransitionEvent]]:
        results: list[tuple[ScheduledUpdate, TransitionEvent]] = []

        while self._pending:
            update = self._pending.popleft()
            transition_event = self._map_event_type(update.event_type)

            callbacks = self._callbacks.get(update.event_type, [])
            for callback in callbacks:
                await callback(update.symbol, transition_event, update.delta)

            results.append((update, transition_event))

        return results

    async def process_one(self) -> tuple[ScheduledUpdate, TransitionEvent] | None:
        if not self._pending:
            return None

        update = self._pending.popleft()
        transition_event = self._map_event_type(update.event_type)

        callbacks = self._callbacks.get(update.event_type, [])
        for callback in callbacks:
            await callback(update.symbol, transition_event, update.delta)

        return (update, transition_event)

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def clear_pending(self) -> None:
        self._pending.clear()

    def get_pending_updates(self) -> list[ScheduledUpdate]:
        return list(self._pending)

    def get_callbacks(self, event_type: SchedulerEventType) -> list[UpdateCallback]:
        return list(self._callbacks.get(event_type, []))

    def get_registered_events(self) -> list[SchedulerEventType]:
        return [
            et for et, cbs in self._callbacks.items() if cbs
        ]

    def reset(self) -> None:
        self._callbacks = {
            SchedulerEventType.MARKET_TICK: [],
            SchedulerEventType.FEATURE_UPDATE: [],
            SchedulerEventType.RISK_RECALIBRATION: [],
        }
        self._pending.clear()

    @staticmethod
    def _map_event_type(event_type: SchedulerEventType) -> TransitionEvent:
        mapping = {
            SchedulerEventType.MARKET_TICK: TransitionEvent.MARKET_TICK,
            SchedulerEventType.FEATURE_UPDATE: TransitionEvent.FEATURE_UPDATE,
            SchedulerEventType.RISK_RECALIBRATION: TransitionEvent.RISK_RECALIBRATE,
        }
        return mapping[event_type]
