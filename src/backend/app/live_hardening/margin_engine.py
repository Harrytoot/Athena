from dataclasses import dataclass, field
from decimal import Decimal

DEFAULT_INITIAL_MARGIN_RATE = Decimal("1.0")
DEFAULT_MAINTENANCE_MARGIN_RATE = Decimal("0.25")
DEFAULT_MIN_MAINTENANCE_MARGIN = Decimal("0.20")
DEFAULT_LIQUIDATION_THRESHOLD = Decimal("0.05")


@dataclass
class MarginConfig:
    initial_margin_rate: Decimal = DEFAULT_INITIAL_MARGIN_RATE
    maintenance_margin_rate: Decimal = DEFAULT_MAINTENANCE_MARGIN_RATE
    min_maintenance_margin: Decimal = DEFAULT_MIN_MAINTENANCE_MARGIN
    liquidation_threshold: Decimal = DEFAULT_LIQUIDATION_THRESHOLD
    enable_margin_trading: bool = False


@dataclass
class MarginAccount:
    equity: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    maintenance_margin_required: Decimal = Decimal("0")
    available_margin: Decimal = Decimal("0")
    buying_power: Decimal = Decimal("0")
    margin_call_triggered: bool = False
    liquidation_risk_pct: Decimal = Decimal("0")

    @property
    def equity_with_loan(self) -> Decimal:
        return self.equity + self.margin_used

    @property
    def margin_ratio(self) -> Decimal:
        if self.equity_with_loan <= 0:
            return Decimal("0")
        return self.equity / self.equity_with_loan

    @property
    def excess_margin(self) -> Decimal:
        return self.equity - self.maintenance_margin_required


@dataclass
class MarginCheckResult:
    passed: bool = True
    margin_call: bool = False
    liquidation_warning: bool = False
    buying_power: Decimal = Decimal("0")
    max_new_position: Decimal = Decimal("0")
    required_margin: Decimal = Decimal("0")
    violations: list[str] = field(default_factory=list)
    account: MarginAccount = field(default_factory=MarginAccount)


class MarginEngine:

    def __init__(self, config: MarginConfig | None = None):
        self.config = config or MarginConfig()

    def compute_account(
        self,
        equity: Decimal,
        cash: Decimal,
        positions_value: Decimal,
        positions: dict[str, Decimal] | None = None,
    ) -> MarginAccount:
        if positions is None:
            positions = {}

        if not self.config.enable_margin_trading:
            return MarginAccount(
                equity=equity,
                cash=cash,
                margin_used=Decimal("0"),
                maintenance_margin_required=Decimal("0"),
                available_margin=Decimal("0"),
                buying_power=cash,
                margin_call_triggered=False,
                liquidation_risk_pct=Decimal("0"),
            )

        margin_used = positions_value * (Decimal("1") - self.config.initial_margin_rate)
        margin_used = max(Decimal("0"), margin_used)

        maintenance_required = positions_value * self.config.maintenance_margin_rate
        maintenance_required = max(
            positions_value * self.config.min_maintenance_margin,
            maintenance_required,
        )

        available = equity - maintenance_required

        buying_power = Decimal("0")
        if self.config.initial_margin_rate > 0:
            buying_power = available / self.config.initial_margin_rate
        buying_power = max(Decimal("0"), buying_power)

        margin_call = available < 0

        liquidation_risk = Decimal("0")
        if positions_value > 0:
            liquidation_risk = maintenance_required / positions_value * Decimal("100")

        return MarginAccount(
            equity=equity,
            cash=cash,
            margin_used=margin_used,
            maintenance_margin_required=maintenance_required,
            available_margin=available,
            buying_power=buying_power,
            margin_call_triggered=margin_call,
            liquidation_risk_pct=liquidation_risk,
        )

    def check_new_position(
        self,
        equity: Decimal,
        cash: Decimal,
        current_positions_value: Decimal,
        new_position_notional: Decimal,
    ) -> MarginCheckResult:
        account = self.compute_account(
            equity=equity,
            cash=cash,
            positions_value=current_positions_value + new_position_notional,
        )

        result = MarginCheckResult(
            buying_power=account.buying_power,
            max_new_position=account.buying_power,
            required_margin=new_position_notional * self.config.initial_margin_rate,
            account=account,
        )

        if not self.config.enable_margin_trading:
            if new_position_notional > cash:
                result.passed = False
                result.violations.append(
                    f"Insufficient cash: need {new_position_notional}, have {cash}"
                )
            return result

        if new_position_notional > account.buying_power:
            result.passed = False
            result.violations.append(
                f"New position {new_position_notional} exceeds buying power {account.buying_power}"
            )

        if account.margin_call_triggered:
            result.margin_call = True
            result.violations.append(
                f"Margin call triggered: equity {equity} below maintenance {account.maintenance_margin_required}"
            )

        return result

    def estimate_liquidation_price(
        self,
        entry_price: Decimal,
        quantity: Decimal,
        initial_margin: Decimal,
        maintenance_margin: Decimal,
        side: str = "buy",
    ) -> Decimal:
        if quantity <= 0:
            return Decimal("0")

        if not self.config.enable_margin_trading:
            return Decimal("0") if side == "buy" else Decimal("inf")

        position_value = entry_price * quantity
        equity_at_entry = initial_margin

        if side == "buy":
            max_loss = equity_at_entry - maintenance_margin * position_value
            if quantity > 0 and position_value > 0:
                price_drop = max_loss / quantity if max_loss > 0 else Decimal("0")
                liq_price = entry_price - price_drop
            else:
                liq_price = entry_price
        else:
            equity_at_entry_short = initial_margin
            max_loss_short = equity_at_entry_short - maintenance_margin * position_value
            if quantity > 0 and position_value > 0:
                price_rise = max_loss_short / quantity if max_loss_short > 0 else Decimal("0")
                liq_price = entry_price + price_rise
            else:
                liq_price = entry_price

        return max(Decimal("0"), liq_price)

    def compute_buying_power(
        self,
        equity: Decimal,
        cash: Decimal,
        current_margin_used: Decimal = Decimal("0"),
    ) -> Decimal:
        if not self.config.enable_margin_trading:
            return cash

        available_equity = equity - current_margin_used
        if self.config.initial_margin_rate > 0:
            return max(Decimal("0"), available_equity / self.config.initial_margin_rate)
        return Decimal("0")

    def margin_call_distance(self, account: MarginAccount | None = None) -> Decimal:
        if account is None:
            return Decimal("inf")

        if not self.config.enable_margin_trading:
            return Decimal("inf")

        excess = account.excess_margin
        if excess <= 0:
            return Decimal("0")

        return excess
