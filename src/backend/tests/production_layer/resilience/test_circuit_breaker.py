import pytest
from datetime import datetime, timezone

from app.production_layer.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_successful_call(self):
        cb = CircuitBreaker(name="test")
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED
        assert cb.total_successes == 1

    def test_failure_increment(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(failure_threshold=3),
        )
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert cb.failure_count == 2
        assert cb.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(failure_threshold=2),
        )
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        assert cb.state == CircuitState.OPEN
        assert cb.is_open()

    def test_open_circuit_rejects_calls(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                recovery_timeout_seconds=9999,
            ),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass

        try:
            cb.call(lambda: "should not run")
            assert False, "Should have raised CircuitBreakerOpenError"
        except CircuitBreakerOpenError:
            pass

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                recovery_timeout_seconds=0,
            ),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass

        assert cb.state == CircuitState.OPEN
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.HALF_OPEN

    def test_close_after_successful_probes(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                recovery_timeout_seconds=0,
                reset_success_threshold=2,
                half_open_max_requests=10,
            ),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass

        cb.call(lambda: "ok")
        cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                recovery_timeout_seconds=0,
                reset_success_threshold=5,
            ),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass

        cb.call(lambda: "ok")
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN

    def test_reset(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(failure_threshold=1),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.is_open()
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_half_open_max_requests(self):
        cb = CircuitBreaker(
            name="test",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                recovery_timeout_seconds=0,
                half_open_max_requests=2,
                reset_success_threshold=10,
            ),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass

        cb.call(lambda: "ok")
        cb.call(lambda: "ok")

        try:
            cb.call(lambda: "third")
            assert False, "Should have raised"
        except CircuitBreakerOpenError:
            pass
