import pytest

from app.ingestion.realtime.replay_feed import ReplayFeed
from app.ingestion.realtime.schemas import MarketTick


_SAMPLE_TICK = {
    "symbol": "000001",
    "name": "平安银行",
    "price": 50.0,
    "change_pct": 1.5,
    "volume": 1e7,
    "turnover": 5e8,
    "high": 50.5,
    "low": 49.5,
    "open": 49.8,
    "pre_close": 49.3,
    "bid_price": 49.99,
    "ask_price": 50.01,
    "bid_volume": 5000,
    "ask_volume": 3000,
    "timestamp": "2026-06-29T10:00:00",
}


class TestReplayFeed:

    @pytest.fixture
    def empty_feed(self):
        return ReplayFeed()

    @pytest.fixture
    def feed_with_data(self):
        feed = ReplayFeed()
        feed.load_ticks([
            dict(_SAMPLE_TICK),
            dict({**_SAMPLE_TICK, "symbol": "000002", "price": 20.0}),
            dict({**_SAMPLE_TICK, "symbol": "000001", "price": 50.5}),
        ])
        return feed

    @pytest.mark.asyncio
    async def test_get_ticks_returns_correct_count(self, feed_with_data):
        ticks = await feed_with_data.get_realtime_ticks(["000001"])
        assert len(ticks) == 1
        assert ticks[0].symbol == "000001"

    @pytest.mark.asyncio
    async def test_get_ticks_advances_cursor(self, feed_with_data):
        await feed_with_data.get_realtime_ticks(["000001"])
        assert feed_with_data.cursor == 1

        await feed_with_data.get_realtime_ticks(["000002"])
        assert feed_with_data.cursor == 2

    @pytest.mark.asyncio
    async def test_get_ticks_all_symbols(self, feed_with_data):
        ticks = await feed_with_data.get_realtime_ticks([])
        assert len(ticks) == 1

    @pytest.mark.asyncio
    async def test_reset_cursor(self, feed_with_data):
        await feed_with_data.get_realtime_ticks(["000001"])
        await feed_with_data.get_realtime_ticks(["000002"])
        feed_with_data.reset_cursor()
        assert feed_with_data.cursor == 0
        ticks = await feed_with_data.get_realtime_ticks(["000001"])
        assert ticks[0].symbol == "000001"

    @pytest.mark.asyncio
    async def test_append_tick(self, empty_feed):
        tick = MarketTick(
            symbol="600000", name="浦发银行", price=10.0, change_pct=0.5,
            volume=1e6, turnover=1e7, high=10.1, low=9.9, open=10.0,
            pre_close=10.0,
        )
        empty_feed.append_tick(tick)
        assert empty_feed.remaining == 1
        ticks = await empty_feed.get_realtime_ticks(["600000"])
        assert len(ticks) == 1
        assert ticks[0].symbol == "600000"

    @pytest.mark.asyncio
    async def test_remaining_count(self, feed_with_data):
        assert feed_with_data.remaining == 3
        await feed_with_data.get_realtime_ticks(["000001"])
        assert feed_with_data.remaining == 2

    @pytest.mark.asyncio
    async def test_historical_bars_from_ticks(self, feed_with_data):
        bars = await feed_with_data.get_historical_bars("000001", "1d")
        assert len(bars) == 2
        assert all(b.symbol == "000001" for b in bars)

    @pytest.mark.asyncio
    async def test_historical_bars_cached(self, feed_with_data):
        bars1 = await feed_with_data.get_historical_bars("000001", "1d")
        bars2 = await feed_with_data.get_historical_bars("000001", "1d")
        assert bars1 is bars2

    @pytest.mark.asyncio
    async def test_load_ticks_resets_cursor(self, empty_feed):
        empty_feed.load_ticks([_SAMPLE_TICK, _SAMPLE_TICK])
        assert empty_feed.cursor == 0
        assert empty_feed.remaining == 2

    @pytest.mark.asyncio
    async def test_recorded_ticks_returns_copy(self, feed_with_data):
        recorded = feed_with_data.recorded_ticks
        assert len(recorded) == 3
        recorded.append({})
        assert len(feed_with_data.recorded_ticks) == 3
