from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from app.execution_live.broker.base import OrderRequest, OrderResult, OrderSide, OrderStatus, OrderType


class OrderLifecycle(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    RISK_CHECKED = "risk_checked"
    ROUTED = "routed"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class ManagedOrder:
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType = OrderType.MARKET
    limit_price: Decimal | None = None
    strategy_id: str | None = None
    lifecycle: OrderLifecycle = OrderLifecycle.CREATED
    broker_order_id: str | None = None
    filled_quantity: Decimal = Decimal("0")
    average_price: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rejection_reason: str | None = None
    metadata: dict = field(default_factory=dict)
    lifecycle_history: list[dict] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.lifecycle in (
            OrderLifecycle.CREATED,
            OrderLifecycle.VALIDATED,
            OrderLifecycle.RISK_CHECKED,
            OrderLifecycle.ROUTED,
            OrderLifecycle.SUBMITTED,
            OrderLifecycle.ACKNOWLEDGED,
            OrderLifecycle.PARTIALLY_FILLED,
        )

    @property
    def is_complete(self) -> bool:
        return self.lifecycle in (
            OrderLifecycle.FILLED,
            OrderLifecycle.CANCELLED,
            OrderLifecycle.REJECTED,
            OrderLifecycle.FAILED,
        )

    def transition(self, to_state: OrderLifecycle, reason: str | None = None):
        self.lifecycle = to_state
        self.updated_at = datetime.now(timezone.utc)
        entry = {
            "from": self.lifecycle_history[-1]["to"] if self.lifecycle_history else None,
            "to": to_state.value,
            "timestamp": self.updated_at.isoformat(),
        }
        if reason:
            entry["reason"] = reason
        self.lifecycle_history.append(entry)

    def apply_broker_result(self, result: OrderResult):
        self.broker_order_id = result.broker_order_id
        self.filled_quantity = result.filled_quantity
        self.average_price = result.average_price
        self.commission = result.commission

        status_map = {
            OrderStatus.FILLED: OrderLifecycle.FILLED,
            OrderStatus.PARTIALLY_FILLED: OrderLifecycle.PARTIALLY_FILLED,
            OrderStatus.CANCELLED: OrderLifecycle.CANCELLED,
            OrderStatus.REJECTED: OrderLifecycle.REJECTED,
            OrderStatus.FAILED: OrderLifecycle.FAILED,
        }
        self.lifecycle = status_map.get(result.status, OrderLifecycle.FAILED)
        self.rejection_reason = result.rejection_reason
        self.updated_at = datetime.now(timezone.utc)

    def to_request(self) -> OrderRequest:
        return OrderRequest(
            symbol=self.symbol,
            side=self.side,
            quantity=self.quantity,
            order_type=self.order_type,
            limit_price=self.limit_price,
            strategy_id=self.strategy_id,
            client_order_id=self.order_id,
            metadata=self.metadata,
        )


class OrderManager:

    def __init__(self):
        self._orders: dict[str, ManagedOrder] = {}
        self._order_history: list[ManagedOrder] = []

    def create_order(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Decimal | None = None,
        strategy_id: str | None = None,
        metadata: dict | None = None,
    ) -> ManagedOrder:
        order = ManagedOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            strategy_id=strategy_id,
            metadata=metadata or {},
        )
        order.transition(OrderLifecycle.CREATED)
        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> ManagedOrder | None:
        return self._orders.get(order_id)

    def get_active_orders(self) -> list[ManagedOrder]:
        return [o for o in self._orders.values() if o.is_active]

    def get_orders_by_strategy(self, strategy_id: str) -> list[ManagedOrder]:
        return [o for o in self._orders.values() if o.strategy_id == strategy_id]

    def get_all_orders(self) -> list[ManagedOrder]:
        return list(self._orders.values())

    def update_from_broker(self, order_id: str, result: OrderResult):
        order = self._orders.get(order_id)
        if order is None:
            return
        order.apply_broker_result(result)
        self._order_history.append(order)

    def cancel_order(self, order_id: str):
        order = self._orders.get(order_id)
        if order and order.is_active:
            order.transition(OrderLifecycle.CANCELLED, "Cancelled by user")

    def reject_order(self, order_id: str, reason: str):
        order = self._orders.get(order_id)
        if order and order.is_active:
            order.lifecycle = OrderLifecycle.REJECTED
            order.rejection_reason = reason
            order.updated_at = datetime.now(timezone.utc)
            order.transition(OrderLifecycle.REJECTED, reason)

    def get_order_count(self) -> int:
        return len(self._orders)

    def get_filled_count(self) -> int:
        return len([o for o in self._orders.values() if o.lifecycle == OrderLifecycle.FILLED])

    def get_rejected_count(self) -> int:
        return len([o for o in self._orders.values() if o.lifecycle == OrderLifecycle.REJECTED])

    def reset(self):
        self._orders.clear()
        self._order_history.clear()
