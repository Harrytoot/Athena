from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class DegradationLevel(Enum):
    NORMAL = 0
    CONSERVATIVE = 1
    PAPER_ONLY = 2
    SHUTDOWN = 3


@dataclass
class DegradationPolicy:
    level: DegradationLevel
    max_position_size_pct: Decimal
    max_leverage: Decimal
    allow_live_trading: bool
    max_daily_trades: int
    require_manual_approval: bool
    description: str


DEGRADATION_POLICIES: Dict[DegradationLevel, DegradationPolicy] = {
    DegradationLevel.NORMAL: DegradationPolicy(
        level=DegradationLevel.NORMAL,
        max_position_size_pct=Decimal("100"),
        max_leverage=Decimal("3"),
        allow_live_trading=True,
        max_daily_trades=1000,
        require_manual_approval=False,
        description="Full normal operation",
    ),
    DegradationLevel.CONSERVATIVE: DegradationPolicy(
        level=DegradationLevel.CONSERVATIVE,
        max_position_size_pct=Decimal("25"),
        max_leverage=Decimal("1.5"),
        allow_live_trading=True,
        max_daily_trades=50,
        require_manual_approval=False,
        description="Reduced risk: smaller positions, lower leverage, fewer trades",
    ),
    DegradationLevel.PAPER_ONLY: DegradationPolicy(
        level=DegradationLevel.PAPER_ONLY,
        max_position_size_pct=Decimal("100"),
        max_leverage=Decimal("3"),
        allow_live_trading=False,
        max_daily_trades=1000,
        require_manual_approval=False,
        description="Paper trading only; no live orders",
    ),
    DegradationLevel.SHUTDOWN: DegradationPolicy(
        level=DegradationLevel.SHUTDOWN,
        max_position_size_pct=Decimal("0"),
        max_leverage=Decimal("0"),
        allow_live_trading=False,
        max_daily_trades=0,
        require_manual_approval=True,
        description="Full shutdown: no trading, manual recovery required",
    ),
}


@dataclass(frozen=True)
class DegradationEvent:
    timestamp: datetime
    from_level: DegradationLevel
    to_level: DegradationLevel
    reason: str
    auto_triggered: bool


@dataclass
class DegradationMode:
    current_level: DegradationLevel = DegradationLevel.NORMAL
    degradation_history: List[DegradationEvent] = field(default_factory=list)
    upgrade_cooldown_seconds: int = 300
    last_degraded_at: Optional[datetime] = None
    manual_override: Optional[DegradationLevel] = None

    def get_active_policy(self) -> DegradationPolicy:
        effective = self.manual_override or self.current_level
        return DEGRADATION_POLICIES[effective]

    def degrade(
        self, target: DegradationLevel, reason: str, auto: bool = True
    ) -> DegradationEvent:
        if target.value <= self.current_level.value:
            raise ValueError(
                f"Cannot degrade from {self.current_level.value} to {target.value} "
                f"(degradation must increase severity)"
            )

        event = DegradationEvent(
            timestamp=datetime.now(timezone.utc),
            from_level=self.current_level,
            to_level=target,
            reason=reason,
            auto_triggered=auto,
        )
        self.current_level = target
        self.degradation_history.append(event)
        self.last_degraded_at = datetime.now(timezone.utc)
        return event

    def upgrade(self, target: DegradationLevel, reason: str) -> DegradationEvent:
        if target.value >= self.current_level.value:
            raise ValueError(
                f"Cannot upgrade from {self.current_level.value} to {target.value} "
                f"(upgrade must reduce severity)"
            )

        if self.last_degraded_at is not None:
            elapsed = (datetime.now(timezone.utc) - self.last_degraded_at).total_seconds()
            if elapsed < self.upgrade_cooldown_seconds:
                raise DegradationCooldownError(
                    f"Upgrade cooldown active: {self.upgrade_cooldown_seconds - elapsed:.0f}s remaining"
                )

        event = DegradationEvent(
            timestamp=datetime.now(timezone.utc),
            from_level=self.current_level,
            to_level=target,
            reason=reason,
            auto_triggered=False,
        )
        self.current_level = target
        self.degradation_history.append(event)
        return event

    def set_manual_override(self, level: Optional[DegradationLevel]) -> None:
        self.manual_override = level

    def should_allow_trade(self, position_size_pct: Decimal, leverage: Decimal) -> bool:
        policy = self.get_active_policy()
        if not policy.allow_live_trading:
            return False
        if position_size_pct > policy.max_position_size_pct:
            return False
        if leverage > policy.max_leverage:
            return False
        return True

    def get_recent_degradations(self, limit: int = 20) -> List[DegradationEvent]:
        return self.degradation_history[-limit:]

    def is_normal(self) -> bool:
        return self.get_active_policy().level == DegradationLevel.NORMAL

    def reset(self) -> None:
        self.current_level = DegradationLevel.NORMAL
        self.degradation_history.clear()
        self.last_degraded_at = None
        self.manual_override = None


class DegradationCooldownError(Exception):
    pass
