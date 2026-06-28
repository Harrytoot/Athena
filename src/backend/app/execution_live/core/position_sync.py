from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from app.domain.entities.portfolio import Portfolio, Position
from app.execution_live.broker.base import Broker, BrokerPosition


class SyncAction(str, Enum):
    NONE = "none"
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"


@dataclass
class PositionDiff:
    symbol: str
    local_quantity: Decimal = Decimal("0")
    broker_quantity: Decimal = Decimal("0")
    local_cost: Decimal = Decimal("0")
    broker_cost: Decimal = Decimal("0")
    action: SyncAction = SyncAction.NONE
    delta_quantity: Decimal = Decimal("0")
    delta_cost: Decimal = Decimal("0")


@dataclass
class SyncResult:
    diffs: list[PositionDiff] = field(default_factory=list)
    reconciled: bool = True
    errors: list[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_changes(self) -> bool:
        return any(d.action != SyncAction.NONE for d in self.diffs)

    @property
    def change_count(self) -> int:
        return len([d for d in self.diffs if d.action != SyncAction.NONE])


class PositionSync:

    def __init__(self, tolerance: Decimal = Decimal("0.0001")):
        self.tolerance = tolerance
        self._last_sync: SyncResult | None = None

    def reconcile(
        self,
        local_portfolio: Portfolio,
        broker_positions: list[BrokerPosition],
    ) -> SyncResult:
        result = SyncResult()

        local_positions: dict[str, Position] = {}
        for p in local_portfolio.positions:
            local_positions[p.symbol] = p

        broker_positions_map: dict[str, BrokerPosition] = {}
        for bp in broker_positions:
            broker_positions_map[bp.symbol] = bp

        all_symbols = set(list(local_positions.keys()) + list(broker_positions_map.keys()))

        for symbol in all_symbols:
            local = local_positions.get(symbol)
            broker = broker_positions_map.get(symbol)

            local_qty = local.shares if local else Decimal("0")
            local_cost = local.cost_price if local else Decimal("0")
            broker_qty = broker.quantity if broker else Decimal("0")
            broker_cost = broker.average_price if broker else Decimal("0")

            diff = PositionDiff(
                symbol=symbol,
                local_quantity=local_qty,
                broker_quantity=broker_qty,
                local_cost=local_cost,
                broker_cost=broker_cost,
            )

            if local and broker:
                qty_diff = abs(local_qty - broker_qty)
                cost_diff = abs(local_cost - broker_cost)
                if qty_diff > self.tolerance or cost_diff > self.tolerance:
                    diff.action = SyncAction.UPDATE
                    diff.delta_quantity = broker_qty - local_qty
                    diff.delta_cost = broker_cost - local_cost
            elif local and not broker:
                diff.action = SyncAction.REMOVE
                diff.delta_quantity = -local_qty
            elif not local and broker:
                diff.action = SyncAction.ADD
                diff.delta_quantity = broker_qty
                diff.delta_cost = broker_cost

            if diff.action != SyncAction.NONE:
                result.diffs.append(diff)

        result.reconciled = len(result.diffs) == 0
        result.synced_at = datetime.now(timezone.utc)
        self._last_sync = result

        return result

    def apply_sync(
        self,
        portfolio: Portfolio,
        sync_result: SyncResult,
    ) -> Portfolio:
        for diff in sync_result.diffs:
            if diff.action == SyncAction.ADD:
                portfolio.add_position(
                    Position(
                        symbol=diff.symbol,
                        shares=diff.broker_quantity,
                        cost_price=diff.broker_cost,
                    )
                )
            elif diff.action == SyncAction.REMOVE:
                for pos in portfolio.positions:
                    if pos.symbol == diff.symbol:
                        portfolio.remove_position(pos.id or "")
                        break
            elif diff.action == SyncAction.UPDATE:
                for pos in portfolio.positions:
                    if pos.symbol == diff.symbol:
                        pos.shares = diff.broker_quantity
                        pos.cost_price = diff.broker_cost
                        break

        return portfolio

    @property
    def last_sync(self) -> SyncResult | None:
        return self._last_sync
