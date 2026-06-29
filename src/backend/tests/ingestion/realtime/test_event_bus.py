import pytest

from app.ingestion.realtime.event_bus import IngestionEvent, IngestionEventBus


class TestIngestionEventBus:

    @pytest.fixture
    def bus(self):
        return IngestionEventBus()

    def test_publish_creates_event_with_id(self, bus):
        event = bus.publish("market_tick", "000001", {"price": 50.0})
        assert isinstance(event, IngestionEvent)
        assert event.event_id != ""
        assert event.symbol == "000001"
        assert event.event_type == "market_tick"

    def test_publish_increments_sequence_number(self, bus):
        e1 = bus.publish("market_tick", "000001")
        e2 = bus.publish("market_tick", "000001")
        assert e1.sequence_number == 1
        assert e2.sequence_number == 2

    def test_publish_different_symbols_separate_sequences(self, bus):
        e1 = bus.publish("market_tick", "000001")
        e2 = bus.publish("market_tick", "000002")
        assert e1.sequence_number == 1
        assert e2.sequence_number == 1

    def test_event_log_records_all_events(self, bus):
        bus.publish("market_tick", "000001")
        bus.publish("feature_update", "000001")
        log = bus.get_event_log()
        assert len(log) == 2
        assert bus.event_count == 2

    def test_get_events_for_symbol(self, bus):
        bus.publish("market_tick", "000001")
        bus.publish("market_tick", "000002")
        bus.publish("market_tick", "000001")
        events = bus.get_events_for_symbol("000001")
        assert len(events) == 2

    def test_reset_clears_log(self, bus):
        bus.publish("market_tick", "000001")
        bus.reset()
        assert bus.event_count == 0
        assert bus.get_event_log() == []

    def test_reset_resets_sequences(self, bus):
        bus.publish("market_tick", "000001")
        bus.reset()
        e = bus.publish("market_tick", "000001")
        assert e.sequence_number == 1

    def test_subscriber_receives_events(self, bus):
        received = []

        def callback(event):
            received.append(event)

        bus.subscribe(callback)
        bus.publish("market_tick", "000001")
        assert len(received) == 1
        assert received[0].symbol == "000001"

    def test_subscriber_exception_does_not_block(self, bus):
        def failing_callback(event):
            raise RuntimeError("subscriber failure")

        def good_callback(event):
            pass

        bus.subscribe(failing_callback)
        bus.subscribe(good_callback)
        event = bus.publish("market_tick", "000001")
        assert event is not None

    def test_to_replay_events_serializable(self, bus):
        bus.publish("market_tick", "000001", {"price": 50.0})
        bus.publish("market_tick", "000002", {"price": 20.0})
        replay_data = bus.to_replay_events()
        assert len(replay_data) == 2
        assert replay_data[0]["event_type"] == "market_tick"
        assert replay_data[0]["symbol"] == "000001"
        assert replay_data[0]["payload"]["price"] == 50.0

    def test_from_replay_events_roundtrip(self, bus):
        bus.publish("market_tick", "000001", {"price": 50.0})
        replay_data = bus.to_replay_events()
        events = IngestionEventBus.from_replay_events(replay_data)
        assert len(events) == 1
        assert events[0].symbol == "000001"
        assert events[0].payload["price"] == 50.0

    def test_event_deterministic_id(self):
        e1 = IngestionEvent(
            event_type="market_tick",
            symbol="000001",
            payload={"price": 50.0},
            event_timestamp="2026-06-29T10:00:00",
            sequence_number=1,
        )
        e2 = IngestionEvent(
            event_type="market_tick",
            symbol="000001",
            payload={"price": 50.0},
            event_timestamp="2026-06-29T10:00:00",
            sequence_number=1,
        )
        assert e1.event_id == e2.event_id

    def test_event_log_is_ordered(self, bus):
        bus.publish("event_a", "000001")
        bus.publish("event_b", "000001")
        bus.publish("event_c", "000001")
        log = bus.get_event_log()
        types = [e.event_type for e in log]
        assert types == ["event_a", "event_b", "event_c"]
