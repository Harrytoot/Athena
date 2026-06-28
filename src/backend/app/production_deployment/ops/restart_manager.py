from dataclasses import dataclass
from typing import Awaitable, Callable, Optional
import asyncio
import logging
import time

from app.production_deployment.runtime_manager import RuntimeManager, ComponentStatus

logger = logging.getLogger(__name__)


@dataclass
class RestartPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    reset_after_seconds: float = 300.0


@dataclass
class RestartRecord:
    component_name: str
    attempt: int = 0
    first_failure: float = 0.0
    last_failure: float = 0.0
    last_restart: float = 0.0
    total_restarts: int = 0


class RestartManager:
    def __init__(
        self,
        runtime_manager: RuntimeManager,
        policy: Optional[RestartPolicy] = None,
    ) -> None:
        self._runtime = runtime_manager
        self._policy = policy or RestartPolicy()
        self._records: dict[str, RestartRecord] = {}
        self._enabled = True
        self._monitor_task: Optional[asyncio.Task] = None
        self._on_restart_callbacks: list[Callable[[str], Awaitable[None]]] = []
        self._on_failure_callbacks: list[Callable[[str, str], Awaitable[None]]] = []

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        logger.info("Restart manager enabled")

    def disable(self) -> None:
        self._enabled = False
        logger.info("Restart manager disabled")

    def on_restart(self, callback: Callable[[str], Awaitable[None]]) -> None:
        self._on_restart_callbacks.append(callback)

    def on_failure(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        self._on_failure_callbacks.append(callback)

    def get_record(self, component_name: str) -> Optional[RestartRecord]:
        return self._records.get(component_name)

    def get_all_records(self) -> dict[str, RestartRecord]:
        return dict(self._records)

    def reset_record(self, component_name: str) -> None:
        self._records.pop(component_name, None)
        component = self._runtime.get(component_name)
        if component:
            component.reset_counters()

    async def handle_failure(self, component_name: str) -> bool:
        if not self._enabled:
            logger.debug("Restart manager disabled, skipping restart for %s", component_name)
            return False

        component = self._runtime.get(component_name)
        if component is None:
            return False

        now = time.time()
        record = self._records.get(component_name)
        if record is None:
            record = RestartRecord(
                component_name=component_name,
                first_failure=now,
                last_failure=now,
            )
            self._records[component_name] = record

        if now - record.first_failure > self._policy.reset_after_seconds:
            record.attempt = 0
            record.first_failure = now

        record.attempt += 1
        record.last_failure = now

        if record.attempt > self._policy.max_retries:
            logger.error(
                "Component %s exceeded max retries (%d), giving up",
                component_name,
                self._policy.max_retries,
            )
            await self._notify_failure(
                component_name,
                f"Exceeded max retries ({self._policy.max_retries})",
            )
            return False

        delay = min(
            self._policy.base_delay_seconds * (self._policy.backoff_multiplier ** (record.attempt - 1)),
            self._policy.max_delay_seconds,
        )

        logger.warning(
            "Restarting %s (attempt %d/%d, delay %.1fs)",
            component_name,
            record.attempt,
            self._policy.max_retries,
            delay,
        )

        await asyncio.sleep(delay)
        success = await self._runtime.restart(component_name)

        if success:
            record.total_restarts += 1
            record.last_restart = now
            await self._notify_restart(component_name)
            logger.info("Component %s restarted successfully", component_name)
        else:
            await self._notify_failure(component_name, "Restart failed")
            await self.handle_failure(component_name)

        return success

    async def start_monitoring(self, interval_seconds: float = 10.0) -> None:
        if self._monitor_task is not None:
            return

        async def _monitor() -> None:
            while True:
                try:
                    await self._check_and_restart()
                except Exception as e:
                    logger.error("Monitor loop error: %s", e)
                await asyncio.sleep(interval_seconds)

        self._monitor_task = asyncio.ensure_future(_monitor())
        logger.info("Restart monitor started (interval=%ss)", interval_seconds)

    async def stop_monitoring(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        logger.info("Restart monitor stopped")

    async def _check_and_restart(self) -> None:
        if not self._enabled:
            return

        for name, status in self._runtime.get_status().items():
            if status == ComponentStatus.FAILED:
                await self.handle_failure(name)

    async def _notify_restart(self, component_name: str) -> None:
        for callback in self._on_restart_callbacks:
            try:
                await callback(component_name)
            except Exception as e:
                logger.error("Restart callback error: %s", e)

    async def _notify_failure(self, component_name: str, reason: str) -> None:
        for callback in self._on_failure_callbacks:
            try:
                await callback(component_name, reason)
            except Exception as e:
                logger.error("Failure callback error: %s", e)
