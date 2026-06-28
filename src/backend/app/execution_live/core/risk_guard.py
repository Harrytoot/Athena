from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class RiskGuardConfig:
    max_position_pct: Decimal = Decimal("20")
    max_single_order_pct: Decimal = Decimal("10")
    max_daily_loss_pct: Decimal = Decimal("5")
    max_turnover_pct: Decimal = Decimal("200")
    max_leverage: Decimal = Decimal("1")
    max_positions: int = 50
    min_cash_reserve_pct: Decimal = Decimal("5")
    enable_kill_switch: bool = True


@dataclass
class RiskLimits:
    max_position_notional: Decimal = Decimal("0")
    max_single_order_notional: Decimal = Decimal("0")
    max_daily_loss: Decimal = Decimal("0")
    daily_turnover_limit: Decimal = Decimal("0")
    min_cash_required: Decimal = Decimal("0")

    @classmethod
    def from_config(cls, config: RiskGuardConfig, total_equity: Decimal) -> "RiskLimits":
        return cls(
            max_position_notional=total_equity * config.max_position_pct / Decimal("100"),
            max_single_order_notional=total_equity * config.max_single_order_pct / Decimal("100"),
            max_daily_loss=total_equity * config.max_daily_loss_pct / Decimal("100"),
            daily_turnover_limit=total_equity * config.max_turnover_pct / Decimal("100"),
            min_cash_required=total_equity * config.min_cash_reserve_pct / Decimal("100"),
        )


@dataclass
class RiskCheckResult:
    passed: bool = True
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class RiskGuard:

    def __init__(self, config: RiskGuardConfig | None = None):
        self.config = config or RiskGuardConfig()
        self._daily_pnl: Decimal = Decimal("0")
        self._daily_turnover: Decimal = Decimal("0")
        self._positions: dict[str, Decimal] = {}
        self._kill_switched = False
        self._violation_history: list[RiskCheckResult] = []

    def pre_trade_check(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        current_positions: dict[str, Decimal] | None = None,
        current_equity: Decimal | None = None,
        current_cash: Decimal | None = None,
    ) -> RiskCheckResult:
        result = RiskCheckResult()

        if self._kill_switched and self.config.enable_kill_switch:
            result.passed = False
            result.violations.append("Kill switch is active")
            return result

        notional = quantity * price

        if current_positions is None:
            current_positions = dict(self._positions)

        if current_equity is None:
            current_equity = Decimal("0")
        if current_cash is None:
            current_cash = Decimal("0")

        limits = RiskLimits.from_config(self.config, current_equity)

        if notional > limits.max_single_order_notional:
            result.violations.append(
                f"Order notional {notional} exceeds max single order {limits.max_single_order_notional}"
            )

        projected_position = Decimal("0")
        if symbol in current_positions:
            projected_position = current_positions[symbol]

        if side == "buy":
            projected_position += notional
        else:
            projected_position -= notional

        if abs(projected_position) > limits.max_position_notional:
            result.violations.append(
                f"Projected position {abs(projected_position)} exceeds max {limits.max_position_notional} for {symbol}"
            )

        if current_cash - notional < 0 and side == "buy":
            result.violations.append(f"Insufficient cash: need {notional}, have {current_cash}")

        if current_cash - notional < limits.min_cash_required and side == "buy":
            result.violations.append(
                f"Trade would breach min cash reserve of {limits.min_cash_required}"
            )

        if self._daily_turnover + notional > limits.daily_turnover_limit:
            result.violations.append(
                f"Daily turnover {self._daily_turnover + notional} exceeds limit {limits.daily_turnover_limit}"
            )

        if self._daily_pnl - notional * Decimal("0.01") < -limits.max_daily_loss:
            result.violations.append(
                f"Potential daily loss exceeds max {limits.max_daily_loss}"
            )

        position_count = len(current_positions)
        if position_count >= self.config.max_positions and symbol not in current_positions:
            result.violations.append(
                f"Max positions {self.config.max_positions} reached"
            )

        if abs(notional) > Decimal("0") and notional / (current_equity or Decimal("1")) > Decimal("0.5"):
            result.warnings.append(f"Large order: {notional} vs equity {current_equity}")

        result.passed = not result.has_violations

        self._violation_history.append(result)
        if len(self._violation_history) > 1000:
            self._violation_history = self._violation_history[-500:]

        return result

    def record_trade(self, notional: Decimal):
        self._daily_turnover += abs(notional)

    def record_pnl(self, pnl: Decimal):
        self._daily_pnl += pnl

    def update_positions(self, positions: dict[str, Decimal]):
        self._positions = dict(positions)

    def activate_kill_switch(self, reason: str = ""):
        self._kill_switched = True
        self._violation_history.append(
            RiskCheckResult(
                passed=False,
                violations=[f"KILL SWITCH ACTIVATED: {reason}"],
            )
        )

    def deactivate_kill_switch(self):
        self._kill_switched = False

    def is_kill_switched(self) -> bool:
        return self._kill_switched

    def get_daily_stats(self) -> dict:
        return {
            "daily_pnl": str(self._daily_pnl),
            "daily_turnover": str(self._daily_turnover),
            "kill_switched": self._kill_switched,
            "active_violations": len([r for r in self._violation_history[-50:] if not r.passed]),
        }

    def reset_daily(self):
        self._daily_pnl = Decimal("0")
        self._daily_turnover = Decimal("0")
