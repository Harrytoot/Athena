from datetime import datetime, timezone

import pytest

from app.execution.trade_scheduler import (
    LatencyConfig,
    TradeScheduler,
    ScheduleResult,
    ScheduledTrade,
    ExecutionDelay,
)


class TestTradeScheduler:

    def test_schedule_basic(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [
            ("s1", "buy", 100_000, 1000.0),
            ("s2", "sell", 50_000, 500.0),
        ]
        result = scheduler.schedule(trades)

        assert isinstance(result, ScheduleResult)
        assert result.trade_count == 2
        assert result.completed_count == 2
        assert result.avg_latency_ms > 0

    def test_schedule_empty_trades(self):
        scheduler = TradeScheduler()
        result = scheduler.schedule([])

        assert result.trade_count == 0
        assert result.avg_latency_ms == 0.0
        assert result.max_latency_ms == 0.0

    def test_all_trades_completed(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [
            ("s1", "buy", 100_000, 1000.0),
            ("s2", "buy", 200_000, 2000.0),
            ("s3", "sell", 150_000, 1500.0),
        ]
        result = scheduler.schedule(trades)

        assert result.completed_count == 3

    def test_delay_positive(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [("s1", "buy", 100_000, 1000.0)]
        result = scheduler.schedule(trades)

        delay = result.trades[0].delay
        assert delay is not None
        assert delay.delay_ms > 0
        assert delay.delay_seconds > 0

    def test_avg_and_max_latency(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [
            ("s1", "buy", 100_000, 1000.0),
            ("s2", "buy", 200_000, 2000.0),
        ]
        result = scheduler.schedule(trades)

        assert result.avg_latency_ms > 0
        assert result.max_latency_ms >= result.avg_latency_ms

    def test_custom_start_time(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        start = datetime(2025, 6, 26, 9, 30, 0, tzinfo=timezone.utc)
        trades = [("s1", "buy", 100_000, 1000.0)]
        result = scheduler.schedule(trades, start_time=start)

        executed = result.trades[0].executed_time
        assert executed is not None
        assert executed >= start

    def test_queue_depth(self):
        scheduler = TradeScheduler()
        assert scheduler.queue_depth() == 0

        scheduler.schedule([("s1", "buy", 100_000, 1000.0)])
        assert scheduler.queue_depth() == 0

    def test_deterministic_with_seed(self):
        config = LatencyConfig(seed=123)
        sched1 = TradeScheduler(config=config)
        sched2 = TradeScheduler(config=config)

        trades = [("s1", "buy", 100_000, 1000.0)]
        r1 = sched1.schedule(trades)
        r2 = sched2.schedule(trades)

        assert r1.avg_latency_ms == r2.avg_latency_ms
        assert r1.max_latency_ms == r2.max_latency_ms

    def test_scheduled_trade_status(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [("s1", "buy", 100_000, 1000.0)]
        result = scheduler.schedule(trades)

        trade = result.trades[0]
        assert trade.status == "completed"
        assert trade.is_completed

    def test_delay_type_variants(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [(f"s{i}", "buy", 100_000, 1000.0) for i in range(50)]
        result = scheduler.schedule(trades)

        delay_types = {t.delay.delay_type for t in result.trades if t.delay}
        assert "normal" in delay_types

    def test_total_execution_time(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [
            ("s1", "buy", 100_000, 1000.0),
            ("s2", "sell", 200_000, 2000.0),
        ]
        result = scheduler.schedule(trades)

        assert result.total_execution_time_ms > 0

    def test_scheduled_times_are_ordered(self):
        scheduler = TradeScheduler(config=LatencyConfig(seed=42))
        trades = [
            ("s1", "buy", 100_000, 1000.0),
            ("s2", "buy", 200_000, 2000.0),
            ("s3", "sell", 150_000, 1500.0),
        ]
        result = scheduler.schedule(trades)

        times = [t.scheduled_time for t in result.trades]
        for i in range(len(times) - 1):
            assert times[i] <= times[i + 1]
