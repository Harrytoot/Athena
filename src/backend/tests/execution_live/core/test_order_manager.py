import pytest
from decimal import Decimal

from app.execution_live.core.order_manager import OrderManager, OrderLifecycle
from app.execution_live.broker.base import (
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
)


class TestManagedOrder:
    def test_creation(self):
        mgr = OrderManager()
        order = mgr.create_order(
            order_id="ORD-001",
            symbol="600000",
            side=OrderSide.BUY,
            quantity=Decimal("100"),
        )
        assert order.order_id == "ORD-001"
        assert order.lifecycle == OrderLifecycle.CREATED
        assert order.is_active

    def test_transitions(self):
        mgr = OrderManager()
        order = mgr.create_order("ORD-001", "600000", OrderSide.BUY, Decimal("100"))
        order.transition(OrderLifecycle.VALIDATED)
        assert order.lifecycle == OrderLifecycle.VALIDATED

    def test_apply_broker_result_filled(self):
        mgr = OrderManager()
        order = mgr.create_order("ORD-001", "600000", OrderSide.BUY, Decimal("100"))
        result = OrderResult(
            broker_order_id="BRKR-1",
            symbol="600000",
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            filled_quantity=Decimal("100"),
            average_price=Decimal("50.00"),
            status=OrderStatus.FILLED,
        )
        order.apply_broker_result(result)
        assert order.lifecycle == OrderLifecycle.FILLED
        assert order.broker_order_id == "BRKR-1"
        assert order.filled_quantity == Decimal("100")
        assert order.average_price == Decimal("50.00")

    def test_apply_broker_result_rejected(self):
        mgr = OrderManager()
        order = mgr.create_order("ORD-001", "600000", OrderSide.BUY, Decimal("100"))
        result = OrderResult(
            broker_order_id="BRKR-1",
            status=OrderStatus.REJECTED,
            rejection_reason="Risk limit",
        )
        order.apply_broker_result(result)
        assert order.lifecycle == OrderLifecycle.REJECTED
        assert order.rejection_reason == "Risk limit"

    def test_is_complete(self):
        mgr = OrderManager()
        order = mgr.create_order("ORD-001", "600000", OrderSide.BUY, Decimal("100"))
        assert not order.is_complete
        order.transition(OrderLifecycle.FILLED)
        assert order.is_complete

    def test_to_request(self):
        mgr = OrderManager()
        order = mgr.create_order(
            order_id="ORD-001",
            symbol="600000",
            side=OrderSide.SELL,
            quantity=Decimal("200"),
            order_type=OrderType.LIMIT,
            limit_price=Decimal("55.00"),
            strategy_id="strat-1",
        )
        req = order.to_request()
        assert req.symbol == "600000"
        assert req.side == OrderSide.SELL
        assert req.quantity == Decimal("200")
        assert req.order_type == OrderType.LIMIT
        assert req.limit_price == Decimal("55.00")
        assert req.strategy_id == "strat-1"
        assert req.client_order_id == "ORD-001"


class TestOrderManager:
    def test_create_and_retrieve(self):
        mgr = OrderManager()
        mgr.create_order("ORD-001", "600000", OrderSide.BUY, Decimal("100"))
        order = mgr.get_order("ORD-001")
        assert order is not None
        assert order.symbol == "600000"

    def test_get_active_orders(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"))
        mgr.create_order("B", "S2", OrderSide.BUY, Decimal("100"))
        mgr.reject_order("B", "test")
        active = mgr.get_active_orders()
        assert len(active) == 1
        assert active[0].order_id == "A"

    def test_get_orders_by_strategy(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"), strategy_id="strat-A")
        mgr.create_order("B", "S2", OrderSide.BUY, Decimal("100"), strategy_id="strat-B")
        mgr.create_order("C", "S3", OrderSide.BUY, Decimal("100"), strategy_id="strat-A")
        orders = mgr.get_orders_by_strategy("strat-A")
        assert len(orders) == 2

    def test_cancel_order(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"))
        mgr.cancel_order("A")
        assert mgr.get_order("A").lifecycle == OrderLifecycle.CANCELLED

    def test_reject_order(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"))
        mgr.reject_order("A", "Risk limit exceeded")
        order = mgr.get_order("A")
        assert order.lifecycle == OrderLifecycle.REJECTED
        assert order.rejection_reason == "Risk limit exceeded"

    def test_counts(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"))
        mgr.create_order("B", "S2", OrderSide.SELL, Decimal("100"))
        mgr.reject_order("B", "test")

        assert mgr.get_order_count() == 2
        assert mgr.get_rejected_count() == 1

    def test_update_from_broker(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"))
        result = OrderResult(
            broker_order_id="B-1",
            status=OrderStatus.FILLED,
            filled_quantity=Decimal("100"),
            average_price=Decimal("50"),
            quantity=Decimal("100"),
            side=OrderSide.BUY,
            symbol="S1",
        )
        mgr.update_from_broker("A", result)
        order = mgr.get_order("A")
        assert order.lifecycle == OrderLifecycle.FILLED

    def test_reset(self):
        mgr = OrderManager()
        mgr.create_order("A", "S1", OrderSide.BUY, Decimal("100"))
        mgr.reset()
        assert mgr.get_order_count() == 0
