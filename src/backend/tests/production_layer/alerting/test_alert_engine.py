from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.alerting.alert_engine import (
    Alert,
    AlertRegistry,
    AlertSeverity,
)


class TestAlert:
    def test_create(self):
        alert = Alert.create(
            severity=AlertSeverity.WARN,
            rule_name="latency_spike",
            title="High latency",
            message="Latency 600ms exceeded 500ms",
            source="execution",
        )
        assert alert.severity == AlertSeverity.WARN
        assert alert.rule_name == "latency_spike"
        assert alert.source == "execution"
        assert not alert.acknowledged
        assert len(alert.id) > 0

    def test_context_stored(self):
        alert = Alert.create(
            severity=AlertSeverity.INFO,
            rule_name="test",
            title="t",
            message="m",
            source="s",
            context={"latency_ms": "600", "threshold_ms": "500"},
        )
        assert alert.context["latency_ms"] == "600"


class TestAlertSeverity:
    def test_ordering(self):
        assert AlertSeverity.INFO < AlertSeverity.WARN
        assert AlertSeverity.WARN < AlertSeverity.CRITICAL
        assert AlertSeverity.CRITICAL.priority() == 3


class TestAlertRegistry:
    def test_fire_and_retrieve(self):
        registry = AlertRegistry()
        alert = Alert.create(
            AlertSeverity.WARN, "test_rule", "title", "msg", "source"
        )
        registry.fire(alert)
        assert len(registry.history) == 1

    def test_get_alerts_by_severity(self):
        registry = AlertRegistry()
        registry.fire(Alert.create(AlertSeverity.INFO, "r1", "t", "m", "s"))
        registry.fire(Alert.create(AlertSeverity.WARN, "r2", "t", "m", "s"))
        registry.fire(Alert.create(AlertSeverity.CRITICAL, "r3", "t", "m", "s"))

        warns = registry.get_alerts(AlertSeverity.WARN)
        assert len(warns) == 1
        assert warns[0].rule_name == "r2"

    def test_count_by_severity(self):
        registry = AlertRegistry()
        registry.fire(Alert.create(AlertSeverity.INFO, "r", "t", "m", "s"))
        registry.fire(Alert.create(AlertSeverity.INFO, "r", "t", "m", "s"))
        registry.fire(Alert.create(AlertSeverity.WARN, "r", "t", "m", "s"))

        counts = registry.count_by_severity()
        assert counts["INFO"] == 2
        assert counts["WARN"] == 1

    def test_handler_called(self):
        registry = AlertRegistry()
        received = []

        def handler(alert):
            received.append(alert)

        registry.register_handler(AlertSeverity.WARN, handler)
        alert = Alert.create(AlertSeverity.WARN, "r", "t", "m", "s")
        registry.fire(alert)
        assert len(received) == 1
        assert received[0].rule_name == "r"

    def test_handler_not_called_for_other_severity(self):
        registry = AlertRegistry()
        received = []

        registry.register_handler(AlertSeverity.CRITICAL, lambda a: received.append(a))
        registry.fire(Alert.create(AlertSeverity.WARN, "r", "t", "m", "s"))
        assert len(received) == 0

    def test_dedup(self):
        registry = AlertRegistry(dedup_window_seconds=60)
        alert1 = Alert.create(AlertSeverity.WARN, "r", "t", "m", "s")
        alert2 = Alert.create(AlertSeverity.WARN, "r", "t", "m2", "s")
        registry.fire(alert1)
        registry.fire(alert2)
        assert len(registry.history) == 2

    def test_max_history(self):
        registry = AlertRegistry(max_history=5)
        for i in range(10):
            registry.fire(Alert.create(AlertSeverity.INFO, f"r{i}", "t", "m", "s"))
        assert len(registry.history) == 5

    def test_clear(self):
        registry = AlertRegistry()
        registry.fire(Alert.create(AlertSeverity.INFO, "r", "t", "m", "s"))
        registry.clear()
        assert len(registry.history) == 0

    def test_handler_exception_suppressed(self):
        registry = AlertRegistry()

        def bad_handler(alert):
            raise RuntimeError("handler error")

        registry.register_handler(AlertSeverity.WARN, bad_handler)
        registry.fire(Alert.create(AlertSeverity.WARN, "r", "t", "m", "s"))
        assert len(registry.history) == 1
