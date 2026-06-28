import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.broker_integration.adapters.base_adapter import (
    AdapterConfig,
    BrokerAdapter,
    BrokerMode,
    BrokerHealth,
    HealthStatus,
    PaperAdapter,
)
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


class TestBrokerMode:
    def test_modes(self):
        assert BrokerMode.PAPER == "paper"
        assert BrokerMode.REPLAY == "replay"
        assert BrokerMode.LIVE == "live"
        assert BrokerMode.SANDBOX == "sandbox"


class TestAdapterConfig:
    def test_defaults(self):
        cfg = AdapterConfig()
        assert cfg.mode == BrokerMode.PAPER
        assert cfg.broker_name == ""
        assert cfg.connect_timeout_seconds == 10.0
        assert cfg.max_retries == 3

    def test_custom(self):
        cfg = AdapterConfig(
            mode=BrokerMode.LIVE,
            broker_name="alpaca",
            max_retries=5,
        )
        assert cfg.mode == BrokerMode.LIVE
        assert cfg.broker_name == "alpaca"
        assert cfg.max_retries == 5


class TestHealthStatus:
    def test_healthy_default(self):
        h = HealthStatus()
        assert h.healthy
        assert h.health == BrokerHealth.HEALTHY

    def test_unhealthy(self):
        h = HealthStatus(healthy=False, health=BrokerHealth.DISCONNECTED, errors=["Connection refused"])
        assert not h.healthy
        assert h.health == BrokerHealth.DISCONNECTED
        assert len(h.errors) == 1


class TestPaperAdapter:
    def test_connect_and_disconnect(self):
        adapter = PaperAdapter(initial_cash=Decimal("500000"))
        assert not adapter.is_connected()

        adapter.connect()
        assert adapter.is_connected()
        assert adapter.broker is not None

        account = adapter.get_account()
        assert account.cash == Decimal("500000")

        adapter.disconnect()
        assert not adapter.is_connected()

    def test_submit_order_paper(self):
        adapter = PaperAdapter(
            initial_cash=Decimal("100000"),
            price_feed={"TEST": Decimal("50")},
        )
        adapter.connect()

        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = adapter.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_submit_order_disconnected(self):
        adapter = PaperAdapter()
        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = adapter.submit_order(req)
        assert result.status == OrderStatus.FAILED
        assert "not connected" in result.rejection_reason.lower()

    def test_get_positions(self):
        adapter = PaperAdapter(
            initial_cash=Decimal("100000"),
            price_feed={"TEST": Decimal("50")},
        )
        adapter.connect()
        adapter.submit_order(OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100")))

        positions = adapter.get_positions()
        assert len(positions) >= 1
        assert any(p.symbol == "TEST" for p in positions)

    def test_get_account(self):
        adapter = PaperAdapter(initial_cash=Decimal("123456"))
        adapter.connect()
        account = adapter.get_account()
        assert account.cash == Decimal("123456")

    def test_health_check_connected(self):
        adapter = PaperAdapter()
        adapter.connect()
        health = adapter.check_health()
        assert health.healthy
        assert health.health == BrokerHealth.HEALTHY

    def test_health_check_disconnected(self):
        adapter = PaperAdapter()
        health = adapter.check_health()
        assert not health.healthy
        assert health.health == BrokerHealth.DISCONNECTED

    def test_set_price(self):
        adapter = PaperAdapter(price_feed={"AAA": Decimal("10")})
        adapter.connect()
        adapter.set_price("AAA", Decimal("20"))
        assert adapter.broker._price_feed["AAA"] == Decimal("20")

    def test_mode(self):
        adapter = PaperAdapter()
        assert adapter.mode == BrokerMode.PAPER
