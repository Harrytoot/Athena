import pytest
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
from app.execution_live.broker.mock_broker import MockBroker, MockBrokerConfig
from app.execution_live.broker.paper_broker import PaperBroker, PaperBrokerConfig


class TestOrderRequest:
    def test_market_order_defaults(self):
        req = OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        assert req.order_type == OrderType.MARKET
        assert req.limit_price is None

    def test_limit_order_requires_price(self):
        with pytest.raises(ValueError, match="limit_price is required"):
            OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"), order_type=OrderType.LIMIT)

    def test_limit_order_with_price(self):
        req = OrderRequest(
            symbol="600000",
            side=OrderSide.SELL,
            quantity=Decimal("200"),
            order_type=OrderType.LIMIT,
            limit_price=Decimal("50.00"),
        )
        assert req.limit_price == Decimal("50.00")


class TestOrderResult:
    def test_fill_ratio(self):
        result = OrderResult(
            broker_order_id="TEST-1",
            quantity=Decimal("100"),
            filled_quantity=Decimal("50"),
        )
        assert result.fill_ratio == Decimal("0.5")

    def test_fill_ratio_zero(self):
        result = OrderResult(
            broker_order_id="TEST-1",
            quantity=Decimal("0"),
            filled_quantity=Decimal("0"),
        )
        assert result.fill_ratio == Decimal("0")

    def test_is_filled(self):
        result = OrderResult(
            broker_order_id="TEST-1",
            status=OrderStatus.FILLED,
        )
        assert result.is_filled


class TestMockBroker:
    def test_submit_market_order(self):
        broker = MockBroker()
        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = broker.submit_order(req)
        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == Decimal("100")
        assert result.average_price == Decimal("100")

    def test_submit_rejected_symbol(self):
        broker = MockBroker()
        broker.reject_symbol("BLOCKED")
        req = OrderRequest(symbol="BLOCKED", side=OrderSide.BUY, quantity=Decimal("100"))
        result = broker.submit_order(req)
        assert result.status == OrderStatus.REJECTED

    def test_positions_updated(self):
        broker = MockBroker()
        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        broker.submit_order(req)
        positions = broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "TEST"
        assert positions[0].quantity == Decimal("100")

    def test_cancel_order(self):
        broker = MockBroker()
        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = broker.submit_order(req)
        cancelled = broker.cancel_order(result.broker_order_id)
        assert cancelled.status == OrderStatus.CANCELLED

    def test_disconnected_submit(self):
        broker = MockBroker()
        broker.set_connected(False)
        req = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100"))
        result = broker.submit_order(req)
        assert result.status == OrderStatus.FAILED

    def test_get_account(self):
        broker = MockBroker(config=MockBrokerConfig(initial_cash=Decimal("1000000")))
        account = broker.get_account()
        assert account.cash == Decimal("1000000")

    def test_sell_reduces_position(self):
        broker = MockBroker()
        broker.submit_order(OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=Decimal("100")))
        broker.submit_order(OrderRequest(symbol="TEST", side=OrderSide.SELL, quantity=Decimal("40")))
        positions = broker.get_positions()
        assert positions[0].quantity == Decimal("60")


class TestPaperBroker:
    @pytest.fixture
    def price_feed(self):
        return {
            "600000": Decimal("50.00"),
            "000001": Decimal("30.00"),
        }

    @pytest.fixture
    def paper_broker(self, price_feed):
        return PaperBroker(
            config=PaperBrokerConfig(seed=42, initial_cash=Decimal("1000000")),
            price_feed=price_feed,
        )

    def test_deterministic_fill(self, price_feed):
        broker1 = PaperBroker(
            config=PaperBrokerConfig(seed=42),
            price_feed=price_feed,
        )
        broker2 = PaperBroker(
            config=PaperBrokerConfig(seed=42),
            price_feed=price_feed,
        )
        req = OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        result1 = broker1.submit_order(req)
        result2 = broker2.submit_order(req)
        assert result1.status == result2.status
        assert result1.filled_quantity == result2.filled_quantity
        assert result1.average_price == result2.average_price

    def test_buy_updates_position(self, paper_broker):
        req = OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        paper_broker.submit_order(req)
        positions = paper_broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "600000"
        assert positions[0].quantity > Decimal("0")

    def test_missing_price_rejected(self):
        broker = PaperBroker(
            config=PaperBrokerConfig(seed=42),
            price_feed={},
        )
        req = OrderRequest(symbol="UNKNOWN", side=OrderSide.BUY, quantity=Decimal("100"))
        result = broker.submit_order(req)
        assert result.status == OrderStatus.REJECTED

    def test_trade_logging(self, paper_broker):
        req = OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        paper_broker.submit_order(req)
        log = paper_broker.get_trade_log()
        assert len(log) >= 2
        assert log[0]["event"] == "order_created"
        assert log[-1]["event"] == "order_executed"

    def test_account_updated(self, paper_broker):
        paper_broker.submit_order(
            OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        )
        account = paper_broker.get_account()
        assert account.cash < Decimal("1000000")

    def test_commission_applied(self, paper_broker):
        req = OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        result = paper_broker.submit_order(req)
        assert result.commission >= Decimal("5")

    def test_disconnected(self, paper_broker):
        paper_broker.set_connected(False)
        req = OrderRequest(symbol="600000", side=OrderSide.BUY, quantity=Decimal("100"))
        result = paper_broker.submit_order(req)
        assert result.status == OrderStatus.FAILED
