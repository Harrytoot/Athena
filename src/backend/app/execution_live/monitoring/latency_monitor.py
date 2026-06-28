from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LatencyRecord:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event: str = ""
    latency_ms: float = 0.0
    order_id: str | None = None
    strategy_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class LatencyStats:
    count: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    total_ms: float = 0.0

    @property
    def mean_seconds(self) -> float:
        return self.mean_ms / 1000.0


class LatencyMonitor:

    def __init__(self, max_records: int = 10000):
        self._records: list[LatencyRecord] = []
        self._max_records = max_records
        self._event_buffer: dict[str, datetime] = {}

    def start_event(self, event_key: str):
        self._event_buffer[event_key] = datetime.now(timezone.utc)

    def end_event(
        self,
        event_key: str,
        event: str = "",
        order_id: str | None = None,
        strategy_id: str | None = None,
        metadata: dict | None = None,
    ) -> float:
        if event_key not in self._event_buffer:
            return 0.0

        start = self._event_buffer.pop(event_key)
        latency_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000

        record = LatencyRecord(
            event=event or event_key,
            latency_ms=latency_ms,
            order_id=order_id,
            strategy_id=strategy_id,
            metadata=metadata or {},
        )
        self._records.append(record)

        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records // 2:]

        return latency_ms

    def record(self, event: str, latency_ms: float, **kwargs):
        record = LatencyRecord(
            event=event,
            latency_ms=latency_ms,
            **kwargs,
        )
        self._records.append(record)

        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records // 2:]

    def get_stats(self, event: str | None = None, limit: int | None = None) -> LatencyStats:
        records = self._records
        if event:
            records = [r for r in records if r.event == event]
        if limit:
            records = records[-limit:]

        if not records:
            return LatencyStats()

        latencies = sorted(r.latency_ms for r in records)
        n = len(latencies)

        return LatencyStats(
            count=n,
            min_ms=round(min(latencies), 2),
            max_ms=round(max(latencies), 2),
            mean_ms=round(sum(latencies) / n, 2),
            median_ms=round(latencies[n // 2], 2),
            p95_ms=round(latencies[int(n * 0.95)], 2),
            p99_ms=round(latencies[int(n * 0.99)], 2),
            total_ms=round(sum(latencies), 2),
        )

    def get_latest(self, limit: int = 10) -> list[LatencyRecord]:
        return self._records[-limit:]

    def clear(self):
        self._records.clear()
        self._event_buffer.clear()
