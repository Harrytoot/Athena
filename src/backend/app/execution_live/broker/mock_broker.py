from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from app.execution_live.broker.base import (
    Broker,
    BrokerAccount,
    BrokerPosition,
    OrderRequest,
    OrderResult,
    OrderStatus,
)


@dataclass
class MockBrokerConfig:
    initial_cash: Decimal = Decimal("1000000")
    always_fill: bool = True
    fixed_price: Decimal = Decimal("100")
    auto_confirm: bool = True


class MockBroker(Broker):

    def __init__(self, config: MockBrokerConfig | None = None):
        self.config = config or MockBrokerConfig()
        self._orders: dict[str, OrderResult] = {}
        self._positions: dict[str, BrokerPosition] = {}
        self._account = BrokerAccount(
            account_id=f"mock-{uuid.uuid4().hex[:8]}",
            cash=self.config.initial_cash,
            equity=self.config.initial_cash,
        )
        self._counter = 0
        self._connected = True
        self._cancel_history: list[str] = []
        self._rejections: list[str] = []

    def submit_order(self, request: OrderRequest) -> OrderResult:
        self._counter += 1
        order_id = f"MOCK-{self._counter:06d}"
        now = datetime.now(timezone.utc)

        result = OrderResult(
            broker_order_id=order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            submitted_at=now,
        )

        if request.symbol in self._rejections:
            result.status = OrderStatus.REJECTED
            result.rejection_reason = f"Symbol {request.symbol} on rejection list"
            self._orders[order_id] = result
            return result

        if not self._connected:
            result.status = OrderStatus.FAILED
            self._orders[order_id] = result
            return result

        price = self.config.fixed_price
        if request.order_type == "limit" and request.limit_price is not None:
            price = request.limit_price

        if self.config.always_fill:
            result.status = OrderStatus.FILLED
            result.filled_quantity = request.quantity
            result.average_price = price
            result.filled_at = now
        else:
            half = request.quantity / Decimal("2")
            result.status = OrderStatus.PARTIALLY_FILLED
            result.filled_quantity = half
            result.average_price = price

        self._account.cash -= result.notional
        self._update_position(request.symbol, request.side, result.filled_quantity, price)
        self._account.equity = self._calculate_equity()

        self._orders[order_id] = result
        return result

    def cancel_order(self, broker_order_id: str) -> OrderResult:
        self._cancel_history.append(broker_order_id)
        if broker_order_id not in self._orders:
            return OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="Order not found",
            )
        order = self._orders[broker_order_id]
        order.status = OrderStatus.CANCELLED
        return order

    def get_order_status(self, broker_order_id: str) -> OrderResult:
        return self._orders.get(
            broker_order_id,
            OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="Order not found",
            ),
        )

    def get_positions(self) -> list[BrokerPosition]:
        return list(self._positions.values())

    def get_account(self) -> BrokerAccount:
        self._account.equity = self._calculate_equity()
        return self._account

    def is_connected(self) -> bool:
        return self._connected

    def set_connected(self, status: bool):
        self._connected = status

    def reject_symbol(self, symbol: str):
        if symbol not in self._rejections:
            self._rejections.append(symbol)

    def clear_rejections(self):
        self._rejections.clear()

    def _update_position(self, symbol: str, side, quantity: Decimal, price: Decimal):
        if symbol not in self._positions:
            self._positions[symbol] = BrokerPosition(
                symbol=symbol,
                quantity=Decimal("0"),
                average_price=Decimal("0"),
            )
        pos = self._positions[symbol]
        if side == "buy":
            total_cost = pos.quantity * pos.average_price + quantity * price
            pos.quantity += quantity
            pos.average_price = total_cost / pos.quantity if pos.quantity > 0 else Decimal("0")
        else:
            pos.quantity -= quantity
            if pos.quantity <= 0:
                del self._positions[symbol]

    def _calculate_equity(self) -> Decimal:
        pos_value = sum(
            p.quantity * (p.current_price or p.average_price)
            for p in self._positions.values()
        )
        return self._account.cash + pos_value
