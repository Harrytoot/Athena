from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, Optional
import asyncio
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class FailoverRole(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    STANDBY = "standby"
    OFFLINE = "offline"


class FailoverReason(str, Enum):
    MANUAL = "manual"
    HEALTH_FAILURE = "health_failure"
    TIMEOUT = "timeout"
    ADMIN = "admin"
    UNKNOWN = "unknown"


@dataclass
class InstanceInfo:
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: FailoverRole = FailoverRole.STANDBY
    host: str = ""
    port: int = 0
    last_heartbeat: float = 0.0
    is_healthy: bool = True
    priority: int = 0


@dataclass
class FailoverEvent:
    timestamp: float = field(default_factory=time.time)
    reason: FailoverReason = FailoverReason.UNKNOWN
    from_instance: str = ""
    to_instance: str = ""
    details: str = ""


class FailoverController:
    def __init__(
        self,
        instance_id: Optional[str] = None,
        heartbeat_interval: float = 10.0,
        lease_duration: float = 30.0,
    ) -> None:
        self._instance = InstanceInfo(
            instance_id=instance_id or str(uuid.uuid4())[:8],
            role=FailoverRole.STANDBY,
        )
        self._peers: dict[str, InstanceInfo] = {}
        self._heartbeat_interval = heartbeat_interval
        self._lease_duration = lease_duration
        self._history: list[FailoverEvent] = []
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._enabled = False
        self._on_promote_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._on_demote_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._heartbeat_callbacks: list[Callable[[InstanceInfo], Awaitable[None]]] = []

    @property
    def instance(self) -> InstanceInfo:
        return self._instance

    @property
    def role(self) -> FailoverRole:
        return self._instance.role

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def is_primary(self) -> bool:
        return self._instance.role == FailoverRole.PRIMARY

    @property
    def history(self) -> list[FailoverEvent]:
        return list(self._history)

    def register_peer(self, instance_id: str, host: str = "", port: int = 0, priority: int = 0) -> None:
        self._peers[instance_id] = InstanceInfo(
            instance_id=instance_id,
            role=FailoverRole.STANDBY,
            host=host,
            port=port,
            priority=priority,
        )
        logger.info("Peer registered: %s (priority=%d)", instance_id, priority)

    def remove_peer(self, instance_id: str) -> None:
        self._peers.pop(instance_id, None)

    def get_peers(self) -> list[InstanceInfo]:
        return list(self._peers.values())

    async def promote_to_primary(self, reason: FailoverReason = FailoverReason.MANUAL) -> FailoverEvent:
        previous_role = self._instance.role
        self._instance.role = FailoverRole.PRIMARY
        self._instance.last_heartbeat = time.time()

        event = FailoverEvent(
            reason=reason,
            from_instance=self._instance.instance_id,
            to_instance=self._instance.instance_id,
            details=f"Promoted from {previous_role.value} to PRIMARY",
        )
        self._history.append(event)
        logger.info("Instance %s promoted to PRIMARY (reason: %s)", self._instance.instance_id, reason.value)

        for callback in self._on_promote_callbacks:
            try:
                await callback()
            except Exception as e:
                logger.error("Promote callback error: %s", e)

        return event

    async def demote_to_standby(self, reason: FailoverReason = FailoverReason.MANUAL) -> FailoverEvent:
        previous_role = self._instance.role
        self._instance.role = FailoverRole.STANDBY

        event = FailoverEvent(
            reason=reason,
            from_instance=self._instance.instance_id,
            to_instance=self._instance.instance_id,
            details=f"Demoted from {previous_role.value} to STANDBY",
        )
        self._history.append(event)
        logger.info("Instance %s demoted to STANDBY (reason: %s)", self._instance.instance_id, reason.value)

        for callback in self._on_demote_callbacks:
            try:
                await callback()
            except Exception as e:
                logger.error("Demote callback error: %s", e)

        return event

    async def failover_to_peer(self, target_id: str, reason: FailoverReason) -> Optional[FailoverEvent]:
        target = self._peers.get(target_id)
        if target is None:
            logger.error("Failover target not found: %s", target_id)
            return None

        if not target.is_healthy:
            logger.warning("Failover target %s is not healthy", target_id)
            return None

        await self.demote_to_standby(reason)

        event = FailoverEvent(
            reason=reason,
            from_instance=self._instance.instance_id,
            to_instance=target_id,
            details=f"Failover to {target_id}",
        )
        self._history.append(event)

        logger.info(
            "Failover initiated: %s -> %s (reason: %s)",
            self._instance.instance_id,
            target_id,
            reason.value,
        )

        return event

    def get_best_peer(self) -> Optional[InstanceInfo]:
        healthy_peers = [p for p in self._peers.values() if p.is_healthy]
        if not healthy_peers:
            return None
        healthy_peers.sort(key=lambda p: (-p.priority, p.last_heartbeat))
        return healthy_peers[0]

    def on_promote(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_promote_callbacks.append(callback)

    def on_demote(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_demote_callbacks.append(callback)

    def on_heartbeat(self, callback: Callable[[InstanceInfo], Awaitable[None]]) -> None:
        self._heartbeat_callbacks.append(callback)

    async def start_heartbeat(self) -> None:
        self._enabled = True

        async def _beat() -> None:
            while self._enabled:
                self._instance.last_heartbeat = time.time()
                for callback in self._heartbeat_callbacks:
                    try:
                        await callback(self._instance)
                    except Exception as e:
                        logger.error("Heartbeat callback error: %s", e)
                await asyncio.sleep(self._heartbeat_interval)

        self._heartbeat_task = asyncio.ensure_future(_beat())
        logger.info("Heartbeat started (interval=%ss)", self._heartbeat_interval)

    async def stop_heartbeat(self) -> None:
        self._enabled = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        logger.info("Heartbeat stopped")

    async def check_peer_health(self, instance_id: str, healthy: bool) -> None:
        peer = self._peers.get(instance_id)
        if peer:
            peer.is_healthy = healthy
            peer.last_heartbeat = time.time()

    async def attempt_auto_failover(self) -> Optional[FailoverEvent]:
        if not self.is_primary:
            logger.debug("Not primary, skipping auto-failover check")
            return None

        best_peer = self.get_best_peer()
        if best_peer is None:
            logger.warning("No healthy peer available for failover")
            return None

        return await self.failover_to_peer(best_peer.instance_id, FailoverReason.HEALTH_FAILURE)

    def get_event_history(self, limit: int = 20) -> list[FailoverEvent]:
        return self._history[-limit:]
