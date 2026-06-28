from decimal import Decimal

from app.production_layer.resilience.degradation_mode import (
    DegradationMode,
    DegradationLevel,
    DegradationPolicy,
    DegradationCooldownError,
)


class TestDegradationMode:
    def test_initial_normal(self):
        dm = DegradationMode()
        assert dm.current_level == DegradationLevel.NORMAL
        assert dm.is_normal()

    def test_get_active_policy(self):
        dm = DegradationMode()
        policy = dm.get_active_policy()
        assert policy.level == DegradationLevel.NORMAL
        assert policy.allow_live_trading

    def test_degrade_to_conservative(self):
        dm = DegradationMode()
        event = dm.degrade(DegradationLevel.CONSERVATIVE, "PnL drawdown detected")
        assert dm.current_level == DegradationLevel.CONSERVATIVE
        assert event.from_level == DegradationLevel.NORMAL
        assert event.auto_triggered
        assert len(dm.degradation_history) == 1

    def test_degrade_to_paper_only(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.CONSERVATIVE, "step 1")
        dm.degrade(DegradationLevel.PAPER_ONLY, "step 2")
        assert dm.current_level == DegradationLevel.PAPER_ONLY
        assert dm.degradation_history[0].from_level == DegradationLevel.NORMAL
        assert dm.degradation_history[1].from_level == DegradationLevel.CONSERVATIVE

    def test_degrade_to_shutdown(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.CONSERVATIVE, "s1")
        dm.degrade(DegradationLevel.PAPER_ONLY, "s2")
        dm.degrade(DegradationLevel.SHUTDOWN, "critical failure")
        assert dm.current_level == DegradationLevel.SHUTDOWN

    def test_cannot_degrade_upwards(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.CONSERVATIVE, "down")
        try:
            dm.degrade(DegradationLevel.NORMAL, "invalid")
            assert False
        except ValueError:
            pass

    def test_upgrade(self):
        dm = DegradationMode(upgrade_cooldown_seconds=0)
        dm.degrade(DegradationLevel.CONSERVATIVE, "degraded")
        dm.degrade(DegradationLevel.PAPER_ONLY, "worse")
        event = dm.upgrade(DegradationLevel.CONSERVATIVE, "recovered")
        assert dm.current_level == DegradationLevel.CONSERVATIVE
        assert not event.auto_triggered

    def test_upgrade_with_cooldown(self):
        dm = DegradationMode(upgrade_cooldown_seconds=9999)
        dm.degrade(DegradationLevel.CONSERVATIVE, "issues")
        try:
            dm.upgrade(DegradationLevel.NORMAL, "too soon")
            assert False
        except DegradationCooldownError:
            pass

    def test_upgrade_no_cooldown(self):
        dm = DegradationMode(upgrade_cooldown_seconds=0)
        dm.degrade(DegradationLevel.CONSERVATIVE, "issue")
        dm.upgrade(DegradationLevel.NORMAL, "fixed")
        assert dm.current_level == DegradationLevel.NORMAL

    def test_cannot_upgrade_downwards(self):
        dm = DegradationMode()
        try:
            dm.upgrade(DegradationLevel.SHUTDOWN, "invalid")
            assert False
        except ValueError:
            pass

    def test_manual_override(self):
        dm = DegradationMode()
        dm.set_manual_override(DegradationLevel.SHUTDOWN)
        policy = dm.get_active_policy()
        assert policy.level == DegradationLevel.SHUTDOWN
        assert not policy.allow_live_trading

        dm.set_manual_override(None)
        assert dm.get_active_policy().level == DegradationLevel.NORMAL

    def test_should_allow_trade(self):
        dm = DegradationMode()
        assert dm.should_allow_trade(Decimal("50"), Decimal("1"))
        assert not dm.should_allow_trade(Decimal("200"), Decimal("1"))

    def test_should_allow_trade_paper_only(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.PAPER_ONLY, "issues")
        assert not dm.should_allow_trade(Decimal("10"), Decimal("1"))

    def test_conservative_limits(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.CONSERVATIVE, "risk")
        assert dm.should_allow_trade(Decimal("10"), Decimal("1"))
        assert not dm.should_allow_trade(Decimal("30"), Decimal("1"))
        assert not dm.should_allow_trade(Decimal("10"), Decimal("2"))

    def test_recent_degradations(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.CONSERVATIVE, "r1")
        dm.degrade(DegradationLevel.PAPER_ONLY, "r2")
        recent = dm.get_recent_degradations()
        assert len(recent) == 2

    def test_reset(self):
        dm = DegradationMode()
        dm.degrade(DegradationLevel.SHUTDOWN, "critical")
        dm.set_manual_override(DegradationLevel.CONSERVATIVE)
        dm.reset()
        assert dm.current_level == DegradationLevel.NORMAL
        assert dm.manual_override is None
        assert len(dm.degradation_history) == 0
