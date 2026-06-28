from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from app.domain.entities.portfolio import Position
from app.execution_live.broker.base import BrokerPosition


class PositionDiffAction(str, Enum):
    NONE = "none"
    ADD_LOCAL = "add_local"
    ADD_BROKER = "add_broker"
    REMOVE_LOCAL = "remove_local"
    REMOVE_BROKER = "remove_broker"
    UPDATE_QUANTITY = "update_quantity"
    UPDATE_PRICE = "update_price"


@dataclass
class PositionDiffDetail:
    symbol: str
    action: PositionDiffAction = PositionDiffAction.NONE
    local_quantity: Decimal = Decimal("0")
    broker_quantity: Decimal = Decimal("0")
    local_cost_price: Decimal = Decimal("0")
    broker_cost_price: Decimal = Decimal("0")
    local_market_value: Decimal = Decimal("0")
    broker_market_value: Decimal = Decimal("0")
    quantity_delta: Decimal = Decimal("0")
    price_delta: Decimal = Decimal("0")
    resolved: bool = False
    resolution_note: str = ""


@dataclass
class PositionReconciliationResult:
    matched: list[PositionDiffDetail] = field(default_factory=list)
    diffs: list[PositionDiffDetail] = field(default_factory=list)
    reconciled: bool = False
    reconciled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str = ""

    @property
    def diff_count(self) -> int:
        return len(self.diffs)

    @property
    def has_breaks(self) -> bool:
        return any(d.action != PositionDiffAction.NONE for d in self.diffs)


class PositionReconciler:
    """Reconciles local portfolio positions against broker positions.

    Detects:
    - Quantity mismatches
    - Cost basis differences
    - Missing positions (local or broker side)
    - Market value discrepancies

    Builds on the simpler PositionSync in execution_live but adds
    detailed diff tracking, tolerance-based resolution, and audit trail.
    """

    def __init__(
        self,
        quantity_tolerance: Decimal = Decimal("0.0001"),
        price_tolerance: Decimal = Decimal("0.01"),
    ):
        self.quantity_tolerance = quantity_tolerance
        self.price_tolerance = price_tolerance
        self._reconciliations: list[PositionReconciliationResult] = []

    def reconcile(
        self,
        local_positions: list[Position],
        broker_positions: list[BrokerPosition],
    ) -> PositionReconciliationResult:
        result = PositionReconciliationResult()

        local_map: dict[str, Position] = {}
        for p in local_positions:
            local_map[p.symbol] = p

        broker_map: dict[str, BrokerPosition] = {}
        for bp in broker_positions:
            broker_map[bp.symbol] = bp

        all_symbols = set(local_map.keys()) | set(broker_map.keys())

        for symbol in sorted(all_symbols):
            local = local_map.get(symbol)
            broker = broker_map.get(symbol)

            detail = PositionDiffDetail(symbol=symbol)

            if local and broker:
                detail.local_quantity = local.shares
                detail.broker_quantity = broker.quantity
                detail.local_cost_price = local.cost_price
                detail.broker_cost_price = broker.average_price
                detail.local_market_value = local.market_value
                detail.broker_market_value = broker.market_value or Decimal("0")

                qty_diff = abs(local.shares - broker.quantity)
                price_diff = abs(local.cost_price - broker.average_price)

                if qty_diff <= self.quantity_tolerance and price_diff <= self.price_tolerance:
                    detail.action = PositionDiffAction.NONE
                    result.matched.append(detail)
                else:
                    if qty_diff > self.quantity_tolerance:
                        detail.action = PositionDiffAction.UPDATE_QUANTITY
                        detail.quantity_delta = broker.quantity - local.shares
                    if price_diff > self.price_tolerance:
                        if detail.action == PositionDiffAction.NONE:
                            detail.action = PositionDiffAction.UPDATE_PRICE
                        detail.price_delta = broker.average_price - local.cost_price

                    result.diffs.append(detail)

            elif local and not broker:
                detail.action = PositionDiffAction.ADD_LOCAL
                detail.local_quantity = local.shares
                detail.local_cost_price = local.cost_price
                detail.local_market_value = local.market_value
                detail.quantity_delta = -local.shares
                result.diffs.append(detail)

            elif not local and broker:
                detail.action = PositionDiffAction.ADD_BROKER
                detail.broker_quantity = broker.quantity
                detail.broker_cost_price = broker.average_price
                detail.broker_market_value = broker.market_value or Decimal("0")
                detail.quantity_delta = broker.quantity
                result.diffs.append(detail)

        result.reconciled = len(result.diffs) == 0

        if result.reconciled:
            result.summary = f"All {len(result.matched)} positions reconciled"
        else:
            actions = [d.action.value for d in result.diffs]
            result.summary = f"{len(result.diffs)} diffs: {', '.join(actions[:5])}"

        self._reconciliations.append(result)
        return result

    def resolve_diffs(
        self,
        result: PositionReconciliationResult,
        resolve_to_broker: bool = True,
    ) -> PositionReconciliationResult:
        """Auto-resolve diffs by trusting broker (or local)."""
        for diff in result.diffs:
            if resolve_to_broker:
                diff.local_quantity = diff.broker_quantity
                diff.local_cost_price = diff.broker_cost_price
                diff.resolution_note = "Resolved to broker values"
            else:
                diff.broker_quantity = diff.local_quantity
                diff.broker_cost_price = diff.local_cost_price
                diff.resolution_note = "Resolved to local values"
            diff.resolved = True
        return result

    def get_history(self) -> list[PositionReconciliationResult]:
        return list(self._reconciliations)

    def get_last(self) -> PositionReconciliationResult | None:
        return self._reconciliations[-1] if self._reconciliations else None
