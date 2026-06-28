from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.observability.latency_tracker import LatencyTracker


class TestLatencyTracker:
    def test_record_and_count(self):
        lt = LatencyTracker()
        assert lt.count("exec", "order") == 0
        lt.record("exec", "order", Decimal("100"))
        assert lt.count("exec", "order") == 1

    def test_percentiles(self):
        lt = LatencyTracker()
        for d in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            lt.record("api", "request", Decimal(str(d)))

        assert lt.p50("api", "request") == Decimal("60")
        assert lt.p95("api", "request") == Decimal("100")
        assert lt.p99("api", "request") == Decimal("100")

    def test_percentiles_empty(self):
        lt = LatencyTracker()
        assert lt.p50("none", "none") == Decimal("0")
        assert lt.p99("none", "none") == Decimal("0")

    def test_mean(self):
        lt = LatencyTracker()
        lt.record("api", "req", Decimal("10"))
        lt.record("api", "req", Decimal("20"))
        lt.record("api", "req", Decimal("30"))
        assert lt.mean("api", "req") == Decimal("20")

    def test_mean_empty(self):
        lt = LatencyTracker()
        assert lt.mean("none", "none") == Decimal("0")

    def test_latest(self):
        lt = LatencyTracker()
        lt.record("exec", "order", Decimal("100"))
        lt.record("exec", "order", Decimal("200"))

        latest = lt.latest("exec", "order")
        assert latest is not None
        assert latest.duration_ms == Decimal("200")

    def test_latest_empty(self):
        lt = LatencyTracker()
        assert lt.latest("none", "none") is None

    def test_exceed_threshold(self):
        lt = LatencyTracker()
        lt.record("exec", "order", Decimal("600"))
        assert lt.exceed_threshold("exec", "order", Decimal("500"))
        assert not lt.exceed_threshold("exec", "order", Decimal("1000"))

    def test_exceed_threshold_no_data(self):
        lt = LatencyTracker()
        assert not lt.exceed_threshold("none", "none", Decimal("100"))

    def test_clear(self):
        lt = LatencyTracker()
        lt.record("a", "b", Decimal("10"))
        lt.clear()
        assert lt.count("a", "b") == 0
