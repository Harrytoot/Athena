import pytest
from decimal import Decimal

from app.broker_integration.adapters.alpaca_adapter import AlpacaAdapter
from app.broker_integration.adapters.ibkr_adapter import IBKRAdapter
from app.broker_integration.adapters.binance_adapter import BinanceAdapter
from app.broker_integration.adapters.base_adapter import BrokerMode
from app.execution_live.broker.base import OrderRequest, OrderSide, OrderStatus


class TestAlpacaAdapter:
    def test_create_and_connect(self):
        adapter = AlpacaAdapter(api_key="test_key", secret_key="test_secret")
        adapter.connect()
        assert adapter.is_connected()

    def test_submit_order_works(self):
        adapter = AlpacaAdapter(initial_cash=Decimal("100000"), price_feed={"AAPL": Decimal("150")})
        adapter.connect()
        req = OrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=Decimal("10"))
        result = adapter.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_mode_is_sandbox_by_default(self):
        adapter = AlpacaAdapter()
        assert adapter.mode == BrokerMode.SANDBOX


class TestIBKRAdapter:
    def test_create_and_connect(self):
        adapter = IBKRAdapter(host="localhost", port=7497, client_id=1)
        adapter.connect()
        assert adapter.is_connected()

    def test_submit_order_works(self):
        adapter = IBKRAdapter(initial_cash=Decimal("100000"), price_feed={"SPY": Decimal("400")})
        adapter.connect()
        req = OrderRequest(symbol="SPY", side=OrderSide.SELL, quantity=Decimal("5"))
        result = adapter.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_mode_is_sandbox_by_default(self):
        adapter = IBKRAdapter()
        assert adapter.mode == BrokerMode.SANDBOX


class TestBinanceAdapter:
    def test_create_and_connect(self):
        adapter = BinanceAdapter(api_key="test_key", secret_key="test_secret")
        adapter.connect()
        assert adapter.is_connected()

    def test_submit_order_works(self):
        adapter = BinanceAdapter(initial_cash=Decimal("100000"), price_feed={"BTCUSDT": Decimal("50000")})
        adapter.connect()
        req = OrderRequest(symbol="BTCUSDT", side=OrderSide.BUY, quantity=Decimal("1"))
        result = adapter.submit_order(req)
        assert result.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)

    def test_mode_is_sandbox_by_default(self):
        adapter = BinanceAdapter()
        assert adapter.mode == BrokerMode.SANDBOX
