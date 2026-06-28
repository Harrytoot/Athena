from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.observability.metrics_collector import (
    MetricsCollector,
    MetricPoint,
    LatencySnapshot,
    LiveMetrics,
)


class TestMetricPoint:
    def test_create_metric_point(self):
        mp = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            name="cpu_usage",
            value=Decimal("75.5"),
            tags={"host": "server1"},
        )
        assert mp.name == "cpu_usage"
        assert mp.value == Decimal("75.5")
        assert mp.tags == {"host": "server1"}

    def test_empty_name_raises(self):
        try:
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                name="",
                value=Decimal("1"),
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_frozen(self):
        mp = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            name="test",
            value=Decimal("1"),
        )
        try:
            mp.name = "changed"
            assert False, "Should have raised"
        except Exception:
            pass


class TestLatencySnapshot:
    def test_create_snapshot(self):
        snap = LatencySnapshot(
            timestamp=datetime.now(timezone.utc),
            component="execution",
            operation="order_roundtrip",
            duration_ms=Decimal("123.45"),
        )
        assert snap.component == "execution"
        assert snap.duration_ms == Decimal("123.45")


class TestMetricsCollector:
    def test_record_metric(self):
        mc = MetricsCollector()
        mc.record_metric("fill_rate", Decimal("95.5"))
        assert len(mc.metric_buffer) == 1

    def test_record_latency(self):
        mc = MetricsCollector()
        mc.record_latency("execution", "order_roundtrip", Decimal("100"))
        assert len(mc.latency_buffer) == 1

    def test_get_recent_metrics(self):
        mc = MetricsCollector()
        for i in range(100):
            mc.record_metric("pnl", Decimal(str(i)))
        recent = mc.get_recent_metrics("pnl", limit=10)
        assert len(recent) == 10
        assert recent[-1].value == Decimal("99")

    def test_get_avg_metric(self):
        mc = MetricsCollector()
        mc.record_metric("test", Decimal("10"))
        mc.record_metric("test", Decimal("20"))
        avg = mc.get_avg_metric("test")
        assert avg == Decimal("15")

    def test_get_avg_metric_empty(self):
        mc = MetricsCollector()
        assert mc.get_avg_metric("nonexistent") == Decimal("0")

    def test_get_latency_p50(self):
        mc = MetricsCollector()
        for d in [10, 30, 20, 50, 40]:
            mc.record_latency("exec", "roundtrip", Decimal(str(d)))
        p50 = mc.get_latency_p50("exec", "roundtrip")
        assert p50 == Decimal("30")

    def test_get_latency_p99(self):
        mc = MetricsCollector()
        for d in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            mc.record_latency("a", "b", Decimal(str(d)))
        p99 = mc.get_latency_p99("a", "b")
        assert p99 == Decimal("100")

    def test_snapshot_live_metrics(self):
        mc = MetricsCollector()
        mc.record_latency("execution", "order_roundtrip", Decimal("50"))
        lm = mc.snapshot_live_metrics(
            total_pnl=Decimal("1000"),
            total_exposure=Decimal("50000"),
            fill_rate_pct=Decimal("98"),
            open_orders=3,
            active_risk_limit_pct=Decimal("45"),
        )
        assert lm.total_pnl == Decimal("1000")
        assert lm.fill_rate_pct == Decimal("98")
        assert lm.open_orders == 3

    def test_clear(self):
        mc = MetricsCollector()
        mc.record_metric("x", Decimal("1"))
        mc.record_latency("a", "b", Decimal("5"))
        mc.clear()
        assert len(mc.metric_buffer) == 0
        assert len(mc.latency_buffer) == 0
