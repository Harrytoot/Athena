import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ingestion.realtime.intraday_scheduler import IntradayScheduler
from app.ingestion.realtime.trading_calendar import TradingCalendar


class TestIntradayScheduler:

    @pytest.fixture
    def mock_pipeline(self):
        pipeline = MagicMock()
        pipeline.run_cycle = AsyncMock(
            return_value={"status": "ok", "cycle": 1, "features_written": 4}
        )
        return pipeline

    @pytest.fixture
    def open_calendar(self):
        cal = MagicMock(spec=TradingCalendar)
        cal.session_phase.return_value = "open_morning"
        return cal

    @pytest.fixture
    def closed_calendar(self):
        cal = MagicMock(spec=TradingCalendar)
        cal.session_phase.return_value = "closed"
        return cal

    @pytest.mark.asyncio
    async def test_scheduler_starts_and_stops(self, mock_pipeline, open_calendar):
        scheduler = IntradayScheduler(
            pipeline=mock_pipeline,
            calendar=open_calendar,
            tick_interval=1,
        )
        await scheduler.start()
        assert scheduler.is_running is True

        await asyncio.sleep(0.1)
        await scheduler.stop()
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_scheduler_runs_cycle_during_open(self, mock_pipeline, open_calendar):
        scheduler = IntradayScheduler(
            pipeline=mock_pipeline,
            calendar=open_calendar,
            tick_interval=1,
        )
        await scheduler.start()
        await asyncio.sleep(1.5)
        await scheduler.stop()

        assert scheduler.tick_count >= 1

    @pytest.mark.asyncio
    async def test_scheduler_pauses_outside_trading(self, mock_pipeline, closed_calendar):
        scheduler = IntradayScheduler(
            pipeline=mock_pipeline,
            calendar=closed_calendar,
            tick_interval=1,
        )
        await scheduler.start()
        await asyncio.sleep(0.3)
        await scheduler.stop()

        assert scheduler.tick_count == 0
        mock_pipeline.run_cycle.assert_not_called()

    @pytest.mark.asyncio
    async def test_tick_count_increments_correctly(self, mock_pipeline, open_calendar):
        scheduler = IntradayScheduler(
            pipeline=mock_pipeline,
            calendar=open_calendar,
            tick_interval=1,
        )
        await scheduler.start()
        await asyncio.sleep(1.5)
        await scheduler.stop()

        assert scheduler.tick_count >= 1

    @pytest.mark.asyncio
    async def test_double_start_is_safe(self, mock_pipeline, open_calendar):
        scheduler = IntradayScheduler(
            pipeline=mock_pipeline,
            calendar=open_calendar,
            tick_interval=1,
        )
        await scheduler.start()
        await scheduler.start()
        await asyncio.sleep(0.1)
        await scheduler.stop()
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_stop_without_start_is_safe(self, mock_pipeline):
        scheduler = IntradayScheduler(pipeline=mock_pipeline, tick_interval=1)
        await scheduler.stop()
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_counters_initial_values(self, mock_pipeline):
        scheduler = IntradayScheduler(pipeline=mock_pipeline)
        assert scheduler.tick_count == 0
        assert scheduler.feature_count == 0
        assert scheduler.overview_count == 0
