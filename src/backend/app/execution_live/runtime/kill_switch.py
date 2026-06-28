from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class KillSwitchState(str, Enum):
    ARMED = "armed"
    TRIGGERED = "triggered"
    DISARMED = "disarmed"


@dataclass
class KillSwitchTrigger:
    trigger_id: str
    reason: str
    severity: str = "critical"
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


class KillSwitch:

    def __init__(self):
        self.state = KillSwitchState.DISARMED
        self._triggers: list[KillSwitchTrigger] = []
        self._auto_triggers_enabled = True

    def arm(self):
        self.state = KillSwitchState.ARMED

    def disarm(self):
        self.state = KillSwitchState.DISARMED

    def trigger(self, reason: str, severity: str = "critical", metadata: dict | None = None):
        self.state = KillSwitchState.TRIGGERED
        trigger = KillSwitchTrigger(
            trigger_id=f"KS-{len(self._triggers) + 1:04d}",
            reason=reason,
            severity=severity,
            metadata=metadata or {},
        )
        self._triggers.append(trigger)
        return trigger

    def reset(self):
        self.state = KillSwitchState.DISARMED
        self._triggers.clear()

    def is_active(self) -> bool:
        return self.state == KillSwitchState.TRIGGERED

    def is_armed(self) -> bool:
        return self.state == KillSwitchState.ARMED

    def should_block(self) -> bool:
        return self.state == KillSwitchState.TRIGGERED

    def check_conditions(
        self,
        daily_pnl: Decimal | None = None,
        max_daily_loss: Decimal | None = None,
        consecutive_failures: int = 0,
        max_consecutive_failures: int = 10,
        api_errors: int = 0,
        max_api_errors: int = 5,
        position_anomaly: bool = False,
    ) -> bool:
        if not self._auto_triggers_enabled or self.state != KillSwitchState.ARMED:
            return False

        if daily_pnl is not None and max_daily_loss is not None:
            if daily_pnl < -max_daily_loss:
                self.trigger(
                    reason=f"Daily loss {daily_pnl} exceeds max {max_daily_loss}",
                    severity="critical",
                    metadata={"daily_pnl": str(daily_pnl), "max_daily_loss": str(max_daily_loss)},
                )
                return True

        if consecutive_failures >= max_consecutive_failures:
            self.trigger(
                reason=f"Consecutive failures {consecutive_failures} >= {max_consecutive_failures}",
                severity="critical",
                metadata={"consecutive_failures": consecutive_failures},
            )
            return True

        if api_errors >= max_api_errors:
            self.trigger(
                reason=f"API errors {api_errors} >= {max_api_errors}",
                severity="critical",
                metadata={"api_errors": api_errors},
            )
            return True

        if position_anomaly:
            self.trigger(
                reason="Position anomaly detected",
                severity="critical",
            )
            return True

        return False

    def enable_auto_triggers(self):
        self._auto_triggers_enabled = True

    def disable_auto_triggers(self):
        self._auto_triggers_enabled = False

    def get_triggers(self) -> list[KillSwitchTrigger]:
        return list(self._triggers)

    def get_last_trigger(self) -> KillSwitchTrigger | None:
        if self._triggers:
            return self._triggers[-1]
        return None

    def status_report(self) -> dict:
        return {
            "state": self.state.value,
            "auto_triggers_enabled": self._auto_triggers_enabled,
            "trigger_count": len(self._triggers),
            "last_trigger": self._triggers[-1].reason if self._triggers else None,
        }
