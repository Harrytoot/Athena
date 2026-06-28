from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.live_hardening.capital_manager import CapitalManager, CapitalCheckResult
from app.live_hardening.margin_engine import MarginEngine, MarginCheckResult
from app.live_hardening.order_prevalidator import OrderPrevalidator, PrevalidationResult
from app.live_hardening.exchange_rules_engine import ExchangeRulesEngine, MarketId, ExchangeRuleCheckResult


@dataclass
class ComplianceResult:
    passed: bool = True
    order_id: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    prevalidation: PrevalidationResult | None = None
    exchange_check: ExchangeRuleCheckResult | None = None
    capital_check: CapitalCheckResult | None = None
    margin_check: MarginCheckResult | None = None

    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    block_reason: str = ""
    quarantine: bool = False

    def _collect_all(self):
        all_violations: list[str] = []
        all_warnings: list[str] = []

        if self.prevalidation:
            all_violations.extend(self.prevalidation.violations)
            all_warnings.extend(self.prevalidation.warnings)

        if self.exchange_check:
            all_violations.extend(self.exchange_check.violations)
            all_warnings.extend(self.exchange_check.warnings)

        if self.capital_check:
            all_violations.extend(self.capital_check.violations)

        if self.margin_check:
            all_violations.extend(self.margin_check.violations)

        return all_violations, all_warnings

    @property
    def is_blocked(self) -> bool:
        violations, _ = self._collect_all()
        return not self.passed or len(violations) > 0

    @property
    def all_violations(self) -> list[str]:
        violations, _ = self._collect_all()
        return violations

    @property
    def all_warnings(self) -> list[str]:
        _, warnings = self._collect_all()
        return warnings

    @property
    def summary(self) -> str:
        if self.passed and not self.is_blocked:
            return "PASSED"
        violations, _ = self._collect_all()
        return f"BLOCKED: {'; '.join(violations[:5])}"


class ComplianceGuard:

    def __init__(
        self,
        capital_manager: CapitalManager | None = None,
        margin_engine: MarginEngine | None = None,
        order_prevalidator: OrderPrevalidator | None = None,
        exchange_rules_engine: ExchangeRulesEngine | None = None,
        strict_mode: bool = True,
    ):
        self.capital_manager = capital_manager or CapitalManager()
        self.margin_engine = margin_engine or MarginEngine()
        self.order_prevalidator = order_prevalidator or OrderPrevalidator()
        self.exchange_rules_engine = exchange_rules_engine or ExchangeRulesEngine()
        self.strict_mode = strict_mode

    def check_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        market_id: MarketId | str | None = None,
        equity: Decimal | None = None,
        cash: Decimal | None = None,
        current_positions_value: Decimal | None = None,
        reference_price: Decimal | None = None,
        check_time: datetime | None = None,
        order_type: str = "market",
        strategy_id: str | None = None,
        order_id: str = "",
        asset_sector: str = "",
    ) -> ComplianceResult:
        result = ComplianceResult(order_id=order_id)

        pre_val = self.order_prevalidator.validate(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            strategy_id=strategy_id,
        )
        result.prevalidation = pre_val

        if not pre_val.passed:
            result.passed = False
            result.block_reason = "prevalidation"
            return result

        if market_id is not None:
            ex_check = self.exchange_rules_engine.check_order(
                market_id=market_id,
                symbol=pre_val.normalized_symbol,
                side=pre_val.normalized_side,
                quantity=pre_val.normalized_quantity,
                price=pre_val.normalized_price,
                reference_price=reference_price,
                check_time=check_time,
            )
            result.exchange_check = ex_check

            if not ex_check.passed:
                result.passed = False
                result.block_reason = "exchange_rules"
                if self.strict_mode:
                    return result

        notional = pre_val.normalized_quantity * pre_val.normalized_price

        if equity is not None:
            cap_check = self.capital_manager.check_new_trade(
                asset_id=pre_val.normalized_symbol,
                trade_notional=notional,
                equity=equity,
                sector=asset_sector,
            )
            result.capital_check = cap_check

            if not cap_check.passed:
                result.passed = False
                result.block_reason = "capital"
                if self.strict_mode:
                    return result

        if equity is not None and cash is not None:
            pos_value = current_positions_value or Decimal("0")
            margin_check = self.margin_engine.check_new_position(
                equity=equity,
                cash=cash,
                current_positions_value=pos_value,
                new_position_notional=notional,
            )
            result.margin_check = margin_check

            if not margin_check.passed:
                result.passed = False
                result.block_reason = "margin"
                if self.strict_mode:
                    return result

        return result

    def check_batch(
        self,
        orders: list[dict],
        market_id: MarketId | str | None = None,
        equity: Decimal | None = None,
        cash: Decimal | None = None,
        current_positions_value: Decimal | None = None,
        check_time: datetime | None = None,
    ) -> list[ComplianceResult]:
        results: list[ComplianceResult] = []
        running_exposure = Decimal("0")

        for i, order in enumerate(orders):
            result = self.check_order(
                symbol=order.get("symbol", ""),
                side=order.get("side", "buy"),
                quantity=Decimal(str(order.get("quantity", "0"))),
                price=Decimal(str(order.get("price", "0"))),
                market_id=market_id,
                equity=equity,
                cash=cash,
                current_positions_value=(current_positions_value or Decimal("0")) + running_exposure,
                reference_price=order.get("reference_price"),
                check_time=check_time,
                order_type=order.get("order_type", "market"),
                strategy_id=order.get("strategy_id"),
                order_id=order.get("order_id", f"BATCH-{i}"),
                asset_sector=order.get("sector", ""),
            )
            results.append(result)

            if result.passed:
                qty = Decimal(str(order.get("quantity", "0")))
                price = Decimal(str(order.get("price", "0")))
                running_exposure += qty * price

        return results

    def pre_execution_gate(
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
    ) -> ComplianceResult:
        return self.check_order(
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

    def update_capital_state(
        self,
        equity: Decimal,
        cash: Decimal | None = None,
        asset_exposures: dict[str, Decimal] | None = None,
        sector_exposures: dict[str, Decimal] | None = None,
    ):
        self.capital_manager.update_state(
            equity=equity,
            cash=cash,
            asset_exposures=asset_exposures,
            sector_exposures=sector_exposures,
        )

    def get_guard_status(self) -> dict:
        state = self.capital_manager.state
        return {
            "capital": {
                "equity": str(state.current_equity),
                "peak": str(state.peak_equity),
                "drawdown_pct": str(state.drawdown_pct),
                "leverage": str(state.leverage_ratio),
            },
            "mode": "strict" if self.strict_mode else "lenient",
            "capital_manager_configured": self.capital_manager.max_drawdown_pct > 0,
            "margin_enabled": self.margin_engine.config.enable_margin_trading,
        }
