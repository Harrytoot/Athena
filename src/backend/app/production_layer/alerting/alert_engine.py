from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid


class AlertSeverity(Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"

    def priority(self) -> int:
        return {AlertSeverity.INFO: 1, AlertSeverity.WARN: 2, AlertSeverity.CRITICAL: 3}[self]

    def __lt__(self, other: "AlertSeverity") -> bool:
        return self.priority() < other.priority()


@dataclass(frozen=True)
class Alert:
    id: str
    severity: AlertSeverity
    rule_name: str
    title: str
    message: str
    source: str
    context: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False

    @classmethod
    def create(
        cls,
        severity: AlertSeverity,
        rule_name: str,
        title: str,
        message: str,
        source: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> "Alert":
        return cls(
            id=str(uuid.uuid4()),
            severity=severity,
            rule_name=rule_name,
            title=title,
            message=message,
            source=source,
            context=context or {},
            timestamp=datetime.now(timezone.utc),
        )


@dataclass
class AlertRegistry:
    handlers: Dict[AlertSeverity, List[Callable[[Alert], None]]] = field(default_factory=dict)
    history: List[Alert] = field(default_factory=list)
    max_history: int = 1000
    dedup_window_seconds: int = 300

    def register_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]) -> None:
        self.handlers.setdefault(severity, []).append(handler)

    def _is_duplicate(self, alert: Alert) -> bool:
        cutoff = alert.timestamp.timestamp() - self.dedup_window_seconds
        for past in reversed(self.history):
            if past.timestamp.timestamp() < cutoff:
                break
            if past.rule_name == alert.rule_name and past.source == alert.source:
                return True
        return False

    def fire(self, alert: Alert) -> None:
        self.history.append(alert)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        handlers = self.handlers.get(alert.severity, [])
        for handler in handlers:
            try:
                handler(alert)
            except Exception:
                pass

    def get_alerts(
        self, severity: Optional[AlertSeverity] = None, limit: int = 50
    ) -> List[Alert]:
        results = self.history
        if severity is not None:
            results = [a for a in results if a.severity == severity]
        return results[-limit:]

    def count_by_severity(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for a in self.history:
            key = a.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def clear(self) -> None:
        self.history.clear()
        self.handlers.clear()
