from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Dict, List, Optional


@dataclass(frozen=True)
class HealthStatus:
    component: str
    status: str
    message: str
    checked_at: datetime
    latency_ms: Decimal = Decimal("0")

    STATUS_UP = "up"
    STATUS_DOWN = "down"
    STATUS_TIMEOUT = "timeout"
    STATUS_HEALTHY = "healthy"


@dataclass(frozen=True)
class ComponentHealthReport:
    timestamp: datetime
    components: Dict[str, HealthStatus]
    overall_status: str
    degradation_active: bool

    def healthy_component_count(self) -> int:
        return sum(1 for s in self.components.values() if s.status == HealthStatus.STATUS_UP)

    def total_component_count(self) -> int:
        return len(self.components)


@dataclass
class SystemHealthMonitor:
    health_check_registry: Dict[str, Callable[[], HealthStatus]] = field(default_factory=dict)
    max_consecutive_failures: int = 3
    failure_counts: Dict[str, int] = field(default_factory=dict)
    degraded: bool = False

    def register_check(self, name: str, check_fn: Callable[[], HealthStatus]) -> None:
        if not name:
            raise ValueError("component name must not be empty")
        self.health_check_registry[name] = check_fn
        self.failure_counts.setdefault(name, 0)

    def unregister_check(self, name: str) -> None:
        self.health_check_registry.pop(name, None)
        self.failure_counts.pop(name, None)

    def run_all_checks(self) -> ComponentHealthReport:
        results: Dict[str, HealthStatus] = {}
        any_unhealthy = False

        for name, check_fn in self.health_check_registry.items():
            try:
                status = check_fn()
                results[name] = status
                if status.status == HealthStatus.STATUS_UP:
                    self.failure_counts[name] = 0
                else:
                    any_unhealthy = True
                    self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
            except Exception as e:
                any_unhealthy = True
                self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
                results[name] = HealthStatus(
                    component=name,
                    status=HealthStatus.STATUS_DOWN,
                    message=str(e),
                    checked_at=datetime.now(timezone.utc),
                )

        overall = HealthStatus.STATUS_UP
        if self.degraded:
            overall = "degraded"
        elif any_unhealthy:
            overall = HealthStatus.STATUS_DOWN

        return ComponentHealthReport(
            timestamp=datetime.now(timezone.utc),
            components=results,
            overall_status=overall,
            degradation_active=self.degraded,
        )

    def check_degradation_threshold(self) -> bool:
        for name, count in self.failure_counts.items():
            if count >= self.max_consecutive_failures:
                return True
        return False

    def activate_degradation(self) -> None:
        self.degraded = True

    def deactivate_degradation(self) -> None:
        self.degraded = False
        self.failure_counts.clear()

    def get_failure_summary(self) -> Dict[str, int]:
        return dict(self.failure_counts)
