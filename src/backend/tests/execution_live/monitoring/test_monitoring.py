import pytest
from decimal import Decimal

from app.execution_live.monitoring.execution_logger import ExecutionLogger, LogLevel, LogEntry
from app.execution_live.monitoring.pnl_tracker import PnLTracker
from app.execution_live.monitoring.latency_monitor import LatencyMonitor


class TestExecutionLogger:
    def test_log_entry(self):
        logger = ExecutionLogger()
        logger.log(
            event="order_created",
            order_id="ORD-001",
            symbol="600000",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("50"),
        )
        assert logger.entry_count() == 1

    def test_log_multiple(self):
        logger = ExecutionLogger()
        for i in range(5):
            logger.log(event=f"test_{i}")
        assert logger.entry_count() == 5

    def test_get_entries_filtered(self):
        logger = ExecutionLogger()
        logger.log(event="order_created", level=LogLevel.INFO)
        logger.log(event="order_failed", level=LogLevel.ERROR)
        errors = logger.get_errors()
        assert len(errors) == 1
        assert errors[0].event == "order_failed"

    def test_get_recent(self):
        logger = ExecutionLogger()
        for i in range(100):
            logger.log(event=f"event_{i}")
        recent = logger.get_recent(limit=10)
        assert len(recent) == 10

    def test_log_order_created(self):
        logger = ExecutionLogger()
        logger.log_order_created("ORD-001", "600000", "buy", Decimal("100"))
        assert logger.entry_count() == 1

    def test_log_order_filled(self):
        logger = ExecutionLogger()
        logger.log_order_filled("ORD-001", Decimal("100"), Decimal("50"))
        entries = logger.get_entries()
        assert entries[0].event == "order_filled"
        assert entries[0].notional == "5000"

    def test_log_risk_violation(self):
        logger = ExecutionLogger()
        logger.log_risk_violation("Max position exceeded", symbol="600000")
        entries = logger.get_entries()
        assert entries[0].level == LogLevel.WARNING
        assert entries[0].event == "risk_violation"

    def test_log_kill_switch(self):
        logger = ExecutionLogger()
        logger.log_kill_switch("Daily loss limit hit")
        entries = logger.get_entries()
        assert entries[0].level == LogLevel.CRITICAL
        assert entries[0].event == "kill_switch_activated"

    def test_close(self):
        logger = ExecutionLogger()
        logger.close()


class TestPnLTracker:
    def test_initial_snapshot(self):
        tracker = PnLTracker(initial_equity=Decimal("1000000"))
        snap = tracker.snapshot(equity=Decimal("1000000"))
        assert snap.total_equity == Decimal("1000000")

    def test_record_trade_buy_profit(self):
        tracker = PnLTracker(initial_equity=Decimal("1000000"))
        tracker.record_trade(
            symbol="600000",
            side="sell",
            quantity=Decimal("100"),
            entry_price=Decimal("50"),
            exit_price=Decimal("55"),
        )
        stats = tracker.get_stats()
        assert Decimal(stats["total_realized_pnl"]) > Decimal("0")

    def test_record_trade_sell_loss(self):
        tracker = PnLTracker(initial_equity=Decimal("1000000"))
        tracker.record_trade(
            symbol="600000",
            side="buy",
            quantity=Decimal("100"),
            entry_price=Decimal("50"),
            exit_price=Decimal("55"),
        )
        stats = tracker.get_stats()
        assert Decimal(stats["total_realized_pnl"]) < Decimal("0")

    def test_record_realized_pnl(self):
        tracker = PnLTracker()
        tracker.record_realized_pnl(Decimal("5000"))
        stats = tracker.get_stats()
        assert Decimal(stats["total_realized_pnl"]) == Decimal("5000")
        assert stats["trade_count"] == 1
        assert stats["win_count"] == 1

    def test_multiple_snapshots(self):
        tracker = PnLTracker(initial_equity=Decimal("1000000"))
        tracker.snapshot(equity=Decimal("1000000"))
        tracker.snapshot(equity=Decimal("1010000"))
        tracker.snapshot(equity=Decimal("990000"))
        snapshots = tracker.get_snapshots()
        assert len(snapshots) == 3

    def test_trade_count(self):
        tracker = PnLTracker()
        tracker.record_trade("A", "sell", Decimal("100"), Decimal("50"), Decimal("55"))
        tracker.record_trade("B", "buy", Decimal("100"), Decimal("50"), Decimal("55"))
        stats = tracker.get_stats()
        assert stats["trade_count"] == 2
        assert stats["win_count"] == 1
        assert stats["loss_count"] == 1

    def test_reset(self):
        tracker = PnLTracker()
        tracker.record_realized_pnl(Decimal("5000"))
        tracker.reset()
        stats = tracker.get_stats()
        assert Decimal(stats["total_realized_pnl"]) == Decimal("0")
        assert stats["trade_count"] == 0


class TestLatencyMonitor:
    def test_record_latency(self):
        monitor = LatencyMonitor()
        monitor.record("order_submit", 50.5)
        stats = monitor.get_stats("order_submit")
        assert stats.count == 1
        assert stats.mean_ms == 50.5

    def test_start_end_event(self):
        import time

        monitor = LatencyMonitor()
        monitor.start_event("test_event")
        time.sleep(0.05)
        latency = monitor.end_event("test_event", event="test", order_id="ORD-001")
        assert latency > 0

    def test_get_stats_empty(self):
        monitor = LatencyMonitor()
        stats = monitor.get_stats()
        assert stats.count == 0

    def test_multiple_events(self):
        monitor = LatencyMonitor()
        for i in range(10):
            monitor.record("submit", float(i * 10))
        stats = monitor.get_stats("submit")
        assert stats.count == 10
        assert stats.mean_ms > 0

    def test_percentiles(self):
        monitor = LatencyMonitor()
        for i in range(100):
            monitor.record("submit", float(i))
        stats = monitor.get_stats("submit")
        assert stats.p95_ms > 0
        assert stats.median_ms > 0
        assert stats.min_ms == 0.0
        assert stats.max_ms == 99.0

    def test_clear(self):
        monitor = LatencyMonitor()
        monitor.record("submit", 100)
        monitor.clear()
        stats = monitor.get_stats()
        assert stats.count == 0
