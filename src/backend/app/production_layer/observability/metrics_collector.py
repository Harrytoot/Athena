from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from collections import deque


@dataclass(frozen=True)
class MetricPoint:
    timestamp: datetime
    name: str
    value: Decimal
    tags: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            raise ValueError("metric name must not be empty")


@dataclass(frozen=True)
class LatencySnapshot:
    timestamp: datetime
    component: str
    operation: str
    duration_ms: Decimal


@dataclass(frozen=True)
class LiveMetrics:
    timestamp: datetime
    total_pnl: Decimal
    total_exposure: Decimal
    fill_rate_pct: Decimal
    avg_latency_ms: Decimal
    open_orders: int
    active_risk_limit_pct: Decimal


@dataclass
class MetricsCollector:
    metric_buffer: deque = field(default_factory=lambda: deque(maxlen=10000))
    latency_buffer: deque = field(default_factory=lambda: deque(maxlen=5000))

    def record_metric(self, name: str, value: Decimal, tags: Optional[Dict[str, str]] = None) -> None:
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            name=name,
            value=value,
            tags=tags or {},
        )
        self.metric_buffer.append(point)

    def record_latency(self, component: str, operation: str, duration_ms: Decimal) -> None:
        snap = LatencySnapshot(
            timestamp=datetime.now(timezone.utc),
            component=component,
            operation=operation,
            duration_ms=duration_ms,
        )
        self.latency_buffer.append(snap)

    def get_recent_metrics(self, name: str, limit: int = 50) -> List[MetricPoint]:
        matches = [m for m in self.metric_buffer if m.name == name]
        return list(matches)[-limit:]

    def get_avg_metric(self, name: str, limit: int = 50) -> Decimal:
        matches = self.get_recent_metrics(name, limit)
        if not matches:
            return Decimal("0")
        total = sum((m.value for m in matches), Decimal("0"))
        return total / Decimal(len(matches))

    def get_latency_p50(self, component: str, operation: str) -> Decimal:
        durations = [
            s.duration_ms
            for s in self.latency_buffer
            if s.component == component and s.operation == operation
        ]
        if not durations:
            return Decimal("0")
        sorted_durations = sorted(durations, key=lambda d: d)
        idx = int(len(sorted_durations) * 0.5)
        return sorted_durations[min(idx, len(sorted_durations) - 1)]

    def get_latency_p99(self, component: str, operation: str) -> Decimal:
        durations = [
            s.duration_ms
            for s in self.latency_buffer
            if s.component == component and s.operation == operation
        ]
        if not durations:
            return Decimal("0")
        sorted_durations = sorted(durations, key=lambda d: d)
        idx = int(len(sorted_durations) * 0.99)
        return sorted_durations[min(idx, len(sorted_durations) - 1)]

    def snapshot_live_metrics(
        self,
        total_pnl: Decimal,
        total_exposure: Decimal,
        fill_rate_pct: Decimal,
        open_orders: int,
        active_risk_limit_pct: Decimal,
    ) -> LiveMetrics:
        avg_lat = self.get_latency_p50("execution", "order_roundtrip")
        return LiveMetrics(
            timestamp=datetime.now(timezone.utc),
            total_pnl=total_pnl,
            total_exposure=total_exposure,
            fill_rate_pct=fill_rate_pct,
            avg_latency_ms=avg_lat,
            open_orders=open_orders,
            active_risk_limit_pct=active_risk_limit_pct,
        )

    def clear(self) -> None:
        self.metric_buffer.clear()
        self.latency_buffer.clear()
