import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.portfolio import Portfolio, Position
from app.execution_live.broker.base import OrderRequest, OrderSide, OrderType


@dataclass
class RoutingConfig:
    max_slices: int = 5
    min_slice_notional: Decimal = Decimal("1000")
    prefer_limit_orders: bool = False
    market_order_timeout_seconds: int = 30


@dataclass
class RoutedOrder:
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    strategy_id: str | None = None
    parent_action: str | None = None
    slice_index: int = 0
    total_slices: int = 1
    metadata: dict = field(default_factory=dict)

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


class ExecutionRouter:

    def __init__(self, config: RoutingConfig | None = None):
        self.config = config or RoutingConfig()
        self._routed_count = 0

    def route_portfolio_positions(
        self,
        current_portfolio: Portfolio,
        target_positions: dict[str, Decimal],
        target_prices: dict[str, Decimal] | None = None,
    ) -> list[RoutedOrder]:
        if target_prices is None:
            target_prices = {}

        orders: list[RoutedOrder] = []
        current_map: dict[str, Decimal] = {}

        for pos in current_portfolio.positions:
            if pos.current_price is not None:
                current_map[pos.symbol] = pos.market_value
            else:
                current_map[pos.symbol] = Decimal("0")

        all_symbols = set(list(current_map.keys()) + list(target_positions.keys()))

        for symbol in all_symbols:
            current_value = current_map.get(symbol, Decimal("0"))
            target_value = target_positions.get(symbol, Decimal("0"))
            delta = target_value - current_value

            if abs(delta) < self.config.min_slice_notional:
                continue

            side = OrderSide.BUY if delta > 0 else OrderSide.SELL
            quantity = abs(delta)

            price = target_prices.get(symbol, Decimal("100"))

            sliced = self._slice_order(
                symbol=symbol,
                side=side,
                total_quantity=quantity,
                limit_price=price,
                parent_action="rebalance",
            )
            orders.extend(sliced)

        self._routed_count += len(orders)
        return orders

    def route_single_decision(
        self,
        symbol: str,
        side: OrderSide,
        target_notional: Decimal,
        reference_price: Decimal | None = None,
        strategy_id: str | None = None,
    ) -> list[RoutedOrder]:
        if abs(target_notional) < self.config.min_slice_notional:
            return []

        price = reference_price or Decimal("100")
        quantity = target_notional / price

        return self._slice_order(
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            limit_price=price,
            strategy_id=strategy_id,
            parent_action="single_decision",
        )

    def route_batch(
        self,
        decisions: list[dict],
    ) -> list[RoutedOrder]:
        all_orders: list[RoutedOrder] = []
        for decision in decisions:
            orders = self.route_single_decision(
                symbol=decision.get("symbol", ""),
                side=decision.get("side", OrderSide.BUY),
                target_notional=Decimal(str(decision.get("notional", "0"))),
                reference_price=Decimal(str(decision.get("price", "100"))),
                strategy_id=decision.get("strategy_id"),
            )
            all_orders.extend(orders)
        return all_orders

    def _slice_order(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: Decimal,
        limit_price: Decimal | None = None,
        strategy_id: str | None = None,
        parent_action: str | None = None,
    ) -> list[RoutedOrder]:
        slices = self.config.max_slices

        min_slice_qty = self.config.min_slice_notional / (limit_price or Decimal("1"))

        if total_quantity <= Decimal("0"):
            return []

        if total_quantity <= min_slice_qty * 2 or slices <= 1:
            order_type = OrderType.LIMIT if self.config.prefer_limit_orders else OrderType.MARKET
            order = RoutedOrder(
                order_id=f"RT-{uuid.uuid4().hex[:8]}",
                symbol=symbol,
                side=side,
                quantity=total_quantity,
                order_type=order_type,
                limit_price=limit_price if self.config.prefer_limit_orders else None,
                strategy_id=strategy_id,
                parent_action=parent_action,
                slice_index=0,
                total_slices=1,
            )
            return [order]

        slice_qty = total_quantity / Decimal(str(slices))
        if slice_qty < min_slice_qty:
            slice_qty = min_slice_qty
            slices = max(1, int(float(total_quantity / slice_qty)))

        orders: list[RoutedOrder] = []
        remaining = total_quantity
        for i in range(slices):
            if remaining <= 0:
                break
            qty = min(slice_qty, remaining)
            if i == slices - 1:
                qty = remaining

            order_type = OrderType.LIMIT if self.config.prefer_limit_orders else OrderType.MARKET
            orders.append(
                RoutedOrder(
                    order_id=f"RT-{uuid.uuid4().hex[:8]}",
                    symbol=symbol,
                    side=side,
                    quantity=qty,
                    order_type=order_type,
                    limit_price=limit_price if self.config.prefer_limit_orders else None,
                    strategy_id=strategy_id,
                    parent_action=parent_action,
                    slice_index=i,
                    total_slices=slices,
                )
            )
            remaining -= qty

        return orders

    @property
    def total_routed(self) -> int:
        return self._routed_count
