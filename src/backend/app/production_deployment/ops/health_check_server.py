from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import asyncio
import inspect
import json
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    component: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0.0
    last_checked: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "healthy": self.healthy,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "last_checked_iso": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_checked)
            ) if self.last_checked else None,
        }


@dataclass
class HealthReport:
    overall: bool
    components: list[HealthStatus] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp)),
            "uptime_seconds": round(self.uptime_seconds, 1),
            "components": [c.to_dict() for c in self.components],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class HealthCheckServer:
    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], Any]] = {}
        self._descriptions: dict[str, str] = {}
        self._start_time = time.time()
        self._status_cache: dict[str, HealthStatus] = {}
        self._cache_ttl: float = 5.0
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], Any],
        description: str = "",
    ) -> None:
        self._checks[name] = check_fn
        self._descriptions[name] = description
        logger.info("Health check registered: %s", name)

    def unregister_check(self, name: str) -> None:
        self._checks.pop(name, None)
        self._descriptions.pop(name, None)
        self._status_cache.pop(name, None)

    def register_component(
        self,
        name: str,
        check_fn: Callable[[], Any],
        description: str = "",
    ) -> None:
        self.register_check(name, check_fn, description)

    def mark_ready(self) -> None:
        self._ready = True
        logger.info("Health check server marked as ready")

    def mark_not_ready(self) -> None:
        self._ready = False

    async def check_component(self, name: str) -> Optional[HealthStatus]:
        check_fn = self._checks.get(name)
        if check_fn is None:
            return None

        start = time.time()
        try:
            result = check_fn()
            if inspect.iscoroutine(result):
                healthy = await result
            else:
                healthy = bool(result)
            latency = (time.time() - start) * 1000
            return HealthStatus(
                component=name,
                healthy=healthy,
                message="OK" if healthy else "FAILED",
                latency_ms=latency,
                last_checked=time.time(),
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthStatus(
                component=name,
                healthy=False,
                message=str(e),
                latency_ms=latency,
                last_checked=time.time(),
            )

    async def get_report(self, check_names: Optional[list[str]] = None) -> HealthReport:
        names = check_names if check_names else list(self._checks.keys())
        results: list[HealthStatus] = []

        tasks = []
        for name in names:
            if name in self._checks:
                tasks.append(self.check_component(name))

        gathered = await asyncio.gather(*tasks)
        for result in gathered:
            if result is not None:
                results.append(result)
                self._status_cache[result.component] = result

        overall = self._ready and all(r.healthy for r in results)

        return HealthReport(
            overall=overall,
            components=results,
            uptime_seconds=time.time() - self._start_time,
        )

    async def get_component_status(self, name: str) -> Optional[HealthStatus]:
        cached = self._status_cache.get(name)
        if cached and (time.time() - cached.last_checked) < self._cache_ttl:
            return cached

        status = await self.check_component(name)
        if status:
            self._status_cache[name] = status
        return status

    async def is_healthy(self) -> bool:
        report = await self.get_report()
        return report.overall

    def list_checks(self) -> dict[str, str]:
        return dict(self._descriptions)
