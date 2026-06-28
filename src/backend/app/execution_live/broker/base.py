from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType = OrderType.MARKET
    limit_price: Decimal | None = None
    strategy_id: str | None = None
    client_order_id: str | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for LIMIT orders")


@dataclass
class OrderResult:
    broker_order_id: str
    client_order_id: str | None = None
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: Decimal = Decimal("0")
    filled_quantity: Decimal = Decimal("0")
    average_price: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.PENDING
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    commission: Decimal = Decimal("0")
    rejection_reason: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def fill_ratio(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0")
        return self.filled_quantity / self.quantity

    @property
    def notional(self) -> Decimal:
        return self.filled_quantity * self.average_price

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED


@dataclass
class BrokerPosition:
    symbol: str
    quantity: Decimal
    average_price: Decimal = Decimal("0")
    current_price: Decimal | None = None
    market_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None

    def __post_init__(self):
        if self.market_value is None and self.current_price is not None:
            self.market_value = self.quantity * self.current_price
        if self.unrealized_pnl is None and self.average_price > 0:
            current = self.current_price or self.average_price
            self.unrealized_pnl = self.quantity * (current - self.average_price)


@dataclass
class BrokerAccount:
    account_id: str
    cash: Decimal = Decimal("0")
    equity: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    currency: str = "CNY"

    @property
    def buying_power(self) -> Decimal:
        return self.cash - self.margin_used


class Broker(ABC):

    @abstractmethod
    def submit_order(self, request: OrderRequest) -> OrderResult:
        ...

    @abstractmethod
    def cancel_order(self, broker_order_id: str) -> OrderResult:
        ...

    @abstractmethod
    def get_order_status(self, broker_order_id: str) -> OrderResult:
        ...

    @abstractmethod
    def get_positions(self) -> list[BrokerPosition]:
        ...

    @abstractmethod
    def get_account(self) -> BrokerAccount:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...
