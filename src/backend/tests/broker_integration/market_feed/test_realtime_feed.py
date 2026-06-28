import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.broker_integration.market_feed.realtime_feed import (
    SimulatedRealtimeFeed,
    SimulatedRealtimeFeedConfig,
    RealtimeBar,
)


class TestRealtimeBar:
    def test_mid_price(self):
        bar = RealtimeBar(
            symbol="TEST",
            timestamp=datetime.now(timezone.utc),
            bid=Decimal("100"),
            ask=Decimal("102"),
            last=Decimal("101"),
            volume=Decimal("1000"),
        )
        assert bar.mid == Decimal("101")
        assert bar.spread == Decimal("2")

    def test_to_normalized(self):
        bar = RealtimeBar(
            symbol="TEST",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            bid=Decimal("99"),
            ask=Decimal("101"),
            last=Decimal("100"),
            volume=Decimal("500"),
            open=Decimal("98"),
            high=Decimal("102"),
            low=Decimal("97"),
            close=Decimal("100"),
        )
        nb = bar.to_normalized()
        assert nb.symbol == "TEST"
        assert nb.close == Decimal("100")
        assert nb.source == "realtime"


class TestSimulatedRealtimeFeed:
    def test_subscribe_and_generate_tick(self):
        feed = SimulatedRealtimeFeed(
            config=SimulatedRealtimeFeedConfig(seed=42)
        )
        feed.set_base_price("TEST", Decimal("100"))
        feed.subscribe(["TEST"])
        feed.start()

        feed.generate_tick()

        bar = feed.get_latest("TEST")
        assert bar is not None
        assert bar.symbol == "TEST"
        assert bar.bid > 0
        assert bar.ask > bar.bid
        assert bar.volume > 0

    def test_stop_prevents_generation(self):
        feed = SimulatedRealtimeFeed(config=SimulatedRealtimeFeedConfig(seed=42))
        feed.set_base_price("TEST", Decimal("100"))
        feed.subscribe(["TEST"])

        feed.generate_tick()
        assert feed.get_latest("TEST") is None

    def test_get_all_latest(self):
        feed = SimulatedRealtimeFeed(config=SimulatedRealtimeFeedConfig(seed=42))
        feed.set_base_price("A", Decimal("50"))
        feed.set_base_price("B", Decimal("75"))
        feed.subscribe(["A", "B"])
        feed.start()
        feed.generate_tick()

        all_bars = feed.get_all_latest()
        assert "A" in all_bars
        assert "B" in all_bars

    def test_unsubscribe(self):
        feed = SimulatedRealtimeFeed(config=SimulatedRealtimeFeedConfig(seed=42))
        feed.set_base_price("TEST", Decimal("100"))
        feed.subscribe(["TEST"])
        feed.start()
        feed.generate_tick()

        assert feed.get_latest("TEST") is not None

        feed.unsubscribe(["TEST"])
        feed.generate_tick()

    def test_callback(self):
        feed = SimulatedRealtimeFeed(config=SimulatedRealtimeFeedConfig(seed=42))
        feed.set_base_price("TEST", Decimal("100"))
        feed.subscribe(["TEST"])
        feed.start()

        received: list = []
        feed.on_tick(lambda sym, bar: received.append((sym, bar)))

        feed.generate_tick()
        assert len(received) == 1
        assert received[0][0] == "TEST"

    def test_is_running(self):
        feed = SimulatedRealtimeFeed()
        assert not feed.is_running()
        feed.start()
        assert feed.is_running()
        feed.stop()
        assert not feed.is_running()

    def test_deterministic_same_seed(self):
        feed1 = SimulatedRealtimeFeed(config=SimulatedRealtimeFeedConfig(seed=123))
        feed1.set_base_price("X", Decimal("50"))
        feed1.subscribe(["X"])
        feed1.start()
        feed1.generate_tick()
        bar1 = feed1.get_latest("X")

        feed2 = SimulatedRealtimeFeed(config=SimulatedRealtimeFeedConfig(seed=123))
        feed2.set_base_price("X", Decimal("50"))
        feed2.subscribe(["X"])
        feed2.start()
        feed2.generate_tick()
        bar2 = feed2.get_latest("X")

        assert bar1.last == bar2.last
        assert bar1.bid == bar2.bid
        assert bar1.ask == bar2.ask
