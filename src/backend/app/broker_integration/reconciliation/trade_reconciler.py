from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.execution_live.broker.base import OrderResult, OrderSide, OrderStatus


@dataclass
class TradeRecord:
    order_id: str
    broker_order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    filled_quantity: Decimal
    average_price: Decimal
    commission: Decimal
    status: OrderStatus
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    strategy_id: str | None = None

    @property
    def notional(self) -> Decimal:
        return self.filled_quantity * self.average_price

    @classmethod
    def from_order_result(cls, result: OrderResult, strategy_id: str | None = None) -> "TradeRecord":
        return cls(
            order_id=result.client_order_id or result.broker_order_id,
            broker_order_id=result.broker_order_id,
            symbol=result.symbol,
            side=result.side,
            quantity=result.quantity,
            filled_quantity=result.filled_quantity,
            average_price=result.average_price,
            commission=result.commission,
            status=result.status,
            submitted_at=result.submitted_at,
            filled_at=result.filled_at,
            strategy_id=strategy_id,
        )


@dataclass
class TradeDiff:
    order_id: str
    field: str
    local_value: str = ""
    broker_value: str = ""
    resolved: bool = False
    resolution: str = ""

    @property
    def has_difference(self) -> bool:
        return self.local_value != self.broker_value


@dataclass
class TradeReconciliationResult:
    matched: list[TradeRecord] = field(default_factory=list)
    local_only: list[TradeRecord] = field(default_factory=list)
    broker_only: list[TradeRecord] = field(default_factory=list)
    mismatched: list[TradeDiff] = field(default_factory=list)
    reconciled: bool = False
    reconciled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str = ""

    @property
    def total_trades(self) -> int:
        return len(self.matched) + len(self.local_only) + len(self.broker_only)

    @property
    def mismatch_count(self) -> int:
        return len(self.mismatched)


class TradeReconciler:
    """Reconciles local order/trade records against broker records.

    Identifies:
    - Trades that match (same order ID, same fill details)
    - Trades that exist only locally (not found at broker)
    - Trades that exist only at broker (not recorded locally)
    - Field-level mismatches (e.g., wrong fill price)
    """

    def __init__(self, tolerance: Decimal = Decimal("0.0001")):
        self.tolerance = tolerance
        self._reconciliations: list[TradeReconciliationResult] = []

    def reconcile(
        self,
        local_trades: list[TradeRecord],
        broker_trades: list[TradeRecord],
    ) -> TradeReconciliationResult:
        result = TradeReconciliationResult()

        local_by_id: dict[str, TradeRecord] = {}
        for t in local_trades:
            key = t.broker_order_id or t.order_id
            local_by_id[key] = t

        broker_by_id: dict[str, TradeRecord] = {}
        for t in broker_trades:
            broker_by_id[t.broker_order_id] = t

        all_ids = set(local_by_id.keys()) | set(broker_by_id.keys())

        for order_id in sorted(all_ids):
            local = local_by_id.get(order_id)
            broker = broker_by_id.get(order_id)

            if local and broker:
                diffs = self._compare_trades(local, broker)
                if not diffs:
                    result.matched.append(local)
                else:
                    result.mismatched.extend(diffs)
                    result.matched.append(local)
            elif local and not broker:
                result.local_only.append(local)
            elif not local and broker:
                result.broker_only.append(broker)

        result.reconciled = (
            len(result.local_only) == 0
            and len(result.broker_only) == 0
            and len(result.mismatched) == 0
        )

        parts: list[str] = []
        if result.matched:
            parts.append(f"{len(result.matched)} matched")
        if result.local_only:
            parts.append(f"{len(result.local_only)} local-only")
        if result.broker_only:
            parts.append(f"{len(result.broker_only)} broker-only")
        if result.mismatched:
            unresolved = [d for d in result.mismatched if not d.resolved]
            parts.append(f"{len(unresolved)} mismatched")
        result.summary = "; ".join(parts) if parts else "No trades"

        self._reconciliations.append(result)
        return result

    def _compare_trades(self, local: TradeRecord, broker: TradeRecord) -> list[TradeDiff]:
        diffs: list[TradeDiff] = []

        checks = [
            ("symbol", local.symbol, broker.symbol),
            ("side", local.side.value, broker.side.value),
            ("quantity", str(local.quantity), str(broker.quantity)),
            ("filled_quantity", str(local.filled_quantity), str(broker.filled_quantity)),
            ("average_price", str(local.average_price), str(broker.average_price)),
            ("status", local.status.value, broker.status.value),
        ]

        for field, lv, bv in checks:
            if lv != bv:
                diff = TradeDiff(
                    order_id=local.order_id,
                    field=field,
                    local_value=lv,
                    broker_value=bv,
                )
                if field == "average_price":
                    try:
                        ld = Decimal(lv)
                        bd = Decimal(bv)
                        if abs(ld - bd) <= self.tolerance:
                            diff.resolved = True
                            diff.resolution = "Within tolerance"
                    except Exception:
                        pass
                diffs.append(diff)

        return diffs

    def get_history(self) -> list[TradeReconciliationResult]:
        return list(self._reconciliations)

    def get_last(self) -> TradeReconciliationResult | None:
        return self._reconciliations[-1] if self._reconciliations else None
