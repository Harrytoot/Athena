import pytest
from decimal import Decimal

from app.broker_integration.adapters.base_adapter import (
    AdapterConfig,
    BrokerMode,
    PaperAdapter,
)
from app.broker_integration.gateway.broker_gateway import (
    BrokerGateway,
    GatewayConfig,
    GatewayMode,
    GatewayStatus,
)
from app.broker_integration.gateway.failover_router import FailoverState
from app.execution_live.broker.base import OrderRequest, OrderSide, OrderStatus


class TestGatewayConfig:
    def test_defaults(self):
        cfg = GatewayConfig()
        assert cfg.primary_mode == GatewayMode.PAPER
        assert cfg.enable_failover is True
        assert cfg.enable_health_monitoring is True


class TestGatewayMode:
    def test_modes(self):
        assert GatewayMode.PAPER == "paper"
        assert GatewayMode.REPLAY == "replay"
        assert GatewayMode.LIVE == "live"
        assert GatewayMode.HYBRID == "hybrid"


class TestBrokerGateway:
    def test_create_no_primary(self):
        gateway = BrokerGateway()
        assert gateway.active_adapter is None
        assert not gateway.is_connected()

    def test_set_primary(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter(initial_cash=Decimal("100000"))
        gateway.set_primary(adapter)
        assert gateway.is_connected()

    def test_submit_order_through_primary(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter(
            initial_cash=Decimal("100000"),
            price_feed={"TEST": Decimal("50")},
        )
        gateway.set_primary(adapter)

        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = gateway.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_submit_order_no_adapter(self):
        gateway = BrokerGateway()
        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = gateway.submit_order(req)
        assert result.status == OrderStatus.FAILED
        assert "No active broker adapter" in result.rejection_reason

    def test_get_positions(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter(
            initial_cash=Decimal("100000"),
            price_feed={"TEST": Decimal("50")},
        )
        gateway.set_primary(adapter)
        gateway.submit_order(OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100")))

        positions = gateway.get_positions()
        assert len(positions) >= 1

    def test_get_account(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter(initial_cash=Decimal("123456"))
        gateway.set_primary(adapter)

        account = gateway.get_account()
        assert account.cash == Decimal("123456")

    def test_get_account_no_adapter(self):
        gateway = BrokerGateway()
        account = gateway.get_account()
        assert account.account_id == "unknown"

    def test_get_status(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter()
        gateway.set_primary(adapter)

        status = gateway.get_status()
        assert isinstance(status, GatewayStatus)
        assert status.connected
        assert status.active_adapter == "paper"
        assert status.mode == GatewayMode.PAPER

    def test_set_fallback(self):
        gateway = BrokerGateway()
        primary = PaperAdapter(initial_cash=Decimal("100000"))
        fallback = PaperAdapter(initial_cash=Decimal("50000"))

        gateway.set_primary(primary)
        gateway.set_fallback(fallback)
        assert gateway.is_connected()

    def test_failover_to_paper_fallback(self):
        gateway = BrokerGateway()
        gateway.set_paper_fallback(initial_cash=Decimal("100000"))
        gateway._paper_fallback.set_price("TEST", Decimal("50"))

        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = gateway.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_cancel_order(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter(initial_cash=Decimal("100000"))
        gateway.set_primary(adapter)

        result = gateway.cancel_order("nonexistent")
        assert result.status == OrderStatus.FAILED

    def test_cancel_order_no_adapter(self):
        gateway = BrokerGateway()
        result = gateway.cancel_order("nonexistent")
        assert result.status == OrderStatus.FAILED

    def test_get_order_status(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter(initial_cash=Decimal("100000"))
        gateway.set_primary(adapter)

        result = gateway.get_order_status("nonexistent")
        assert result.status == OrderStatus.FAILED

    def test_failover_disabled(self):
        gateway = BrokerGateway(config=GatewayConfig(enable_failover=False))
        adapter = PaperAdapter(initial_cash=Decimal("100000"), price_feed={"TEST": Decimal("50")})
        gateway.set_primary(adapter)

        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = gateway.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_run_health_cycle(self):
        gateway = BrokerGateway()
        adapter = PaperAdapter()
        gateway.set_primary(adapter)
        gateway.run_health_cycle()

    def test_failover_history(self):
        gateway = BrokerGateway()
        history = gateway.get_failover_history()
        assert isinstance(history, list)

    def test_get_status_no_adapter(self):
        gateway = BrokerGateway()
        status = gateway.get_status()
        assert not status.connected
        assert status.active_adapter == "none"
