from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.live_hardening.capital_manager import CapitalManager, CapitalState
from app.live_hardening.margin_engine import MarginEngine, MarginConfig
from app.live_hardening.order_prevalidator import OrderPrevalidator
from app.live_hardening.exchange_rules_engine import ExchangeRulesEngine, MarketId
from app.live_hardening.compliance_guard import ComplianceGuard, ComplianceResult


@dataclass
class SafetyConfig:
    max_drawdown_pct: Decimal = Decimal("25")
    max_leverage: Decimal = Decimal("3")
    max_single_exposure_pct: Decimal = Decimal("25")
    max_sector_exposure_pct: Decimal = Decimal("50")
    enable_margin_trading: bool = False
    strict_mode: bool = True
    max_order_notional: Decimal = Decimal("100000000")
    block_during_drawdown: bool = True
    block_on_exchange_closed: bool = True
    kill_switch_active: bool = False


@dataclass
class SafetyCheckResult:
    passed: bool = True
    compliance: ComplianceResult | None = None
    capital_state: CapitalState | None = None
    kill_switch_blocked: bool = False
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_safe(self) -> bool:
        if self.kill_switch_blocked:
            return False
        if self.compliance and not self.compliance.passed:
            return False
        return self.passed

    @property
    def summary(self) -> str:
        if self.kill_switch_blocked:
            return "BLOCKED: Kill switch active"
        if self.compliance:
            return self.compliance.summary
        if self.passed:
            return "PASSED"
        return "BLOCKED"


class TradingSafetyLayer:

    def __init__(self, config: SafetyConfig | None = None):
        self.config = config or SafetyConfig()

        self.capital_manager = CapitalManager(
            max_drawdown_pct=self.config.max_drawdown_pct,
            max_leverage=self.config.max_leverage,
            max_single_exposure_pct=self.config.max_single_exposure_pct,
            max_sector_exposure_pct=self.config.max_sector_exposure_pct,
        )

        self.margin_engine = MarginEngine(
            config=MarginConfig(
                enable_margin_trading=self.config.enable_margin_trading,
            )
        )

        self.order_prevalidator = OrderPrevalidator(
            max_order_notional=self.config.max_order_notional,
        )

        self.exchange_rules_engine = ExchangeRulesEngine()

        self.compliance_guard = ComplianceGuard(
            capital_manager=self.capital_manager,
            margin_engine=self.margin_engine,
            order_prevalidator=self.order_prevalidator,
            exchange_rules_engine=self.exchange_rules_engine,
            strict_mode=self.config.strict_mode,
        )

    def validate_trade(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        market_id: MarketId | str,
        equity: Decimal,
        cash: Decimal,
        current_positions_value: Decimal = Decimal("0"),
        reference_price: Decimal | None = None,
        check_time: datetime | None = None,
        strategy_id: str | None = None,
        order_id: str = "",
        asset_sector: str = "",
    ) -> SafetyCheckResult:
        result = SafetyCheckResult()

        if self.config.kill_switch_active:
            result.kill_switch_blocked = True
            result.passed = False
            result.violations.append("Trading safety kill switch is active")
            return result

        self.capital_manager.update_state(
            equity=equity,
            cash=cash,
        )

        cap_state = self.capital_manager.state
        result.capital_state = cap_state

        if self.config.block_during_drawdown and cap_state.drawdown_pct >= self.config.max_drawdown_pct:
            result.passed = False
            result.violations.append(
                f"Drawdown {cap_state.drawdown_pct:.2f}% exceeds max {self.config.max_drawdown_pct}%"
            )
            return result

        compliance = self.compliance_guard.pre_execution_gate(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            market_id=market_id,
            equity=equity,
            cash=cash,
            current_positions_value=current_positions_value,
            reference_price=reference_price,
            check_time=check_time,
            strategy_id=strategy_id,
        )
        result.compliance = compliance

        if compliance.prevalidation:
            result.violations.extend(compliance.prevalidation.violations)
            result.warnings.extend(compliance.prevalidation.warnings)

        if compliance.exchange_check:
            result.violations.extend(compliance.exchange_check.violations)
            result.warnings.extend(compliance.exchange_check.warnings)

        if compliance.capital_check:
            result.violations.extend(compliance.capital_check.violations)

        if compliance.margin_check:
            result.violations.extend(compliance.margin_check.violations)

        result.passed = compliance.passed

        return result

    def validate_batch(
        self,
        orders: list[dict],
        market_id: MarketId | str,
        equity: Decimal,
        cash: Decimal,
        current_positions_value: Decimal = Decimal("0"),
        check_time: datetime | None = None,
    ) -> list[SafetyCheckResult]:
        results: list[SafetyCheckResult] = []

        if self.config.kill_switch_active:
            for order in orders:
                r = SafetyCheckResult(
                    passed=False,
                    kill_switch_blocked=True,
                    violations=["Trading safety kill switch is active"],
                )
                results.append(r)
            return results

        self.capital_manager.update_state(equity=equity, cash=cash)

        compliance_results = self.compliance_guard.check_batch(
            orders=orders,
            market_id=market_id,
            equity=equity,
            cash=cash,
            current_positions_value=current_positions_value,
            check_time=check_time,
        )

        for cr in compliance_results:
            sr = SafetyCheckResult(
                passed=cr.passed,
                compliance=cr,
                capital_state=self.capital_manager.state,
                violations=list(cr.all_violations),
                warnings=list(cr.all_warnings),
            )
            results.append(sr)

        return results

    def get_capital_protection_status(self) -> dict:
        state = self.capital_manager.state
        return {
            "equity": str(state.current_equity),
            "peak_equity": str(state.peak_equity),
            "drawdown_pct": str(state.drawdown_pct),
            "max_drawdown_pct": str(self.config.max_drawdown_pct),
            "drawdown_limit_reached": state.drawdown_pct >= self.config.max_drawdown_pct,
            "leverage": str(state.leverage_ratio),
            "max_leverage": str(self.config.max_leverage),
            "total_exposure": str(state.total_exposure),
            "cash": str(state.cash),
        }

    def get_margin_status(
        self,
        equity: Decimal,
        cash: Decimal,
        positions_value: Decimal,
    ) -> dict:
        account = self.margin_engine.compute_account(
            equity=equity,
            cash=cash,
            positions_value=positions_value,
        )
        return {
            "equity": str(account.equity),
            "cash": str(account.cash),
            "margin_used": str(account.margin_used),
            "maintenance_required": str(account.maintenance_margin_required),
            "buying_power": str(account.buying_power),
            "margin_call": account.margin_call_triggered,
            "liquidation_risk_pct": str(account.liquidation_risk_pct),
            "margin_enabled": self.config.enable_margin_trading,
        }

    def get_exchange_rules_summary(self, market_id: MarketId | str) -> dict:
        return self.exchange_rules_engine.get_profile_summary(market_id)

    def activate_kill_switch(self):
        self.config.kill_switch_active = True

    def deactivate_kill_switch(self):
        self.config.kill_switch_active = False

    def is_kill_switch_active(self) -> bool:
        return self.config.kill_switch_active

    def reset_drawdown_peak(self, equity: Decimal):
        self.capital_manager.update_state(equity=equity, cash=self.capital_manager.state.cash)

    def get_safety_report(self) -> dict:
        capital = self.get_capital_protection_status()
        return {
            "kill_switch_active": self.config.kill_switch_active,
            "capital_protection": capital,
            "strict_mode": self.config.strict_mode,
            "margin_enabled": self.config.enable_margin_trading,
            "markets_available": [m.value for m in self.exchange_rules_engine.list_markets()],
        }
