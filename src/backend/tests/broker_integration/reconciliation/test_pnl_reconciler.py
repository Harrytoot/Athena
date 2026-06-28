import pytest
from decimal import Decimal

from app.broker_integration.reconciliation.pnl_reconciler import (
    PnLReconciler,
    PnLSnapshot,
    PnLReconciliationResult,
)


class TestPnLSnapshot:
    def test_equity_drift(self):
        snap = PnLSnapshot(
            timestamp=None,
            local_equity=Decimal("1050"),
            broker_equity=Decimal("1000"),
        )
        assert snap.equity_drift == Decimal("50")
        assert snap.equity_drift_pct == Decimal("5")

    def test_no_drift(self):
        snap = PnLSnapshot(
            timestamp=None,
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
        )
        assert snap.equity_drift == Decimal("0")

    def test_zero_broker_equity(self):
        snap = PnLSnapshot(
            timestamp=None,
            local_equity=Decimal("100"),
            broker_equity=Decimal("0"),
        )
        assert snap.equity_drift_pct == Decimal("0")

    def test_total_pnl_drift(self):
        snap = PnLSnapshot(
            timestamp=None,
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
            local_realized_pnl=Decimal("100"),
            broker_realized_pnl=Decimal("90"),
            local_unrealized_pnl=Decimal("20"),
            broker_unrealized_pnl=Decimal("15"),
        )
        assert snap.total_pnl_drift == Decimal("15")

    def test_cash_and_positions_drift(self):
        snap = PnLSnapshot(
            timestamp=None,
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
            local_cash=Decimal("500"),
            broker_cash=Decimal("480"),
            local_positions_value=Decimal("500"),
            broker_positions_value=Decimal("520"),
        )
        assert snap.cash_drift == Decimal("20")
        assert snap.positions_value_drift == Decimal("-20")


class TestPnLReconciler:
    def test_empty_reconcile(self):
        reconciler = PnLReconciler()
        result = reconciler.reconcile()
        assert result.reconciled
        assert "No snapshots" in result.summary

    def test_perfect_reconcile(self):
        reconciler = PnLReconciler()
        reconciler.record_snapshot(
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
        )
        reconciler.record_snapshot(
            local_equity=Decimal("1050"),
            broker_equity=Decimal("1050"),
        )

        result = reconciler.reconcile()
        assert result.reconciled

    def test_drift_detection(self):
        reconciler = PnLReconciler(drift_threshold_pct=Decimal("0.5"))
        reconciler.record_snapshot(
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
        )
        reconciler.record_snapshot(
            local_equity=Decimal("1050"),
            broker_equity=Decimal("1000"),
        )

        result = reconciler.reconcile()
        assert not result.reconciled
        assert result.break_count > 0
        assert result.max_drift_pct > Decimal("0.5")

    def test_small_drift_within_threshold(self):
        reconciler = PnLReconciler(drift_threshold_pct=Decimal("5"))
        reconciler.record_snapshot(
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
        )
        reconciler.record_snapshot(
            local_equity=Decimal("1010"),
            broker_equity=Decimal("1000"),
        )

        result = reconciler.reconcile()
        assert result.reconciled

    def test_drift_trend(self):
        reconciler = PnLReconciler()
        for i in range(5):
            reconciler.record_snapshot(
                local_equity=Decimal(1000 + i * 10),
                broker_equity=Decimal("1000"),
            )

        trend = reconciler.get_drift_trend()
        assert len(trend) == 5
        assert trend[0] == Decimal("0")
        assert trend[-1] > trend[0]

    def test_drift_pct_trend(self):
        reconciler = PnLReconciler()
        reconciler.record_snapshot(
            local_equity=Decimal("1050"),
            broker_equity=Decimal("1000"),
        )
        reconciler.record_snapshot(
            local_equity=Decimal("1100"),
            broker_equity=Decimal("1000"),
        )

        trend = reconciler.get_drift_pct_trend()
        assert len(trend) == 2
        assert trend[1] > Decimal("8")

    def test_history(self):
        reconciler = PnLReconciler()
        reconciler.record_snapshot(
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
        )
        reconciler.reconcile()

        assert len(reconciler.get_history()) == 1

    def test_is_acceptable(self):
        reconciler = PnLReconciler()
        reconciler.record_snapshot(
            local_equity=Decimal("1005"),
            broker_equity=Decimal("1000"),
        )
        result = reconciler.reconcile()
        assert result.is_acceptable

    def test_is_not_acceptable(self):
        reconciler = PnLReconciler()
        reconciler.record_snapshot(
            local_equity=Decimal("1100"),
            broker_equity=Decimal("1000"),
        )
        result = reconciler.reconcile()
        assert result.is_acceptable is False

    def test_reset(self):
        reconciler = PnLReconciler()
        reconciler.record_snapshot(
            local_equity=Decimal("1000"),
            broker_equity=Decimal("1000"),
        )
        reconciler.reconcile()

        reconciler.reset()
        result = reconciler.reconcile()
        assert result.reconciled
        assert "No snapshots" in result.summary
