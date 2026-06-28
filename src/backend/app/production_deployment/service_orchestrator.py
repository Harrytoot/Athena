from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import logging

from app.production_deployment.runtime_manager import RuntimeManager, Component

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    STOPPED = "stopped"


@dataclass
class ServiceNode:
    name: str
    dependencies: list[str] = field(default_factory=list)
    initialize_fn: Optional[Callable] = None
    shutdown_fn: Optional[Callable] = None
    health_check_fn: Optional[Callable] = None
    status: ServiceStatus = ServiceStatus.PENDING
    error_message: str = ""

    async def initialize(self) -> bool:
        self.status = ServiceStatus.INITIALIZING
        if self.initialize_fn:
            try:
                result = self.initialize_fn()
                if hasattr(result, "__await__"):
                    await result
                self.status = ServiceStatus.READY
                return True
            except Exception as e:
                self.status = ServiceStatus.STOPPED
                self.error_message = str(e)
                return False
        self.status = ServiceStatus.READY
        return True

    async def shutdown(self) -> bool:
        if self.shutdown_fn:
            try:
                result = self.shutdown_fn()
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Error shutting down %s: %s", self.name, e)
        self.status = ServiceStatus.STOPPED
        return True

    async def health_check(self) -> bool:
        if self.health_check_fn:
            try:
                result = self.health_check_fn()
                if hasattr(result, "__await__"):
                    return await result
                return bool(result)
            except Exception:
                return False
        return self.status == ServiceStatus.READY


class ServiceOrchestrator:
    def __init__(self, runtime_manager: Optional[RuntimeManager] = None) -> None:
        self._services: dict[str, ServiceNode] = {}
        self._runtime_manager = runtime_manager
        self._initialized = False

    def register_service(
        self,
        name: str,
        dependencies: Optional[list[str]] = None,
        initialize_fn: Optional[Callable] = None,
        shutdown_fn: Optional[Callable] = None,
        health_check_fn: Optional[Callable] = None,
    ) -> ServiceNode:
        node = ServiceNode(
            name=name,
            dependencies=dependencies or [],
            initialize_fn=initialize_fn,
            shutdown_fn=shutdown_fn,
            health_check_fn=health_check_fn,
        )
        self._services[name] = node
        logger.info("Service registered: %s (deps: %s)", name, node.dependencies)
        return node

    def unregister_service(self, name: str) -> None:
        self._services.pop(name, None)

    def get_service(self, name: str) -> Optional[ServiceNode]:
        return self._services.get(name)

    def list_services(self) -> list[ServiceNode]:
        return list(self._services.values())

    def get_graph(self) -> dict[str, list[str]]:
        return {name: list(node.dependencies) for name, node in self._services.items()}

    def get_startup_order(self) -> list[list[str]]:
        in_degree: dict[str, int] = {name: len(node.dependencies) for name, node in self._services.items()}
        adjacency: dict[str, list[str]] = {name: [] for name in self._services}
        for name, node in self._services.items():
            for dep in node.dependencies:
                if dep in adjacency:
                    adjacency[dep].append(name)

        queue = [name for name, deg in in_degree.items() if deg == 0]
        order: list[list[str]] = []

        while queue:
            order.append(list(queue))
            next_queue = []
            for current in queue:
                for dependent in adjacency.get(current, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_queue.append(dependent)
            queue = next_queue

        return order

    async def initialize_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        order = self.get_startup_order()

        for level in order:
            tasks = {}
            for name in level:
                service = self._services[name]
                deps_ready = all(
                    self._services[dep].status == ServiceStatus.READY
                    for dep in service.dependencies
                    if dep in self._services
                )
                if not deps_ready:
                    service.error_message = "Dependencies not ready"
                    results[name] = False
                    continue

                import asyncio
                tasks[name] = asyncio.ensure_future(service.initialize())

            for name, task in tasks.items():
                try:
                    results[name] = await task
                except Exception as e:
                    self._services[name].error_message = str(e)
                    self._services[name].status = ServiceStatus.STOPPED
                    results[name] = False

        self._initialized = all(results.values())
        return results

    async def shutdown_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        order = self.get_startup_order()

        for level in reversed(order):
            import asyncio
            tasks = {}
            for name in level:
                service = self._services[name]
                tasks[name] = asyncio.ensure_future(service.shutdown())

            for name, task in tasks.items():
                try:
                    results[name] = await task
                except Exception as e:
                    logger.error("Error shutting down %s: %s", name, e)
                    results[name] = False

        self._initialized = False
        return results

    async def restart_service(self, name: str) -> bool:
        service = self._services.get(name)
        if service is None:
            return False

        await service.shutdown()
        return await service.initialize()

    async def health_check_all(self) -> dict[str, bool]:
        results = {}
        for name, service in self._services.items():
            results[name] = await service.health_check()
        return results

    def is_all_ready(self) -> bool:
        return all(
            service.status == ServiceStatus.READY
            for service in self._services.values()
        )

    @property
    def initialized(self) -> bool:
        return self._initialized

    def bind_to_runtime(self, runtime_manager: RuntimeManager) -> None:
        self._runtime_manager = runtime_manager
        for name, service in self._services.items():
            component = Component(
                name=name,
                dependencies=service.dependencies,
                start_fn=service.initialize,
                stop_fn=service.shutdown,
                health_check_fn=service.health_check,
            )
            runtime_manager.register(component)
