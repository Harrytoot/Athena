import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class IngestionEvent:
    event_type: str
    symbol: str
    payload: dict = field(default_factory=dict)
    event_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = ""
    sequence_number: int = 0

    def __post_init__(self):
        if not self.event_id:
            self.event_id = self._compute_id()

    def _compute_id(self) -> str:
        raw = json.dumps({
            "event_type": self.event_type,
            "symbol": self.symbol,
            "sequence_number": self.sequence_number,
            "timestamp": self.event_timestamp,
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class IngestionEventBus:

    def __init__(self):
        self._event_log: list[IngestionEvent] = []
        self._sequence_counters: dict[str, int] = {}
        self._subscribers: list[callable] = []
        self._replay_mode: bool = False

    def publish(
        self,
        event_type: str,
        symbol: str,
        payload: dict | None = None,
    ) -> IngestionEvent:
        self._sequence_counters.setdefault(symbol, 0)
        self._sequence_counters[symbol] += 1
        seq = self._sequence_counters[symbol]

        event = IngestionEvent(
            event_type=event_type,
            symbol=symbol,
            payload=payload or {},
            sequence_number=seq,
        )
        self._event_log.append(event)

        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                logger.exception("Subscriber failed for event %s", event.event_id)

        logger.debug(
            "Published event %s [%s] symbol=%s seq=%d",
            event.event_id, event_type, symbol, seq,
        )
        return event

    def subscribe(self, callback: callable) -> None:
        self._subscribers.append(callback)

    def get_event_log(self) -> list[IngestionEvent]:
        return list(self._event_log)

    def get_events_for_symbol(self, symbol: str) -> list[IngestionEvent]:
        return [e for e in self._event_log if e.symbol == symbol]

    def reset(self) -> None:
        self._event_log.clear()
        self._sequence_counters.clear()

    @property
    def event_count(self) -> int:
        return len(self._event_log)

    def to_replay_events(self) -> list[dict]:
        return [
            {
                "event_type": e.event_type,
                "symbol": e.symbol,
                "payload": e.payload,
                "event_timestamp": e.event_timestamp,
                "event_id": e.event_id,
                "sequence_number": e.sequence_number,
            }
            for e in self._event_log
        ]

    @staticmethod
    def from_replay_events(events_data: list[dict]) -> list[IngestionEvent]:
        return [
            IngestionEvent(
                event_type=e["event_type"],
                symbol=e["symbol"],
                payload=e.get("payload", {}),
                event_timestamp=e.get("event_timestamp", ""),
                event_id=e.get("event_id", ""),
                sequence_number=e.get("sequence_number", 0),
            )
            for e in events_data
        ]
