from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

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


class BrokerMode(str, Enum):
    PAPER = "paper"
    REPLAY = "replay"
    LIVE = "live"
    SANDBOX = "sandbox"


class BrokerHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"


@dataclass
class AdapterConfig:
    mode: BrokerMode = BrokerMode.PAPER
    broker_name: str = ""
    account_id: str = ""
    connect_timeout_seconds: float = 10.0
    health_check_interval_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class HealthStatus:
    healthy: bool = True
    health: BrokerHealth = BrokerHealth.HEALTHY
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    message: str = ""


class BrokerAdapter(ABC):
    """Unified broker adapter abstraction.

    Wraps a concrete Broker implementation and adds:
    - Mode awareness (paper/replay/live/sandbox)
    - Connection lifecycle (connect/disconnect)
    - Health monitoring
    - Retry logic

    Strategy code depends on this abstraction, never on a concrete broker type.
    """

    def __init__(self, config: AdapterConfig | None = None):
        self.config = config or AdapterConfig()
        self._broker: Broker | None = None
        self._connected = False
        self._last_health: HealthStatus | None = None

    @property
    def mode(self) -> BrokerMode:
        return self.config.mode

    @property
    def broker(self) -> Broker | None:
        return self._broker

    def connect(self) -> bool:
        try:
            self._broker = self._create_broker()
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self):
        self._connected = False
        self._broker = None

    def is_connected(self) -> bool:
        if not self._connected or self._broker is None:
            return False
        return self._broker.is_connected()

    def check_health(self) -> HealthStatus:
        now = datetime.now(timezone.utc)
        errors: list[str] = []

        if not self.is_connected():
            self._last_health = HealthStatus(
                healthy=False,
                health=BrokerHealth.DISCONNECTED,
                last_check=now,
                errors=["Broker is not connected"],
                message="Disconnected",
            )
            return self._last_health

        try:
            account = self._broker.get_account()
            if account is None:
                errors.append("Failed to retrieve account")
        except Exception as e:
            errors.append(f"Account check failed: {e}")

        if errors:
            self._last_health = HealthStatus(
                healthy=False,
                health=BrokerHealth.UNHEALTHY,
                last_check=now,
                errors=errors,
                message="; ".join(errors),
            )
        else:
            self._last_health = HealthStatus(
                healthy=True,
                health=BrokerHealth.HEALTHY,
                last_check=now,
            )

        return self._last_health

    @property
    def last_health(self) -> HealthStatus | None:
        return self._last_health

    def submit_order(self, request: OrderRequest) -> OrderResult:
        if not self.is_connected():
            return OrderResult(
                broker_order_id="",
                client_order_id=request.client_order_id,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                status=OrderStatus.FAILED,
                rejection_reason="Broker not connected",
            )
        return self._broker.submit_order(request)

    def cancel_order(self, broker_order_id: str) -> OrderResult:
        if not self.is_connected():
            return OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="Broker not connected",
            )
        return self._broker.cancel_order(broker_order_id)

    def get_order_status(self, broker_order_id: str) -> OrderResult:
        if not self.is_connected():
            return OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="Broker not connected",
            )
        return self._broker.get_order_status(broker_order_id)

    def get_positions(self) -> list[BrokerPosition]:
        if not self.is_connected():
            return []
        return self._broker.get_positions()

    def get_account(self) -> BrokerAccount:
        if not self.is_connected():
            return BrokerAccount(account_id=self.config.account_id or "unknown")
        return self._broker.get_account()

    @abstractmethod
    def _create_broker(self) -> Broker:
        ...


class PaperAdapter(BrokerAdapter):
    """Adapter wrapping PaperBroker for simulation mode."""

    def __init__(
        self,
        config: AdapterConfig | None = None,
        initial_cash: Decimal = Decimal("1000000"),
        price_feed: dict[str, Decimal] | None = None,
        seed: int | None = 42,
    ):
        super().__init__(config or AdapterConfig(mode=BrokerMode.PAPER, broker_name="paper"))
        self._initial_cash = initial_cash
        self._price_feed = price_feed
        self._seed = seed

    def _create_broker(self) -> Broker:
        from app.execution_live.broker.paper_broker import PaperBroker, PaperBrokerConfig

        config = PaperBrokerConfig(
            initial_cash=self._initial_cash,
            seed=self._seed,
        )
        return PaperBroker(config=config, price_feed=self._price_feed)

    def set_price(self, symbol: str, price: Decimal):
        if isinstance(self._broker, object) and hasattr(self._broker, "set_price"):
            self._broker.set_price(symbol, price)

    def set_price_feed(self, feed: dict[str, Decimal]):
        if isinstance(self._broker, object) and hasattr(self._broker, "set_price_feed"):
            self._broker.set_price_feed(feed)
