from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.observability.system_health_monitor import (
    SystemHealthMonitor,
    HealthStatus,
    ComponentHealthReport,
)


class TestHealthStatus:
    def test_create(self):
        hs = HealthStatus(
            component="broker",
            status=HealthStatus.STATUS_UP,
            message="ok",
            checked_at=datetime.now(timezone.utc),
        )
        assert hs.component == "broker"
        assert hs.status == "up"

    def test_status_constants(self):
        assert HealthStatus.STATUS_UP == "up"
        assert HealthStatus.STATUS_DOWN == "down"
        assert HealthStatus.STATUS_TIMEOUT == "timeout"


class TestSystemHealthMonitor:
    def test_register_check(self):
        monitor = SystemHealthMonitor()

        def check_broker():
            return HealthStatus(
                component="broker",
                status=HealthStatus.STATUS_UP,
                message="ok",
                checked_at=datetime.now(timezone.utc),
            )

        monitor.register_check("broker", check_broker)
        assert "broker" in monitor.health_check_registry
        assert monitor.failure_counts["broker"] == 0

    def test_register_empty_name_raises(self):
        monitor = SystemHealthMonitor()
        try:
            monitor.register_check("", lambda: None)
            assert False
        except ValueError:
            pass

    def test_run_all_checks_all_healthy(self):
        monitor = SystemHealthMonitor()

        def healthy():
            return HealthStatus(
                component="a",
                status=HealthStatus.STATUS_UP,
                message="ok",
                checked_at=datetime.now(timezone.utc),
            )

        monitor.register_check("a", healthy)
        monitor.register_check("b", healthy)

        report = monitor.run_all_checks()
        assert report.overall_status == HealthStatus.STATUS_UP
        assert report.healthy_component_count() == 2

    def test_run_all_checks_one_unhealthy(self):
        monitor = SystemHealthMonitor()

        def healthy():
            return HealthStatus(
                component="a",
                status=HealthStatus.STATUS_UP,
                message="ok",
                checked_at=datetime.now(timezone.utc),
            )

        def unhealthy():
            return HealthStatus(
                component="b",
                status=HealthStatus.STATUS_DOWN,
                message="error",
                checked_at=datetime.now(timezone.utc),
            )

        monitor.register_check("a", healthy)
        monitor.register_check("b", unhealthy)

        report = monitor.run_all_checks()
        assert report.overall_status == HealthStatus.STATUS_DOWN
        assert report.healthy_component_count() == 1

    def test_run_all_checks_exception_handler(self):
        monitor = SystemHealthMonitor()

        def raises():
            raise RuntimeError("boom")

        monitor.register_check("bad", raises)
        report = monitor.run_all_checks()
        assert report.overall_status == HealthStatus.STATUS_DOWN
        assert report.components["bad"].status == HealthStatus.STATUS_DOWN
        assert "boom" in report.components["bad"].message

    def test_failure_count_tracking(self):
        monitor = SystemHealthMonitor(max_consecutive_failures=2)

        def failing():
            return HealthStatus(
                component="svc",
                status=HealthStatus.STATUS_DOWN,
                message="fail",
                checked_at=datetime.now(timezone.utc),
            )

        monitor.register_check("svc", failing)
        monitor.run_all_checks()
        assert monitor.failure_counts["svc"] == 1
        monitor.run_all_checks()
        assert monitor.failure_counts["svc"] == 2

    def test_degradation_threshold(self):
        monitor = SystemHealthMonitor(max_consecutive_failures=2)

        def failing():
            return HealthStatus(
                component="svc",
                status=HealthStatus.STATUS_DOWN,
                message="fail",
                checked_at=datetime.now(timezone.utc),
            )

        monitor.register_check("svc", failing)
        monitor.run_all_checks()
        assert not monitor.check_degradation_threshold()
        monitor.run_all_checks()
        assert monitor.check_degradation_threshold()

    def test_activate_deactivate_degradation(self):
        monitor = SystemHealthMonitor()
        assert not monitor.degraded
        monitor.activate_degradation()
        assert monitor.degraded

        report = monitor.run_all_checks()
        assert report.overall_status == "degraded"
        assert report.degradation_active

        monitor.deactivate_degradation()
        assert not monitor.degraded

    def test_unregister_check(self):
        monitor = SystemHealthMonitor()
        monitor.register_check("x", lambda: None)
        monitor.unregister_check("x")
        assert "x" not in monitor.health_check_registry
        assert "x" not in monitor.failure_counts


class TestComponentHealthReport:
    def test_create(self):
        hs = HealthStatus(
            component="a",
            status=HealthStatus.STATUS_UP,
            message="ok",
            checked_at=datetime.now(timezone.utc),
        )
        report = ComponentHealthReport(
            timestamp=datetime.now(timezone.utc),
            components={"a": hs},
            overall_status=HealthStatus.STATUS_UP,
            degradation_active=False,
        )
        assert report.total_component_count() == 1
        assert report.healthy_component_count() == 1
