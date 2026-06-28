import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.broker_integration.gateway.failover_router import (
    FailoverRouter,
    FailoverConfig,
    FailoverState,
    FailoverEvent,
)


class TestFailoverState:
    def test_states(self):
        assert FailoverState.PRIMARY == "primary"
        assert FailoverState.FAILOVER == "failover"
        assert FailoverState.DEGRADED == "degraded"
        assert FailoverState.RECOVERING == "recovering"


class TestFailoverConfig:
    def test_defaults(self):
        cfg = FailoverConfig()
        assert cfg.failure_threshold == 3
        assert cfg.failure_window_seconds == 60.0
        assert cfg.recovery_threshold == 5
        assert cfg.recovery_window_seconds == 120.0


class TestFailoverRouter:
    def test_initial_state(self):
        router = FailoverRouter()
        assert router.state == FailoverState.PRIMARY

    def test_record_failure_below_threshold(self):
        router = FailoverRouter(config=FailoverConfig(failure_threshold=3))
        router.record_failure()
        router.record_failure()
        assert not router.should_failover()

    def test_record_failure_triggers_failover(self):
        router = FailoverRouter(config=FailoverConfig(failure_threshold=3))
        router.record_failure()
        router.record_failure()
        router.record_failure()
        assert router.should_failover()

    def test_activate_failover_changes_state(self):
        router = FailoverRouter()
        router.activate_failover()
        assert router.state == FailoverState.FAILOVER

    def test_should_not_failover_when_already_in_failover(self):
        router = FailoverRouter()
        router.activate_failover()
        assert not router.should_failover()

    def test_record_success_during_failover(self):
        router = FailoverRouter()
        router.activate_failover()
        router.record_success()
        assert router.state == FailoverState.FAILOVER

    def test_recovery_restore_primary(self):
        router = FailoverRouter(config=FailoverConfig(recovery_threshold=3))
        router.activate_failover()
        router.start_recovery()

        assert router.state == FailoverState.RECOVERING

        router.record_success()
        router.record_success()
        router.record_success()

        assert router.state == FailoverState.PRIMARY

    def test_restore_primary(self):
        router = FailoverRouter(config=FailoverConfig(recovery_threshold=2))
        router.activate_failover()
        router.start_recovery()
        router.record_success()
        router.record_success()

        router.restore_primary()
        assert router.state == FailoverState.PRIMARY

    def test_consecutive_failures(self):
        router = FailoverRouter(config=FailoverConfig(failure_threshold=3))
        router.record_failure()
        router.record_failure()
        router.record_failure()
        assert router.should_failover()

    def test_success_resets_failure_count(self):
        router = FailoverRouter(config=FailoverConfig(failure_threshold=3))
        router.record_failure()
        router.record_failure()
        router.record_success()

        stats = router.get_stats()
        assert stats["consecutive_failures"] == 0

    def test_set_degraded(self):
        router = FailoverRouter()
        router.set_degraded("High latency")
        assert router.state == FailoverState.DEGRADED

    def test_history_tracks_events(self):
        router = FailoverRouter()
        router.activate_failover()
        router.restore_primary()

        history = router.get_history()
        assert len(history) == 2
        assert history[0].event_type == "failover_activated"
        assert history[1].event_type == "primary_restored"

    def test_reset(self):
        router = FailoverRouter()
        router.record_failure()
        router.record_failure()
        router.activate_failover()

        router.reset()
        assert router.state == FailoverState.PRIMARY
        stats = router.get_stats()
        assert stats["consecutive_failures"] == 0

    def test_get_stats(self):
        router = FailoverRouter()
        router.record_failure()
        stats = router.get_stats()
        assert "state" in stats
        assert stats["consecutive_failures"] == 1
        assert "recent_failures" in stats

    def test_should_restore_not_in_recovering(self):
        router = FailoverRouter()
        assert not router.should_restore()

        router.activate_failover()
        assert not router.should_restore()
