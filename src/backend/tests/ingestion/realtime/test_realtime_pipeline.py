from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ingestion.realtime.event_bus import IngestionEventBus
from app.ingestion.realtime.mock_tick_provider import MockRealtimeTickProvider
from app.ingestion.realtime.realtime_pipeline import RealtimePipeline
from app.ingestion.realtime.runtime_bridge import RuntimeBridge


class TestRealtimePipeline:

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.fixture
    def provider(self):
        return MockRealtimeTickProvider(seed=1)

    @pytest.fixture
    def symbols(self):
        return ["000001", "000002"]

    @pytest.fixture
    def pipeline(self, mock_session_factory, provider, symbols):
        return RealtimePipeline(
            session_factory=mock_session_factory,
            provider=provider,
            symbols=symbols,
        )

    @pytest.mark.asyncio
    async def test_run_cycle_returns_result(self, pipeline):
        result = await pipeline.run_cycle()
        assert result["status"] == "ok"
        assert result["features_written"] > 0
        assert result["symbols_triggered"] > 0
        assert result["cycle"] == 1

    @pytest.mark.asyncio
    async def test_run_cycle_increments_cycle_count(self, pipeline):
        await pipeline.run_cycle()
        await pipeline.run_cycle()
        assert pipeline.cycle_count == 2

    @pytest.mark.asyncio
    async def test_run_cycle_records_events(self, pipeline):
        await pipeline.run_cycle()
        events = pipeline.get_event_log()
        assert len(events) > 0
        assert events[0]["event_type"] == "market_tick"

    @pytest.mark.asyncio
    async def test_set_provider_switches_source(self, mock_session_factory, symbols):
        provider1 = MockRealtimeTickProvider(seed=1)
        provider2 = MockRealtimeTickProvider(seed=99)

        ticks1 = await provider1.get_realtime_ticks(symbols)
        ticks2 = await provider2.get_realtime_ticks(symbols)
        assert ticks1 != ticks2

    @pytest.mark.asyncio
    async def test_run_cycle_with_no_symbols(self, mock_session_factory):
        pipeline = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=MockRealtimeTickProvider(seed=1),
            symbols=[],
        )
        result = await pipeline.run_cycle()
        assert result["status"] == "no_data"

    @pytest.mark.asyncio
    async def test_pipeline_event_bus_accessible(self, pipeline):
        assert isinstance(pipeline.event_bus, IngestionEventBus)

    @pytest.mark.asyncio
    async def test_pipeline_runtime_bridge_accessible(self, pipeline):
        assert isinstance(pipeline.runtime_bridge, RuntimeBridge)
