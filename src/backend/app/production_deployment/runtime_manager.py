from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Optional
import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class ComponentStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class Component:
    name: str
    dependencies: list[str] = field(default_factory=list)
    start_fn: Optional[Callable[[], Awaitable[Any]]] = None
    stop_fn: Optional[Callable[[], Awaitable[Any]]] = None
    health_check_fn: Optional[Callable[[], Awaitable[bool]]] = None
    startup_timeout: float = 60.0
    restart_on_failure: bool = True

    status: ComponentStatus = ComponentStatus.STOPPED
    pid: Optional[int] = None
    last_started: float = 0.0
    last_stopped: float = 0.0
    restart_count: int = 0
    error_message: str = ""

    def reset_counters(self) -> None:
        self.restart_count = 0
        self.error_message = ""


class RuntimeManager:
    def __init__(self, max_restarts: int = 3, backoff_seconds: float = 1.0) -> None:
        self._components: dict[str, Component] = {}
        self._max_restarts = max_restarts
        self._backoff_seconds = backoff_seconds
        self._shutting_down = False

    def register(self, component: Component) -> None:
        self._components[component.name] = component
        logger.info("Component registered: %s", component.name)

    def unregister(self, name: str) -> None:
        self._components.pop(name, None)

    def get(self, name: str) -> Optional[Component]:
        return self._components.get(name)

    def list_components(self) -> list[Component]:
        return list(self._components.values())

    def get_status(self) -> dict[str, ComponentStatus]:
        return {name: comp.status for name, comp in self._components.items()}

    async def start_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        self._shutting_down = False

        for _ in range(len(self._components)):
            ready = [
                comp
                for comp in self._components.values()
                if comp.status == ComponentStatus.STOPPED
                and all(
                    self._components[dep].status == ComponentStatus.RUNNING
                    for dep in comp.dependencies
                    if dep in self._components
                )
            ]
            if not ready:
                remaining = [
                    comp.name
                    for comp in self._components.values()
                    if comp.status == ComponentStatus.STOPPED
                ]
                if remaining:
                    logger.error(
                        "Cannot start components due to unresolved dependencies: %s", remaining
                    )
                    for name in remaining:
                        results[name] = False
                break

            for comp in ready:
                results[comp.name] = await self._start_component(comp)

        return results

    async def stop_all(self) -> dict[str, bool]:
        self._shutting_down = True
        results: dict[str, bool] = {}

        for _ in range(len(self._components)):
            stoppable = [
                comp
                for comp in self._components.values()
                if comp.status in (
                    ComponentStatus.RUNNING,
                    ComponentStatus.RESTARTING,
                    ComponentStatus.FAILED,
                )
            ]

            dependents = {
                name
                for name, comp in self._components.items()
                if any(dep == name for dep in comp.dependencies)
            }

            ready = [c for c in stoppable if c.name not in dependents or all(
                self._components[dep].status not in (
                    ComponentStatus.RUNNING, ComponentStatus.STARTING
                )
                for dep in self._components[c.name].dependencies
                if dep in self._components
            )]

            if not ready:
                break

            for comp in ready:
                results[comp.name] = await self._stop_component(comp)

        return results

    async def restart(self, name: str) -> bool:
        comp = self._components.get(name)
        if comp is None:
            logger.error("Unknown component: %s", name)
            return False

        await self._stop_component(comp)
        return await self._start_component(comp)

    async def restart_all(self) -> dict[str, bool]:
        await self.stop_all()
        for comp in self._components.values():
            comp.status = ComponentStatus.STOPPED
        return await self.start_all()

    def is_all_running(self) -> bool:
        if not self._components:
            return True
        return all(
            comp.status == ComponentStatus.RUNNING
            for comp in self._components.values()
        )

    def is_any_failed(self) -> bool:
        return any(
            comp.status == ComponentStatus.FAILED
            for comp in self._components.values()
        )

    async def health_check_all(self) -> dict[str, bool]:
        results = {}
        for name, comp in self._components.items():
            if comp.status == ComponentStatus.RUNNING and comp.health_check_fn:
                try:
                    results[name] = await comp.health_check_fn()
                except Exception:
                    results[name] = False
            else:
                results[name] = comp.status == ComponentStatus.RUNNING
        return results

    async def _start_component(self, component: Component) -> bool:
        if component.start_fn is None:
            component.status = ComponentStatus.RUNNING
            component.last_started = time.time()
            logger.info("Component %s marked as running (no start function)", component.name)
            return True

        component.status = ComponentStatus.STARTING
        component.last_started = time.time()
        try:
            await asyncio.wait_for(
                component.start_fn(), timeout=component.startup_timeout
            )
            component.status = ComponentStatus.RUNNING
            component.error_message = ""
            logger.info("Component %s started successfully", component.name)
            return True
        except asyncio.TimeoutError:
            component.status = ComponentStatus.FAILED
            component.error_message = "Startup timed out"
            logger.error("Component %s startup timed out after %ss", component.name, component.startup_timeout)
            return False
        except Exception as e:
            component.status = ComponentStatus.FAILED
            component.error_message = str(e)
            logger.error("Component %s failed to start: %s", component.name, e)
            return False

    async def _stop_component(self, component: Component) -> bool:
        component.status = ComponentStatus.STOPPING
        component.last_stopped = time.time()
        try:
            if component.stop_fn:
                await component.stop_fn()
            component.status = ComponentStatus.STOPPED
            component.error_message = ""
            component.reset_counters()
            logger.info("Component %s stopped successfully", component.name)
            return True
        except Exception as e:
            component.status = ComponentStatus.FAILED
            component.error_message = str(e)
            logger.error("Component %s failed to stop: %s", component.name, e)
            return False

    async def _handle_failure(self, component: Component) -> None:
        if self._shutting_down or not component.restart_on_failure:
            return

        if component.restart_count >= self._max_restarts:
            component.status = ComponentStatus.FAILED
            logger.error(
                "Component %s exceeded max restarts (%d), marking as FAILED",
                component.name,
                self._max_restarts,
            )
            return

        component.status = ComponentStatus.RESTARTING
        component.restart_count += 1
        delay = self._backoff_seconds * (2 ** (component.restart_count - 1))
        logger.warning(
            "Component %s restart attempt %d/%d after %ss delay",
            component.name,
            component.restart_count,
            self._max_restarts,
            delay,
        )

        await asyncio.sleep(delay)
        await self._stop_component(component)
        await self._start_component(component)
