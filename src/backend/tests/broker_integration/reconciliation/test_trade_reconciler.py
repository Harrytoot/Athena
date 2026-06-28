import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.broker_integration.reconciliation.trade_reconciler import (
    TradeReconciler,
    TradeRecord,
    TradeDiff,
    TradeReconciliationResult,
)
from app.execution_live.broker.base import OrderSide, OrderStatus


def _make_record(
    order_id: str = "O-1",
    broker_order_id: str = "B-1",
    symbol: str = "TEST",
    side: OrderSide = OrderSide.BUY,
    quantity: Decimal = Decimal("100"),
    filled_quantity: Decimal = Decimal("100"),
    average_price: Decimal = Decimal("50"),
) -> TradeRecord:
    return TradeRecord(
        order_id=order_id,
        broker_order_id=broker_order_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        filled_quantity=filled_quantity,
        average_price=average_price,
        commission=Decimal("0"),
        status=OrderStatus.FILLED,
    )


class TestTradeRecord:
    def test_notional(self):
        record = _make_record(filled_quantity=Decimal("100"), average_price=Decimal("50"))
        assert record.notional == Decimal("5000")

    def test_from_order_result(self):
        from app.execution_live.broker.base import OrderResult

        result = OrderResult(
            broker_order_id="B-10",
            client_order_id="C-10",
            symbol="SPY",
            side=OrderSide.SELL,
            quantity=Decimal("200"),
            filled_quantity=Decimal("150"),
            average_price=Decimal("75"),
            status=OrderStatus.PARTIALLY_FILLED,
        )
        record = TradeRecord.from_order_result(result, strategy_id="ST-1")
        assert record.order_id == "C-10"
        assert record.strategy_id == "ST-1"
        assert record.filled_quantity == Decimal("150")


class TestTradeReconciler:
    def test_perfect_match(self):
        reconciler = TradeReconciler()
        local = [_make_record()]
        broker = [_make_record()]

        result = reconciler.reconcile(local, broker)
        assert result.reconciled
        assert len(result.matched) == 1
        assert len(result.local_only) == 0
        assert len(result.broker_only) == 0

    def test_local_only(self):
        reconciler = TradeReconciler()
        local = [_make_record(order_id="L1", broker_order_id="L1")]
        broker = []

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.local_only) == 1

    def test_broker_only(self):
        reconciler = TradeReconciler()
        local = []
        broker = [_make_record(order_id="B1", broker_order_id="B1")]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.broker_only) == 1

    def test_price_mismatch(self):
        reconciler = TradeReconciler()
        local = [_make_record(average_price=Decimal("50"))]
        broker = [_make_record(average_price=Decimal("51"))]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.mismatched) > 0

    def test_price_within_tolerance(self):
        reconciler = TradeReconciler(tolerance=Decimal("0.1"))
        local = [_make_record(average_price=Decimal("50.05"))]
        broker = [_make_record(average_price=Decimal("50.06"))]

        result = reconciler.reconcile(local, broker)
        assert len(result.mismatched) > 0
        assert result.mismatched[0].resolved

    def test_quantity_mismatch(self):
        reconciler = TradeReconciler()
        local = [_make_record(filled_quantity=Decimal("100"))]
        broker = [_make_record(filled_quantity=Decimal("50"))]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled

    def test_multiple_trades(self):
        reconciler = TradeReconciler()
        local = [
            _make_record(order_id="O1", broker_order_id="B1"),
            _make_record(order_id="O2", broker_order_id="B2", symbol="OTHER"),
        ]
        broker = [
            _make_record(order_id="O1", broker_order_id="B1"),
            _make_record(order_id="O2", broker_order_id="B2", symbol="OTHER"),
        ]

        result = reconciler.reconcile(local, broker)
        assert result.reconciled
        assert result.total_trades == 2

    def test_history(self):
        reconciler = TradeReconciler()
        reconciler.reconcile([_make_record()], [_make_record()])
        assert len(reconciler.get_history()) == 1
        assert reconciler.get_last() is not None

    def test_summary(self):
        reconciler = TradeReconciler()
        local = [_make_record(order_id="L1", broker_order_id="B-L1")]
        broker = [_make_record(order_id="B1", broker_order_id="B-B1")]

        result = reconciler.reconcile(local, broker)
        assert "local-only" in result.summary.lower()
        assert "broker-only" in result.summary.lower()


class TestTradeDiff:
    def test_has_difference(self):
        diff = TradeDiff(order_id="1", field="price", local_value="50", broker_value="51")
        assert diff.has_difference
        assert not diff.resolved

        diff2 = TradeDiff(order_id="1", field="price", local_value="50", broker_value="50")
        assert not diff2.has_difference
