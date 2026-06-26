import random
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Order:
    strategy_id: str
    side: str
    quantity: float
    limit_price: float | None = None
    order_id: str = ""

    @property
    def is_buy(self) -> bool:
        return self.side == "buy"

    @property
    def is_sell(self) -> bool:
        return self.side == "sell"


@dataclass
class FillResult:
    order_id: str
    strategy_id: str
    side: str
    requested_quantity: float
    filled_quantity: float
    fill_ratio: float
    average_price: float
    execution_timestamp: datetime
    partial_fill: bool = False

    @property
    def is_complete(self) -> bool:
        return self.fill_ratio >= 0.999


@dataclass
class OrderBookConfig:
    fill_probability: float = 0.85
    partial_fill_threshold: float = 0.3
    min_fill_ratio: float = 0.1
    price_improvement_chance: float = 0.15
    seed: int | None = None


class OrderBookSimulator:

    def __init__(self, config: OrderBookConfig | None = None):
        self.config = config or OrderBookConfig()
        self._rng = random.Random(self.config.seed)

    def simulate_fill(
        self,
        order: Order,
        reference_price: float,
        available_liquidity: float,
        daily_volume: float,
        liquidity_profile: any = None,
    ) -> FillResult:
        if available_liquidity <= 0 or daily_volume <= 0:
            return FillResult(
                order_id=order.order_id,
                strategy_id=order.strategy_id,
                side=order.side,
                requested_quantity=round(order.quantity, 6),
                filled_quantity=0.0,
                fill_ratio=0.0,
                average_price=reference_price,
                execution_timestamp=datetime.now(),
                partial_fill=True,
            )

        participation_rate = order.quantity / daily_volume if daily_volume > 0 else 0.0

        base_fill_prob = self.config.fill_probability
        if participation_rate > 0.1:
            base_fill_prob -= participation_rate * 0.5
        base_fill_prob = max(0.1, base_fill_prob)

        fill_success = self._rng.random() < base_fill_prob

        if not fill_success:
            partial_ratio = self._rng.uniform(
                self.config.min_fill_ratio, self.config.partial_fill_threshold
            )
            filled_qty = order.quantity * partial_ratio
            filled_qty = min(filled_qty, available_liquidity)
            is_partial = True
        else:
            can_fill_all = self._rng.random() < 0.7
            if can_fill_all:
                filled_qty = min(order.quantity, available_liquidity)
                is_partial = filled_qty < order.quantity - 1e-8
            else:
                filled_qty = order.quantity * self._rng.uniform(0.6, 0.95)
                filled_qty = min(filled_qty, available_liquidity)
                is_partial = True

        fill_ratio = filled_qty / order.quantity if order.quantity > 0 else 0.0

        execution_price = self._compute_execution_price(
            reference_price, order.side, fill_ratio, participation_rate
        )

        return FillResult(
            order_id=order.order_id,
            strategy_id=order.strategy_id,
            side=order.side,
            requested_quantity=round(order.quantity, 6),
            filled_quantity=round(filled_qty, 6),
            fill_ratio=round(fill_ratio, 6),
            average_price=round(execution_price, 4),
            execution_timestamp=datetime.now(),
            partial_fill=is_partial,
        )

    def _compute_execution_price(
        self,
        reference_price: float,
        side: str,
        fill_ratio: float,
        participation_rate: float,
    ) -> float:
        price = reference_price

        if fill_ratio < 1.0:
            penalty = (1.0 - fill_ratio) * 0.002
            price = price * (1.0 + penalty) if side == "buy" else price * (1.0 - penalty)

        if participation_rate > 0.05:
            impact_factor = participation_rate * 0.1
            price = price * (1.0 + impact_factor) if side == "buy" else price * (1.0 - impact_factor)

        if self._rng.random() < self.config.price_improvement_chance:
            improvement = self._rng.uniform(0.0001, 0.0005)
            price = price * (1.0 - improvement) if side == "buy" else price * (1.0 + improvement)

        return price

    def compute_notional(
        self,
        fill_result: FillResult,
    ) -> float:
        return round(fill_result.filled_quantity * fill_result.average_price, 2)

    def reset_seed(self, seed: int):
        self._rng = random.Random(seed)
