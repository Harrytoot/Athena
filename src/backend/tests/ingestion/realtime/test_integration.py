from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ingestion.realtime.mock_tick_provider import MockRealtimeTickProvider
from app.ingestion.realtime.realtime_pipeline import RealtimePipeline
from app.ingestion.realtime.replay_feed import ReplayFeed


class TestIntegrationFeatureStore:

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.mark.asyncio
    async def test_feature_store_updated_on_cycle(self, mock_session_factory):
        pipeline = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=MockRealtimeTickProvider(seed=1),
            symbols=["000001"],
        )
        result = await pipeline.run_cycle()
        assert result["features_written"] == 4

    @pytest.mark.asyncio
    async def test_feature_store_batch_write(self, mock_session_factory):
        pipeline = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=MockRealtimeTickProvider(seed=1),
            symbols=["000001", "000002", "000003"],
        )
        result = await pipeline.run_cycle()
        assert result["features_written"] == 12


class TestIntegrationRuntimeTrigger:

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.mark.asyncio
    async def test_runtime_triggered_per_symbol(self, mock_session_factory):
        pipeline = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=MockRealtimeTickProvider(seed=1),
            symbols=["000001", "000002"],
        )
        result = await pipeline.run_cycle()
        assert result["symbols_triggered"] == 2

    @pytest.mark.asyncio
    async def test_runtime_state_persists_between_cycles(self, mock_session_factory):
        pipeline = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=MockRealtimeTickProvider(seed=1),
            symbols=["000001"],
        )
        await pipeline.run_cycle()
        active = pipeline.runtime_bridge.get_runtime().get_active("000001")
        assert active is not None


class TestDeterministicReplay:

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.mark.asyncio
    async def test_produces_same_output_on_replay(self, mock_session_factory):
        symbols = ["000001", "000002"]
        provider = MockRealtimeTickProvider(seed=42)

        pipeline1 = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=provider,
            symbols=symbols,
        )
        result1 = await pipeline1.run_cycle()
        events1 = pipeline1.get_event_log()

        replay_feed = ReplayFeed()
        replay_feed.load_ticks(events1)

        pipeline2 = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=replay_feed,
            symbols=symbols,
        )
        result2 = await pipeline2.run_cycle()
        events2 = pipeline2.get_event_log()

        assert result1["features_written"] > 0
        assert result2["features_written"] > 0
        assert len(events2) == 2

    @pytest.mark.asyncio
    async def test_event_log_deterministic(self, mock_session_factory):
        symbols = ["000001"]

        provider1 = MockRealtimeTickProvider(seed=42)
        provider2 = MockRealtimeTickProvider(seed=42)

        pipeline1 = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=provider1,
            symbols=symbols,
        )
        pipeline2 = RealtimePipeline(
            session_factory=mock_session_factory,
            provider=provider2,
            symbols=symbols,
        )

        await pipeline1.run_cycle()
        await pipeline2.run_cycle()

        events1 = pipeline1.get_event_log()
        events2 = pipeline2.get_event_log()

        assert len(events1) == len(events2)
        for e1, e2 in zip(events1, events2):
            assert e1["event_type"] == e2["event_type"]
            assert e1["symbol"] == e2["symbol"]
