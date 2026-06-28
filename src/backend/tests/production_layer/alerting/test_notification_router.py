from datetime import datetime, timezone

from app.production_layer.alerting.notification_router import (
    Notification,
    NotificationRouter,
    ConsoleChannel,
    LogChannel,
)


class TestNotification:
    def test_create(self):
        n = Notification(
            channel="console",
            recipient="ops",
            title="Alert",
            body="Something happened",
            severity="WARN",
            timestamp=datetime.now(timezone.utc),
        )
        assert n.channel == "console"
        assert n.severity == "WARN"


class TestConsoleChannel:
    def test_send(self):
        ch = ConsoleChannel()
        n = Notification("console", "ops", "t", "b", "INFO", datetime.now(timezone.utc))
        assert ch.send(n)


class TestLogChannel:
    def test_send(self):
        import logging
        logger = logging.getLogger("test_alerts")
        ch = LogChannel(logger)
        n = Notification("log", "ops", "t", "b", "WARN", datetime.now(timezone.utc))
        assert ch.send(n)

    def test_default_logger(self):
        ch = LogChannel()
        n = Notification("log", "ops", "t", "b", "INFO", datetime.now(timezone.utc))
        assert ch.send(n)


class TestNotificationRouter:
    def test_route_to_console(self):
        router = NotificationRouter()
        router.register_channel("console", ConsoleChannel())
        n = Notification("console", "ops", "t", "b", "INFO", datetime.now(timezone.utc))
        results = router.route(n)
        assert results == [True]

    def test_route_to_default_fallback(self):
        router = NotificationRouter()
        router.register_channel("default", ConsoleChannel())
        n = Notification("unknown_channel", "ops", "t", "b", "INFO", datetime.now(timezone.utc))
        results = router.route(n)
        assert results == [True]

    def test_route_log(self):
        router = NotificationRouter()
        notifications_sent = router.route(
            Notification("console", "ops", "t", "b", "INFO", datetime.now(timezone.utc))
        )
        assert len(router.notification_log) == 1

    def test_get_log(self):
        router = NotificationRouter()
        router.register_channel("c1", ConsoleChannel())
        router.register_channel("c2", ConsoleChannel())

        n1 = Notification("c1", "ops", "t1", "b", "INFO", datetime.now(timezone.utc))
        n2 = Notification("c2", "ops", "t2", "b", "INFO", datetime.now(timezone.utc))
        router.route(n1)
        router.route(n2)

        assert len(router.get_log("c1")) == 1
        assert len(router.get_log("c2")) == 1
        assert len(router.get_log()) == 2

    def test_max_notifications(self):
        router = NotificationRouter(max_notifications=5)
        for i in range(10):
            router.route(
                Notification("c", "ops", f"t{i}", "b", "INFO", datetime.now(timezone.utc))
            )
        assert len(router.notification_log) == 5

    def test_clear(self):
        router = NotificationRouter()
        router.route(Notification("c", "ops", "t", "b", "INFO", datetime.now(timezone.utc)))
        router.clear()
        assert len(router.notification_log) == 0
