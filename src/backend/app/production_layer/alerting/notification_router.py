from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Notification:
    channel: str
    recipient: str
    title: str
    body: str
    severity: str
    timestamp: datetime


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, notification: Notification) -> bool:
        ...


class ConsoleChannel(NotificationChannel):
    def send(self, notification: Notification) -> bool:
        return True


class LogChannel(NotificationChannel):
    def __init__(self, logger: Any = None):
        import logging
        self.logger = logger or logging.getLogger("athena.alerts")

    def send(self, notification: Notification) -> bool:
        self.logger.log(
            {"INFO": 20, "WARN": 30, "CRITICAL": 40}.get(notification.severity, 20),
            f"[{notification.severity}] {notification.title}: {notification.body}",
        )
        return True


@dataclass
class NotificationRouter:
    channels: Dict[str, List[NotificationChannel]] = field(default_factory=dict)
    max_notifications: int = 500
    notification_log: List[Notification] = field(default_factory=list)

    def register_channel(self, channel_name: str, channel: NotificationChannel) -> None:
        self.channels.setdefault(channel_name, []).append(channel)

    def route(self, notification: Notification) -> List[bool]:
        results: List[bool] = []

        channels = self.channels.get(notification.channel, [])
        if not channels:
            default_channels = self.channels.get("default", [])
            channels = default_channels

        for channel in channels:
            try:
                success = channel.send(notification)
                results.append(success)
            except Exception:
                results.append(False)

        self.notification_log.append(notification)
        if len(self.notification_log) > self.max_notifications:
            self.notification_log = self.notification_log[-self.max_notifications:]

        return results

    def get_log(self, channel: Optional[str] = None, limit: int = 50) -> List[Notification]:
        results = self.notification_log
        if channel is not None:
            results = [n for n in results if n.channel == channel]
        return results[-limit:]

    def clear(self) -> None:
        self.notification_log.clear()
