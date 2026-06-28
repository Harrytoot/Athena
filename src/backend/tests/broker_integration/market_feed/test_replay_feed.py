import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.broker_integration.market_feed.data_normalizer import NormalizedBar
from app.broker_integration.market_feed.replay_feed import (
    ReplayFeed,
    ReplayFeedConfig,
    ReplayBar,
)


def _make_bar(symbol: str, day: int, price: int) -> NormalizedBar:
    return NormalizedBar(
        symbol=symbol,
        timestamp=datetime(2025, 1, day, tzinfo=timezone.utc),
        open=Decimal(str(price)),
        high=Decimal(str(price + 2)),
        low=Decimal(str(price - 1)),
        close=Decimal(str(price + 1)),
        volume=Decimal("10000"),
        source="test",
    )


class TestReplayBar:
    def test_to_normalized(self):
        rb = ReplayBar(
            symbol="TEST",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=Decimal("10"),
            high=Decimal("12"),
            low=Decimal("9"),
            close=Decimal("11"),
            volume=Decimal("5000"),
        )
        nb = rb.to_normalized()
        assert nb.source == "replay"
        assert nb.close == Decimal("11")


class TestReplayFeed:
    def test_load_and_advance(self):
        feed = ReplayFeed()
        bars = [
            _make_bar("A", 1, 100),
            _make_bar("B", 1, 200),
            _make_bar("A", 2, 101),
        ]
        feed.load_bars(bars)

        assert feed.total_bars == 3
        assert feed.total_timestamps == 2
        assert feed.symbols == {"A", "B"}  # Use the property, not _symbols
        assert not feed.is_finished

    def test_advance_returns_bars(self):
        feed = ReplayFeed()
        bars = [
            _make_bar("A", 1, 100),
            _make_bar("B", 1, 200),
            _make_bar("A", 2, 101),
            _make_bar("B", 2, 201),
        ]
        feed.load_bars(bars)

        result1 = feed.advance()
        assert result1 is not None
        assert "A" in result1
        assert "B" in result1
        assert result1["A"].close == Decimal("101")
        assert result1["B"].close == Decimal("201")

        result2 = feed.advance()
        assert result2 is not None
        assert "A" in result2
        assert result2["A"].close == Decimal("102")

        assert feed.is_finished

        result3 = feed.advance()
        assert result3 is None
        assert feed.is_finished

    def test_reset(self):
        feed = ReplayFeed()
        feed.load_bars([_make_bar("A", 1, 100), _make_bar("A", 2, 101)])
        feed.advance()
        feed.advance()
        assert feed.is_finished

        feed.reset()
        assert not feed.is_finished
        assert feed.current_index == 0

    def test_peek(self):
        feed = ReplayFeed()
        feed.load_bars([_make_bar("A", 1, 100), _make_bar("A", 2, 101)])

        peeked = feed.peek()
        assert peeked is not None
        assert peeked["A"].close == Decimal("101")
        assert feed.current_index == 0

    def test_iterate(self):
        feed = ReplayFeed()
        feed.load_bars([_make_bar("A", 1, 100), _make_bar("A", 2, 101), _make_bar("A", 3, 102)])

        results = list(feed.iterate())
        assert len(results) == 3

    def test_progress(self):
        feed = ReplayFeed()
        feed.load_bars([_make_bar("A", 1, 100), _make_bar("A", 2, 101), _make_bar("A", 3, 102)])

        assert feed.progress == 0.0
        feed.advance()
        assert pytest.approx(feed.progress, abs=0.01) == 1.0 / 3
        feed.advance()
        feed.advance()
        assert feed.progress == 1.0

    def test_deterministic_replay(self):
        bars = [_make_bar("A", i, 100 + i) for i in range(1, 6)]

        feed1 = ReplayFeed()
        feed1.load_bars(bars)
        results1 = list(feed1.iterate())

        feed2 = ReplayFeed()
        feed2.load_bars(bars)
        results2 = list(feed2.iterate())

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert list(r1.keys()) == list(r2.keys())
            for k in r1:
                assert r1[k].close == r2[k].close
                assert r1[k].timestamp == r2[k].timestamp

    def test_get_prices_for_time(self):
        feed = ReplayFeed()
        bars = [
            _make_bar("A", 1, 100),
            _make_bar("A", 2, 101),
            _make_bar("B", 1, 200),
        ]
        feed.load_bars(bars)

        prices = feed.get_prices_for_time(datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert prices["A"] == Decimal("101")
        assert prices["B"] == Decimal("201")

    def test_advance_to(self):
        feed = ReplayFeed()
        bars = [
            _make_bar("A", 1, 100),
            _make_bar("A", 2, 101),
            _make_bar("A", 3, 102),
        ]
        feed.load_bars(bars)

        result = feed.advance_to(datetime(2025, 1, 2, tzinfo=timezone.utc))
        assert result is not None
        assert result["A"].close == Decimal("102")
        assert feed.current_index >= 2

    def test_get_window(self):
        feed = ReplayFeed()
        bars = [
            _make_bar("A", 1, 100),
            _make_bar("A", 2, 101),
            _make_bar("A", 3, 102),
            _make_bar("A", 4, 103),
        ]
        feed.load_bars(bars)

        window = feed.get_window(
            "A",
            datetime(2025, 1, 2, tzinfo=timezone.utc),
            datetime(2025, 1, 3, tzinfo=timezone.utc),
        )
        assert len(window) == 2

    def test_loop_mode(self):
        feed = ReplayFeed(config=ReplayFeedConfig(loop=True))
        feed.load_bars([_make_bar("A", 1, 100), _make_bar("A", 2, 101)])

        feed.advance()
        feed.advance()
        assert not feed.is_finished

    def test_load_ohlcv(self):
        feed = ReplayFeed()
        feed.load_ohlcv(
            symbol="DIRECT",
            timestamps=[
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
            ],
            opens=[Decimal("10"), Decimal("11")],
            highs=[Decimal("12"), Decimal("13")],
            lows=[Decimal("9"), Decimal("10")],
            closes=[Decimal("11"), Decimal("12")],
            volumes=[Decimal("1000"), Decimal("2000")],
        )
        assert feed.total_bars == 2

    def test_serialize_roundtrip(self):
        feed = ReplayFeed()
        feed.load_bars([_make_bar("A", 1, 100), _make_bar("B", 1, 200)])

        data = feed.to_dict()
        assert "A" in data
        assert "B" in data

        feed2 = ReplayFeed.from_dict(data)
        assert feed2.total_bars == feed.total_bars

    def test_start_end_time_filter(self):
        feed = ReplayFeed(
            config=ReplayFeedConfig(
                start_time=datetime(2025, 1, 2, tzinfo=timezone.utc),
                end_time=datetime(2025, 1, 3, tzinfo=timezone.utc),
            )
        )
        feed.load_bars([
            _make_bar("A", 1, 100),
            _make_bar("A", 2, 101),
            _make_bar("A", 3, 102),
            _make_bar("A", 4, 103),
        ])

        result = feed.advance()
        assert result is not None
        assert feed.current_time == datetime(2025, 1, 2, tzinfo=timezone.utc)
