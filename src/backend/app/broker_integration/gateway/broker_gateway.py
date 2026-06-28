from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import logging

from app.broker_integration.adapters.base_adapter import (
    AdapterConfig,
    BrokerAdapter,
    BrokerMode,
    PaperAdapter,
)
from app.broker_integration.gateway.failover_router import (
    FailoverRouter,
    FailoverConfig,
    FailoverEvent,
    FailoverState,
)
from app.execution_live.broker.base import (
    BrokerAccount,
    BrokerPosition,
    OrderRequest,
    OrderResult,
    OrderStatus,
)


logger = logging.getLogger(__name__)


class GatewayMode(str, Enum):
    PAPER = "paper"
    REPLAY = "replay"
    LIVE = "live"
    HYBRID = "hybrid"


@dataclass
class GatewayConfig:
    primary_mode: GatewayMode = GatewayMode.PAPER
    failover: FailoverConfig = field(default_factory=FailoverConfig)
    enable_failover: bool = True
    enable_health_monitoring: bool = True
    default_initial_cash: Decimal = Decimal("1000000")


@dataclass
class GatewayStatus:
    mode: GatewayMode = GatewayMode.PAPER
    active_adapter: str = ""
    failover_state: FailoverState = FailoverState.PRIMARY
    connected: bool = False
    account: BrokerAccount | None = None
    positions_count: int = 0
    last_cycle: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: list[str] = field(default_factory=list)


class BrokerGateway:
    """Unified entry point for all broker operations.

    Abstracts broker mode (paper/replay/live) from the strategy layer.
    Routes orders to the appropriate adapter and handles failover
    automatically when the primary broker becomes unhealthy.

    Usage:
        gateway = BrokerGateway()
        gateway.set_primary(paper_adapter)
        gateway.set_fallback(alpaca_adapter)
        result = gateway.submit_order(request)
    """

    def __init__(self, config: GatewayConfig | None = None):
        self.config = config or GatewayConfig()
        self._primary: BrokerAdapter | None = None
        self._fallback: BrokerAdapter | None = None
        self._paper_fallback: PaperAdapter | None = None
        self._router = FailoverRouter(config=self.config.failover)
        self._cycle_count: int = 0

    def set_primary(self, adapter: BrokerAdapter):
        self._primary = adapter
        if not adapter.is_connected():
            adapter.connect()

    def set_fallback(self, adapter: BrokerAdapter):
        self._fallback = adapter
        if not adapter.is_connected():
            adapter.connect()

    def set_paper_fallback(self, initial_cash: Decimal | None = None):
        """Set up a paper broker as the ultimate fallback."""
        cash = initial_cash or self.config.default_initial_cash
        self._paper_fallback = PaperAdapter(initial_cash=cash)
        self._paper_fallback.connect()

    @property
    def active_adapter(self) -> BrokerAdapter | None:
        return self._resolve_active()

    @property
    def mode(self) -> GatewayMode:
        return self.config.primary_mode

    def _resolve_active(self) -> BrokerAdapter | None:
        if not self.config.enable_failover:
            return self._primary

        if self._primary and self._primary.is_connected():
            health = self._primary.check_health()
            if health.healthy:
                return self._primary

        if self._fallback and self._fallback.is_connected():
            health = self._fallback.check_health()
            if health.healthy:
                return self._fallback

        if self._paper_fallback and self._paper_fallback.is_connected():
            return self._paper_fallback

        return self._primary

    def submit_order(self, request: OrderRequest) -> OrderResult:
        adapter = self._resolve_active()
        if adapter is None:
            return OrderResult(
                broker_order_id="",
                client_order_id=request.client_order_id,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                status=OrderStatus.FAILED,
                rejection_reason="No active broker adapter",
            )

        result = adapter.submit_order(request)

        if result.status == OrderStatus.FAILED:
            self._router.record_failure()

            if self._router.should_failover():
                self._router.activate_failover()
                logger.warning(
                    "Failover activated: %s failures in window",
                    self._router.config.failure_threshold,
                )

                fallback = self._fallback or self._paper_fallback
                if fallback and fallback.is_connected():
                    return fallback.submit_order(request)

        else:
            self._router.record_success()

        return result

    def cancel_order(self, broker_order_id: str) -> OrderResult:
        adapter = self._resolve_active()
        if adapter is None:
            return OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="No active broker adapter",
            )
        return adapter.cancel_order(broker_order_id)

    def get_order_status(self, broker_order_id: str) -> OrderResult:
        adapter = self._resolve_active()
        if adapter is None:
            return OrderResult(
                broker_order_id=broker_order_id,
                status=OrderStatus.FAILED,
                rejection_reason="No active broker adapter",
            )
        return adapter.get_order_status(broker_order_id)

    def get_positions(self) -> list[BrokerPosition]:
        adapter = self._resolve_active()
        if adapter is None:
            return []
        return adapter.get_positions()

    def get_account(self) -> BrokerAccount:
        adapter = self._resolve_active()
        if adapter is None:
            return BrokerAccount(account_id="unknown")
        return adapter.get_account()

    def get_status(self) -> GatewayStatus:
        adapter = self._resolve_active()
        connected = adapter.is_connected() if adapter else False
        account = adapter.get_account() if adapter else None
        positions = adapter.get_positions() if adapter else []

        return GatewayStatus(
            mode=self.config.primary_mode,
            active_adapter=adapter.config.broker_name if adapter else "none",
            failover_state=self._router.state,
            connected=connected,
            account=account,
            positions_count=len(positions),
            last_cycle=datetime.now(timezone.utc),
        )

    def run_health_cycle(self):
        """Run one health monitoring cycle."""
        self._cycle_count += 1

        if not self.config.enable_health_monitoring:
            return

        adapters = [a for a in [self._primary, self._fallback, self._paper_fallback] if a is not None]
        for adapter in adapters:
            adapter.check_health()

        if self._router.state == FailoverState.FAILOVER:
            if self._primary and self._primary.is_connected():
                health = self._primary.check_health()
                if health.healthy:
                    if self._router.should_restore():
                        self._router.restore_primary()
                        logger.info("Primary restored after recovery")

    def get_failover_history(self) -> list[FailoverEvent]:
        return self._router.get_history()

    def is_connected(self) -> bool:
        adapter = self._resolve_active()
        return adapter is not None and adapter.is_connected()
