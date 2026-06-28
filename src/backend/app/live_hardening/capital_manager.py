from dataclasses import dataclass, field
from decimal import Decimal

DEFAULT_MAX_DRAWDOWN_PCT = Decimal("25")
DEFAULT_MAX_LEVERAGE = Decimal("3")
DEFAULT_MAX_SINGLE_EXPOSURE_PCT = Decimal("25")
DEFAULT_MAX_SECTOR_EXPOSURE_PCT = Decimal("50")


@dataclass
class ExposureLimit:
    asset_id: str
    max_notional: Decimal
    max_weight_pct: Decimal
    sector: str = ""

    def is_exceeded(self, current_notional: Decimal, total_equity: Decimal) -> bool:
        if current_notional > self.max_notional:
            return True
        if total_equity > 0:
            current_pct = current_notional / total_equity * Decimal("100")
            if current_pct > self.max_weight_pct:
                return True
        return False


@dataclass
class CapitalState:
    current_equity: Decimal = Decimal("0")
    peak_equity: Decimal = Decimal("0")
    drawdown_pct: Decimal = Decimal("0")
    total_exposure: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    leverage_ratio: Decimal = Decimal("0")

    @classmethod
    def initial(cls, equity: Decimal, cash: Decimal | None = None) -> "CapitalState":
        if cash is None:
            cash = equity
        return cls(
            current_equity=equity,
            peak_equity=equity,
            drawdown_pct=Decimal("0"),
            total_exposure=Decimal("0"),
            cash=cash,
            leverage_ratio=Decimal("0"),
        )


@dataclass
class CapitalCheckResult:
    passed: bool = True
    drawdown_ok: bool = True
    exposure_ok: bool = True
    leverage_ok: bool = True
    violations: list[str] = field(default_factory=list)
    current_drawdown_pct: Decimal = Decimal("0")
    current_leverage: Decimal = Decimal("0")
    available_capital: Decimal = Decimal("0")


class CapitalManager:

    def __init__(
        self,
        max_drawdown_pct: Decimal = DEFAULT_MAX_DRAWDOWN_PCT,
        max_leverage: Decimal = DEFAULT_MAX_LEVERAGE,
        max_single_exposure_pct: Decimal = DEFAULT_MAX_SINGLE_EXPOSURE_PCT,
        max_sector_exposure_pct: Decimal = DEFAULT_MAX_SECTOR_EXPOSURE_PCT,
    ):
        self.max_drawdown_pct = max_drawdown_pct
        self.max_leverage = max_leverage
        self.max_single_exposure_pct = max_single_exposure_pct
        self.max_sector_exposure_pct = max_sector_exposure_pct
        self._state = CapitalState.initial(Decimal("0"))
        self._asset_exposures: dict[str, Decimal] = {}
        self._sector_exposures: dict[str, Decimal] = {}
        self._asset_sector_map: dict[str, str] = {}
        self._exposure_limits: dict[str, ExposureLimit] = {}

    def update_state(
        self,
        equity: Decimal,
        cash: Decimal | None = None,
        asset_exposures: dict[str, Decimal] | None = None,
        sector_exposures: dict[str, Decimal] | None = None,
    ):
        prev_peak = self._state.peak_equity
        new_peak = max(prev_peak, equity)
        drawdown = Decimal("0")
        if new_peak > 0:
            drawdown = (new_peak - equity) / new_peak * Decimal("100")

        total_exposure = Decimal("0")
        if asset_exposures:
            total_exposure = sum(asset_exposures.values())
            self._asset_exposures = dict(asset_exposures)
        if sector_exposures:
            self._sector_exposures = dict(sector_exposures)

        leverage = Decimal("0")
        if equity > 0:
            leverage = total_exposure / equity

        if cash is None:
            cash = equity - total_exposure

        self._state = CapitalState(
            current_equity=equity,
            peak_equity=new_peak,
            drawdown_pct=drawdown,
            total_exposure=total_exposure,
            cash=cash,
            leverage_ratio=leverage,
        )

    def set_exposure_limits(self, limits: list[ExposureLimit]):
        self._exposure_limits = {limit.asset_id: limit for limit in limits}

    def set_asset_sector_map(self, asset_sector: dict[str, str]):
        self._asset_sector_map = dict(asset_sector)

    def check_capital(self, equity: Decimal | None = None) -> CapitalCheckResult:
        state = self._state
        if equity is not None:
            prev_peak = state.peak_equity
            new_peak = max(prev_peak, equity)
            drawdown = Decimal("0")
            if new_peak > 0:
                drawdown = (new_peak - equity) / new_peak * Decimal("100")
        else:
            drawdown = state.drawdown_pct
            equity = state.current_equity

        result = CapitalCheckResult(
            current_drawdown_pct=drawdown,
            current_leverage=state.leverage_ratio,
            available_capital=state.cash,
        )

        if drawdown >= self.max_drawdown_pct:
            result.drawdown_ok = False
            result.violations.append(
                f"Drawdown {drawdown:.2f}% exceeds max {self.max_drawdown_pct}%"
            )

        if state.leverage_ratio > self.max_leverage:
            result.leverage_ok = False
            result.violations.append(
                f"Leverage {state.leverage_ratio:.4f} exceeds max {self.max_leverage}"
            )

        if self._exposure_limits:
            for limit in self._exposure_limits.values():
                current = self._asset_exposures.get(limit.asset_id, Decimal("0"))
                if limit.is_exceeded(current, equity):
                    result.exposure_ok = False
                    result.violations.append(
                        f"Asset {limit.asset_id} exposure {current} exceeds limit {limit.max_notional}"
                    )

        for sector, exposure in self._sector_exposures.items():
            if equity > 0:
                pct = exposure / equity * Decimal("100")
                if pct > self.max_sector_exposure_pct:
                    result.exposure_ok = False
                    result.violations.append(
                        f"Sector {sector} exposure {pct:.2f}% exceeds max {self.max_sector_exposure_pct}%"
                    )

        result.passed = result.drawdown_ok and result.exposure_ok and result.leverage_ok
        return result

    def check_new_trade(
        self,
        asset_id: str,
        trade_notional: Decimal,
        equity: Decimal | None = None,
        sector: str = "",
    ) -> CapitalCheckResult:
        if equity is None:
            equity = self._state.current_equity

        result = self.check_capital(equity=equity)

        if not result.passed:
            return result

        new_exposure = self._asset_exposures.get(asset_id, Decimal("0")) + trade_notional
        if equity > 0:
            new_pct = new_exposure / equity * Decimal("100")
            if new_pct > self.max_single_exposure_pct:
                result.exposure_ok = False
                result.violations.append(
                    f"New {asset_id} exposure {new_pct:.2f}% exceeds max {self.max_single_exposure_pct}%"
                )

        if sector:
            sector_exposure = self._sector_exposures.get(sector, Decimal("0")) + trade_notional
            if equity > 0:
                sector_pct = sector_exposure / equity * Decimal("100")
                if sector_pct > self.max_sector_exposure_pct:
                    result.exposure_ok = False
                    result.violations.append(
                        f"Sector {sector} exposure {sector_pct:.2f}% exceeds max {self.max_sector_exposure_pct}%"
                    )

        if trade_notional > result.available_capital:
            result.violations.append(
                f"Insufficient capital: need {trade_notional}, available {result.available_capital}"
            )

        new_total_exposure = self._state.total_exposure + trade_notional
        if equity > 0:
            new_leverage = new_total_exposure / equity
            if new_leverage > self.max_leverage:
                result.leverage_ok = False
                result.violations.append(
                    f"Post-trade leverage {new_leverage:.4f} exceeds max {self.max_leverage}"
                )

        result.passed = result.drawdown_ok and result.exposure_ok and result.leverage_ok
        return result

    def get_available_risk_budget(self, equity: Decimal | None = None) -> Decimal:
        if equity is None:
            equity = self._state.current_equity
        if equity <= 0:
            return Decimal("0")

        capital_check = self.check_capital(equity=equity)
        if not capital_check.drawdown_ok:
            return Decimal("0")

        remaining_drawdown = self.max_drawdown_pct - capital_check.current_drawdown_pct
        if remaining_drawdown <= 0:
            return Decimal("0")

        risk_budget = equity * remaining_drawdown / Decimal("100")
        return max(Decimal("0"), risk_budget)

    @property
    def state(self) -> CapitalState:
        return self._state

    @property
    def asset_exposures(self) -> dict[str, Decimal]:
        return dict(self._asset_exposures)

    @property
    def sector_exposures(self) -> dict[str, Decimal]:
        return dict(self._sector_exposures)
