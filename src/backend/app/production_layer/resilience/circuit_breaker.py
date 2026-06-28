from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(frozen=True)
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_requests: int = 3
    reset_success_threshold: int = 2


@dataclass
class CircuitBreaker:
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    half_open_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0

    def call(self, fn: Callable[[], Any]) -> Any:
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} is OPEN. "
                    f"Retry after {self._recovery_remaining_seconds()}s"
                )

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.config.half_open_max_requests:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} is HALF_OPEN and max probe requests reached"
                )
            self.half_open_requests += 1

        try:
            result = fn()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> None:
        self.total_successes += 1
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.reset_success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self.failure_count = 0
                self.success_count = 0
                self.half_open_requests = 0

    def _on_failure(self) -> None:
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _should_attempt_recovery(self) -> bool:
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout_seconds

    def _recovery_remaining_seconds(self) -> float:
        if self.last_failure_time is None:
            return 0
        elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return max(0, self.config.recovery_timeout_seconds - elapsed)

    def _transition_to(self, new_state: CircuitState) -> None:
        self.state = new_state
        self.last_state_change = datetime.now(timezone.utc)
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
            self.half_open_requests = 0

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def reset(self) -> None:
        self._transition_to(CircuitState.CLOSED)


class CircuitBreakerOpenError(Exception):
    pass
