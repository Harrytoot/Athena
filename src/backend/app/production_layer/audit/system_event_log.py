from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import uuid


class EventType(Enum):
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    COMPONENT_INIT = "component_init"
    COMPONENT_SHUTDOWN = "component_shutdown"
    CONFIG_CHANGE = "config_change"
    DEGRADATION_ACTIVATE = "degradation_activate"
    DEGRADATION_DEACTIVATE = "degradation_deactivate"
    CIRCUIT_OPEN = "circuit_open"
    CIRCUIT_CLOSE = "circuit_close"
    RECOVERY_START = "recovery_start"
    RECOVERY_COMPLETE = "recovery_complete"
    HEALTH_CHECK_FAIL = "health_check_fail"
    HEALTH_CHECK_RECOVER = "health_check_recover"
    DATA_INCONSISTENCY = "data_inconsistency"
    BROKER_RECONNECT = "broker_reconnect"
    BROKER_DISCONNECT = "broker_disconnect"
    ALERT_GENERATED = "alert_generated"


@dataclass(frozen=True)
class SystemEvent:
    id: str
    event_type: EventType
    source: str
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "SystemEvent":
        return cls(
            id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            message=message,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
        )


@dataclass
class SystemEventLog:
    events: List[SystemEvent] = field(default_factory=list)
    max_events: int = 10000

    def log(
        self,
        event_type: EventType,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> SystemEvent:
        event = SystemEvent.create(event_type, source, message, details)
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        return event

    def get_by_type(self, event_type: EventType, limit: int = 50) -> List[SystemEvent]:
        matches = [e for e in self.events if e.event_type == event_type]
        return matches[-limit:]

    def get_by_source(self, source: str, limit: int = 50) -> List[SystemEvent]:
        matches = [e for e in self.events if e.source == source]
        return matches[-limit:]

    def get_recent(self, limit: int = 50) -> List[SystemEvent]:
        return self.events[-limit:]

    def count_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.events:
            key = e.event_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def clear(self) -> None:
        self.events.clear()
