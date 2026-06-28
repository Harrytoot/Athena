from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from collections import deque


@dataclass
class LatencyTracker:
    max_samples: int = 2000
    samples: deque = field(default_factory=lambda: deque(maxlen=2000))

    def record(self, component: str, operation: str, duration_ms: Decimal) -> None:
        from app.production_layer.observability.metrics_collector import LatencySnapshot

        self.samples.append(
            LatencySnapshot(
                timestamp=datetime.now(timezone.utc),
                component=component,
                operation=operation,
                duration_ms=duration_ms,
            )
        )

    def percentile(self, component: str, operation: str, pct: float) -> Decimal:
        durations = sorted(
            (s.duration_ms for s in self.samples if s.component == component and s.operation == operation),
            key=lambda d: d,
        )
        if not durations:
            return Decimal("0")
        idx = max(0, min(len(durations) - 1, int(len(durations) * pct / 100.0)))
        return durations[idx]

    def p50(self, component: str, operation: str) -> Decimal:
        return self.percentile(component, operation, 50.0)

    def p95(self, component: str, operation: str) -> Decimal:
        return self.percentile(component, operation, 95.0)

    def p99(self, component: str, operation: str) -> Decimal:
        return self.percentile(component, operation, 99.0)

    def mean(self, component: str, operation: str) -> Decimal:
        durations = [s.duration_ms for s in self.samples if s.component == component and s.operation == operation]
        if not durations:
            return Decimal("0")
        return sum(durations, Decimal("0")) / Decimal(len(durations))

    def count(self, component: str, operation: str) -> int:
        return sum(1 for s in self.samples if s.component == component and s.operation == operation)

    def latest(self, component: str, operation: str) -> Optional["LatencySnapshot"]:
        for s in reversed(self.samples):
            if s.component == component and s.operation == operation:
                return s
        return None

    def exceed_threshold(self, component: str, operation: str, threshold_ms: Decimal) -> bool:
        latest = self.latest(component, operation)
        if latest is None:
            return False
        return latest.duration_ms > threshold_ms

    def clear(self) -> None:
        self.samples.clear()
