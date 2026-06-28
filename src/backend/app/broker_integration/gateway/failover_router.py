from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class FailoverState(str, Enum):
    PRIMARY = "primary"
    FAILOVER = "failover"
    DEGRADED = "degraded"
    RECOVERING = "recovering"


@dataclass
class FailoverConfig:
    failure_threshold: int = 3
    failure_window_seconds: float = 60.0
    recovery_threshold: int = 5
    recovery_window_seconds: float = 120.0
    health_check_interval_seconds: float = 10.0


@dataclass
class FailoverEvent:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    from_state: FailoverState = FailoverState.PRIMARY
    to_state: FailoverState = FailoverState.PRIMARY
    reason: str = ""
    metadata: dict = field(default_factory=dict)


class FailoverRouter:
    """Manages failover between primary and fallback brokers.

    Monitors health signals and transitions between states:
    - PRIMARY: Normal operation with primary broker
    - FAILOVER: Primary unhealthy, using fallback
    - DEGRADED: Primary partially healthy
    - RECOVERING: Testing primary before full restore

    Automatic failover is triggered when failure_threshold
    consecutive failures occur within failure_window_seconds.
    Recovery happens after recovery_threshold consecutive
    successes within recovery_window_seconds.
    """

    def __init__(self, config: FailoverConfig | None = None):
        self.config = config or FailoverConfig()
        self._state: FailoverState = FailoverState.PRIMARY
        self._failure_times: list[datetime] = []
        self._success_times: list[datetime] = []
        self._history: list[FailoverEvent] = []
        self._consecutive_failures: int = 0
        self._consecutive_successes: int = 0

    @property
    def state(self) -> FailoverState:
        return self._state

    def record_failure(self):
        now = datetime.now(timezone.utc)
        self._failure_times.append(now)
        self._consecutive_failures += 1
        self._consecutive_successes = 0

        cutoff = now.timestamp() - self.config.failure_window_seconds
        self._failure_times = [t for t in self._failure_times if t.timestamp() >= cutoff]

    def record_success(self):
        now = datetime.now(timezone.utc)
        self._success_times.append(now)
        self._consecutive_successes += 1
        self._consecutive_failures = 0

        cutoff = now.timestamp() - self.config.recovery_window_seconds
        self._success_times = [t for t in self._success_times if t.timestamp() >= cutoff]

        if self._state == FailoverState.RECOVERING:
            if self._consecutive_successes >= self.config.recovery_threshold:
                self.restore_primary()

    def should_failover(self) -> bool:
        if self._state == FailoverState.FAILOVER:
            return False

        recent_failures = len(self._failure_times)
        return recent_failures >= self.config.failure_threshold or self._consecutive_failures >= self.config.failure_threshold

    def should_restore(self) -> bool:
        if self._state != FailoverState.RECOVERING:
            return False

        recent_successes = len(self._success_times)
        return recent_successes >= self.config.recovery_threshold and self._consecutive_successes >= self.config.recovery_threshold

    def activate_failover(self):
        prev = self._state
        self._state = FailoverState.FAILOVER
        self._consecutive_successes = 0
        event = FailoverEvent(
            event_type="failover_activated",
            from_state=prev,
            to_state=FailoverState.FAILOVER,
            reason=f"Failure threshold reached ({self.config.failure_threshold})",
        )
        self._history.append(event)

    def restore_primary(self):
        prev = self._state
        self._state = FailoverState.PRIMARY
        self._consecutive_failures = 0
        self._failure_times.clear()
        event = FailoverEvent(
            event_type="primary_restored",
            from_state=prev,
            to_state=FailoverState.PRIMARY,
            reason=f"Recovery threshold met ({self.config.recovery_threshold})",
        )
        self._history.append(event)

    def start_recovery(self):
        prev = self._state
        self._state = FailoverState.RECOVERING
        self._consecutive_successes = 0
        event = FailoverEvent(
            event_type="recovery_started",
            from_state=prev,
            to_state=FailoverState.RECOVERING,
            reason="Testing primary broker health",
        )
        self._history.append(event)

    def set_degraded(self, reason: str = ""):
        prev = self._state
        self._state = FailoverState.DEGRADED
        event = FailoverEvent(
            event_type="degraded",
            from_state=prev,
            to_state=FailoverState.DEGRADED,
            reason=reason,
        )
        self._history.append(event)

    def get_history(self) -> list[FailoverEvent]:
        return list(self._history)

    def reset(self):
        self._state = FailoverState.PRIMARY
        self._failure_times.clear()
        self._success_times.clear()
        self._consecutive_failures = 0
        self._consecutive_successes = 0

    def get_stats(self) -> dict:
        return {
            "state": self._state.value,
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
            "recent_failures": len(self._failure_times),
            "recent_successes": len(self._success_times),
            "total_events": len(self._history),
        }
