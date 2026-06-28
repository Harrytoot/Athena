from datetime import datetime, timezone

from app.production_layer.audit.system_event_log import (
    SystemEventLog,
    SystemEvent,
    EventType,
)


class TestSystemEvent:
    def test_create(self):
        event = SystemEvent.create(
            event_type=EventType.SYSTEM_START,
            source="main",
            message="System started",
        )
        assert event.event_type == EventType.SYSTEM_START
        assert event.source == "main"
        assert len(event.id) > 0

    def test_with_details(self):
        event = SystemEvent.create(
            event_type=EventType.COMPONENT_INIT,
            source="broker",
            message="Broker initialized",
            details={"broker": "alpaca", "mode": "paper"},
        )
        assert event.details["broker"] == "alpaca"


class TestSystemEventLog:
    def test_log_event(self):
        log = SystemEventLog()
        event = log.log(EventType.SYSTEM_START, "main", "started")
        assert len(log.events) == 1
        assert event.event_type == EventType.SYSTEM_START

    def test_get_by_type(self):
        log = SystemEventLog()
        log.log(EventType.SYSTEM_START, "main", "m1")
        log.log(EventType.SYSTEM_START, "main", "m2")
        log.log(EventType.SYSTEM_STOP, "main", "m3")

        starts = log.get_by_type(EventType.SYSTEM_START)
        assert len(starts) == 2
        stops = log.get_by_type(EventType.SYSTEM_STOP)
        assert len(stops) == 1

    def test_get_by_source(self):
        log = SystemEventLog()
        log.log(EventType.COMPONENT_INIT, "broker", "m")
        log.log(EventType.COMPONENT_INIT, "cache", "m")
        log.log(EventType.COMPONENT_INIT, "broker", "m2")

        broker_events = log.get_by_source("broker")
        assert len(broker_events) == 2

    def test_get_recent(self):
        log = SystemEventLog()
        for i in range(10):
            log.log(EventType.SYSTEM_START, "main", f"m{i}")
        recent = log.get_recent(5)
        assert len(recent) == 5
        assert recent[-1].message == "m9"

    def test_count_by_type(self):
        log = SystemEventLog()
        log.log(EventType.SYSTEM_START, "m", "a")
        log.log(EventType.SYSTEM_START, "m", "b")
        log.log(EventType.DEGRADATION_ACTIVATE, "m", "c")

        counts = log.count_by_type()
        assert counts["system_start"] == 2
        assert counts["degradation_activate"] == 1

    def test_max_events(self):
        log = SystemEventLog(max_events=5)
        for i in range(10):
            log.log(EventType.SYSTEM_START, "main", f"m{i}")
        assert len(log.events) == 5

    def test_clear(self):
        log = SystemEventLog()
        log.log(EventType.SYSTEM_START, "main", "m")
        log.clear()
        assert len(log.events) == 0
