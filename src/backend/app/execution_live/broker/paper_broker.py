import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.execution_live.broker.base import (
    Broker,
    BrokerAccount,
    BrokerPosition,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
)


@dataclass
class PaperBrokerConfig:
    initial_cash: Decimal = Decimal("1000000")
    commission_rate: Decimal = Decimal("0.0003")
    min_commission: Decimal = Decimal("5")
    slippage_bps: Decimal = Decimal("2")
    fill_probability: float = 1.0
    partial_fill_probability: float = 0.05
    min_fill_ratio: float = 0.5
    seed: int | None = 42
    latency_ms_mean: float = 50.0
    latency_ms_std: float = 10.0


class PaperBroker(Broker):

    def __init__(
        self,
        config: PaperBrokerConfig | None = None,
        price_feed: dict[str, Decimal] | None = None,
    ):
        self.config = config or PaperBrokerConfig()
        self._price_feed = price_feed or {}
        self._rng = random.Random(self.config.seed)
        self._orders: dict[str, OrderResult] = {}
        self._positions: dict[str, BrokerPosition] = {}
        self._account = BrokerAccount(
            account_id=f"paper-{uuid.uuid4().hex[:8]}",
            cash=self.config.initial_cash,
            equity=self.config.initial_cash,
        )
        self._order_counter = 0
        self._connected = True
        self._trade_log: list[dict] = []

    def submit_order(self, request: OrderRequest) -> OrderResult:
        self._order_counter += 1
        broker_order_id = f"PAPER-{self._order_counter:06d}"
        now = datetime.now(timezone.utc)

        self._log_trade("order_created", {
            "broker_order_id": broker_order_id,
            "symbol": request.symbol,
            "side": request.side.value,
            "quantity": str(request.quantity),
            "order_type": request.order_type.value,
            "strategy_id": request.strategy_id,
        })

        current_price = self._get_price(request.symbol)

        result = OrderResult(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            status=OrderStatus.SUBMITTED,
            submitted_at=now,
        )

        if not self._connected:
            result.status = OrderStatus.FAILED
            result.rejection_reason = "Broker disconnected"
            self._orders[broker_order_id] = result
            self._log_trade("order_failed", {"broker_order_id": broker_order_id, "reason": "Broker disconnected"})
            return result

        price, filled_qty, fill_status = self._simulate_fill(request, current_price)

        if fill_status == OrderStatus.REJECTED:
            result.status = OrderStatus.REJECTED
            result.rejection_reason = "Risk limit exceeded"
            self._orders[broker_order_id] = result
            self._log_trade("order_rejected", {"broker_order_id": broker_order_id, "reason": result.rejection_reason})
            return result

        commission = self._calculate_commission(filled_qty, price)

        executed_price = self._apply_slippage(price, request.side)
        result.filled_quantity = filled_qty
        result.average_price = executed_price
        result.commission = commission
        result.status = fill_status
        if fill_status == OrderStatus.FILLED:
            result.filled_at = now

        self._account.cash -= result.notional
        self._account.cash -= commission

        if fill_status == OrderStatus.FILLED or fill_status == OrderStatus.PARTIALLY_FILLED:
            self._update_position(request.symbol, request.side, filled_qty, executed_price)

        self._account.equity = self._calculate_equity()

        self._orders[broker_order_id] = result
        self._log_trade("order_executed", {
            "broker_order_id": broker_order_id,
            "filled_quantity": str(filled_qty),
            "average_price": str(executed_price),
            "commission": str(commission),
            "status": fill_status.value,
        })

        return result

    def cancel_order(self, broker_order_id: str) -> OrderResult:
        if broker_order_id not in self._orders:
            return OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="Order not found",
            )

        order = self._orders[broker_order_id]
        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
            return order

        order.status = OrderStatus.CANCELLED
        self._log_trade("order_cancelled", {"broker_order_id": broker_order_id})
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
        positions = []
        for symbol, pos in self._positions.items():
            current_price = self._get_price(symbol)
            pos.current_price = current_price
            if pos.market_value is None and current_price is not None:
                pos.market_value = pos.quantity * current_price
            if current_price is not None:
                pos.unrealized_pnl = pos.quantity * (current_price - pos.average_price)
            positions.append(pos)
        return positions

    def get_account(self) -> BrokerAccount:
        self._account.equity = self._calculate_equity()
        return self._account

    def is_connected(self) -> bool:
        return self._connected

    def set_connected(self, status: bool):
        self._connected = status

    def set_price(self, symbol: str, price: Decimal):
        self._price_feed[symbol] = price

    def set_price_feed(self, feed: dict[str, Decimal]):
        self._price_feed = feed

    def get_trade_log(self) -> list[dict]:
        return list(self._trade_log)

    def _simulate_fill(
        self,
        request: OrderRequest,
        current_price: Decimal | None,
    ) -> tuple[Decimal, Decimal, OrderStatus]:
        """Deterministic fill simulation based on seeded RNG."""
        if current_price is None or current_price <= 0:
            return Decimal("0"), Decimal("0"), OrderStatus.REJECTED

        fill_roll = self._rng.random()

        if fill_roll > self.config.fill_probability:
            return current_price, Decimal("0"), OrderStatus.REJECTED

        quantity = request.quantity

        partial_roll = self._rng.random()
        if partial_roll < self.config.partial_fill_probability:
            ratio = self.config.min_fill_ratio + self._rng.random() * (1.0 - self.config.min_fill_ratio)
            filled_qty = Decimal(str(round(float(quantity) * ratio, 8)))
            status = OrderStatus.PARTIALLY_FILLED
        else:
            filled_qty = quantity
            status = OrderStatus.FILLED

        return current_price, filled_qty, status

    def _apply_slippage(self, price: Decimal, side: OrderSide) -> Decimal:
        slippage_factor = self.config.slippage_bps / Decimal("10000")
        if side == OrderSide.BUY:
            return price * (Decimal("1") + slippage_factor)
        else:
            return price * (Decimal("1") - slippage_factor)

    def _calculate_commission(self, quantity: Decimal, price: Decimal) -> Decimal:
        notional = quantity * price
        commission = notional * self.config.commission_rate
        return max(commission, self.config.min_commission)

    def _update_position(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
    ):
        if symbol not in self._positions:
            self._positions[symbol] = BrokerPosition(
                symbol=symbol,
                quantity=Decimal("0"),
                average_price=Decimal("0"),
            )

        pos = self._positions[symbol]

        if side == OrderSide.BUY:
            total_cost = pos.quantity * pos.average_price + quantity * price
            pos.quantity += quantity
            pos.average_price = total_cost / pos.quantity if pos.quantity > 0 else Decimal("0")
        else:
            if pos.quantity > quantity:
                pos.quantity -= quantity
            else:
                del self._positions[symbol]

        pos.current_price = self._get_price(symbol)

    def _get_price(self, symbol: str) -> Decimal | None:
        return self._price_feed.get(symbol)

    def _calculate_equity(self) -> Decimal:
        position_value = Decimal("0")
        for symbol, pos in self._positions.items():
            price = self._get_price(symbol)
            if price is not None:
                position_value += pos.quantity * price
        return self._account.cash + position_value

    def _log_trade(self, event: str, data: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **data,
        }
        self._trade_log.append(entry)
