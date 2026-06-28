import pytest
from decimal import Decimal

from app.broker_integration.reconciliation.position_reconciler import (
    PositionReconciler,
    PositionDiffDetail,
    PositionDiffAction,
    PositionReconciliationResult,
)
from app.domain.entities.portfolio import Position
from app.execution_live.broker.base import BrokerPosition


def _make_position(symbol: str, shares: Decimal, cost_price: Decimal) -> Position:
    return Position(
        id=f"id-{symbol}",
        symbol=symbol,
        name=symbol,
        shares=shares,
        cost_price=cost_price,
        current_price=cost_price + Decimal("1"),
    )


def _make_broker_position(symbol: str, quantity: Decimal, avg_price: Decimal) -> BrokerPosition:
    return BrokerPosition(
        symbol=symbol,
        quantity=quantity,
        average_price=avg_price,
        current_price=avg_price + Decimal("1"),
    )


class TestPositionDiffDetail:
    def test_defaults(self):
        detail = PositionDiffDetail(symbol="TEST")
        assert detail.action == PositionDiffAction.NONE
        assert detail.quantity_delta == Decimal("0")


class TestPositionReconciler:
    def test_perfect_match(self):
        reconciler = PositionReconciler()
        local = [_make_position("A", Decimal("100"), Decimal("50"))]
        broker = [_make_broker_position("A", Decimal("100"), Decimal("50"))]

        result = reconciler.reconcile(local, broker)
        assert result.reconciled
        assert len(result.matched) == 1
        assert len(result.diffs) == 0

    def test_quantity_mismatch(self):
        reconciler = PositionReconciler()
        local = [_make_position("A", Decimal("100"), Decimal("50"))]
        broker = [_make_broker_position("A", Decimal("80"), Decimal("50"))]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.diffs) == 1
        assert result.diffs[0].action == PositionDiffAction.UPDATE_QUANTITY
        assert result.diffs[0].quantity_delta == Decimal("-20")

    def test_local_only(self):
        reconciler = PositionReconciler()
        local = [_make_position("A", Decimal("100"), Decimal("50"))]
        broker = []

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.diffs) == 1
        assert result.diffs[0].action == PositionDiffAction.ADD_LOCAL

    def test_broker_only(self):
        reconciler = PositionReconciler()
        local = []
        broker = [_make_broker_position("A", Decimal("100"), Decimal("50"))]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.diffs) == 1
        assert result.diffs[0].action == PositionDiffAction.ADD_BROKER

    def test_price_mismatch(self):
        reconciler = PositionReconciler()
        local = [_make_position("A", Decimal("100"), Decimal("50"))]
        broker = [_make_broker_position("A", Decimal("100"), Decimal("55"))]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert result.diffs[0].action == PositionDiffAction.UPDATE_PRICE

    def test_within_tolerance(self):
        reconciler = PositionReconciler(
            quantity_tolerance=Decimal("1"),
            price_tolerance=Decimal("1"),
        )
        local = [_make_position("A", Decimal("100"), Decimal("50"))]
        broker = [_make_broker_position("A", Decimal("100.5"), Decimal("50.5"))]

        result = reconciler.reconcile(local, broker)
        assert result.reconciled

    def test_multiple_symbols(self):
        reconciler = PositionReconciler()
        local = [
            _make_position("A", Decimal("100"), Decimal("50")),
            _make_position("B", Decimal("200"), Decimal("30")),
        ]
        broker = [
            _make_broker_position("A", Decimal("100"), Decimal("50")),
            _make_broker_position("B", Decimal("200"), Decimal("30")),
        ]

        result = reconciler.reconcile(local, broker)
        assert result.reconciled
        assert len(result.matched) == 2

    def test_mixed_scenario(self):
        reconciler = PositionReconciler()
        local = [
            _make_position("A", Decimal("100"), Decimal("50")),
            _make_position("B", Decimal("200"), Decimal("30")),
        ]
        broker = [
            _make_broker_position("A", Decimal("90"), Decimal("50")),
            _make_broker_position("C", Decimal("50"), Decimal("10")),
        ]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled
        assert len(result.diffs) == 3

    def test_resolve_diffs(self):
        reconciler = PositionReconciler()
        local = [_make_position("A", Decimal("100"), Decimal("50"))]
        broker = [_make_broker_position("A", Decimal("90"), Decimal("55"))]

        result = reconciler.reconcile(local, broker)
        assert not result.reconciled

        reconciler.resolve_diffs(result, resolve_to_broker=True)
        assert result.diffs[0].resolved
        assert result.diffs[0].local_quantity == Decimal("90")

    def test_history_and_last(self):
        reconciler = PositionReconciler()
        reconciler.reconcile(
            [_make_position("A", Decimal("100"), Decimal("50"))],
            [_make_broker_position("A", Decimal("100"), Decimal("50"))],
        )
        assert len(reconciler.get_history()) == 1
        assert reconciler.get_last() is not None
        assert reconciler.get_last().reconciled

    def test_summary(self):
        reconciler = PositionReconciler()
        result = reconciler.reconcile(
            [_make_position("A", Decimal("100"), Decimal("50"))],
            [_make_broker_position("A", Decimal("100"), Decimal("50"))],
        )
        assert "reconciled" in result.summary.lower()

    def test_has_breaks(self):
        reconciler = PositionReconciler()
        result = reconciler.reconcile(
            [_make_position("A", Decimal("100"), Decimal("50"))],
            [_make_broker_position("A", Decimal("90"), Decimal("50"))],
        )
        assert result.has_breaks
