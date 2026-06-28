import time
from datetime import datetime, timezone

from app.production_layer.resilience.auto_recovery import (
    AutoRecovery,
    RecoveryPhase,
    RecoveryAction,
    RecoveryStep,
)


class TestAutoRecovery:
    def test_initial_state(self):
        ar = AutoRecovery()
        assert ar.current_phase == RecoveryPhase.IDLE
        assert len(ar.recovery_history) == 0

    def test_register_action(self):
        ar = AutoRecovery()
        ar.register_action("restart", lambda: True)
        assert "restart" in ar.recovery_actions

    def test_execute_recovery_success(self):
        ar = AutoRecovery()
        ar.register_action("restart_broker", lambda: True)
        ar.register_action("reconnect_feed", lambda: True)

        actions = [
            RecoveryAction(
                name="restart", description="restart broker",
                phase=RecoveryPhase.MITIGATING, action_fn="restart_broker",
            ),
            RecoveryAction(
                name="reconnect", description="reconnect feed",
                phase=RecoveryPhase.RESTORING, action_fn="reconnect_feed",
            ),
        ]
        results = ar.execute_recovery(actions)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert ar.current_phase == RecoveryPhase.STABILIZING

    def test_execute_recovery_partial_failure(self):
        ar = AutoRecovery()
        ar.register_action("good", lambda: True)
        ar.register_action("bad", lambda: False)

        actions = [
            RecoveryAction(
                name="g", description="ok", phase=RecoveryPhase.MITIGATING,
                action_fn="good",
            ),
            RecoveryAction(
                name="b", description="fail", phase=RecoveryPhase.RESTORING,
                action_fn="bad",
            ),
        ]
        results = ar.execute_recovery(actions)
        assert len(results) == 2
        assert results[0].success
        assert not results[1].success
        assert ar.current_phase == RecoveryPhase.IDLE

    def test_execute_recovery_exception(self):
        ar = AutoRecovery()
        ar.register_action("explode", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

        actions = [
            RecoveryAction(
                name="e", description="err", phase=RecoveryPhase.MITIGATING,
                action_fn="explode",
            ),
        ]
        results = ar.execute_recovery(actions)
        assert len(results) == 1
        assert not results[0].success

    def test_stabilization_period(self):
        ar = AutoRecovery(stabilization_period_seconds=0)
        ar.register_action("ok", lambda: True)
        actions = [
            RecoveryAction(
                name="ok", description="ok", phase=RecoveryPhase.MITIGATING,
                action_fn="ok",
            ),
        ]
        ar.execute_recovery(actions)
        assert ar.is_stabilized()
        assert ar.verify_stabilization()
        assert ar.current_phase == RecoveryPhase.VERIFIED

    def test_stabilization_not_ready(self):
        ar = AutoRecovery(stabilization_period_seconds=9999)
        ar.stabilization_started_at = datetime.now(timezone.utc)
        assert not ar.is_stabilized()

    def test_reset(self):
        ar = AutoRecovery()
        ar.register_action("a", lambda: True)
        actions = [RecoveryAction("a", "d", RecoveryPhase.MITIGATING, "a")]
        ar.execute_recovery(actions)
        ar.reset()
        assert ar.current_phase == RecoveryPhase.IDLE
        assert ar.stabilization_started_at is None
        assert len(ar.recovery_history) == 0
