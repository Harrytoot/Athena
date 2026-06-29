import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import deps
from app.api.v1 import auth, backtest, dashboard, decision, execution, market, portfolio, recommendation, stock, watchlist
from app.config import settings
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.observation_scheduler import ObservationModeScheduler
from app.ingestion.scheduler import IngestionScheduler
from app.infrastructure.persistence.session import async_session_factory
from app.observation_preanalysis.strategy_batch_runner import StrategyBatchRunner
from app.plugins import PluginRegistry
from app.production_deployment import (
    EnvironmentSwitcher,
    SecretManager,
    RuntimeManager,
    Component,
    ServiceOrchestrator,
)
from app.production_deployment.ops import HealthCheckServer, FailoverController
from app.providers.market.akshare_provider import AkShareMarketProvider

logger = logging.getLogger(__name__)

plugin_registry = PluginRegistry()
_ingestion_scheduler: IngestionScheduler | None = None
_observation_scheduler: ObservationModeScheduler | None = None

_env_switcher = EnvironmentSwitcher()
_secret_manager = SecretManager.get_instance()
_runtime_manager = RuntimeManager(max_restarts=3, backoff_seconds=1.0)
_service_orchestrator = ServiceOrchestrator(runtime_manager=_runtime_manager)
_health_server = HealthCheckServer()
_failover_controller = FailoverController()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ingestion_scheduler, _observation_scheduler
    if settings.ENV == "test":
        yield
        return

    _env_switcher.detect_from_env()
    await _secret_manager.load_for_environment(_env_switcher.current_type)

    await deps.ensure_default_user()
    await plugin_registry.discover_and_load()

    ingestion_service = IngestionService(session_factory=async_session_factory)
    _ingestion_scheduler = IngestionScheduler(service=ingestion_service)
    _ingestion_scheduler.start()

    akshare_provider = AkShareMarketProvider()
    try:
        logger.info("Running startup hydration...")
        await ingestion_service.run_manual(provider=akshare_provider)
        overview = await akshare_provider.get_overview()
        await ingestion_service.cache_overview_to_redis(overview)
        logger.info("Startup hydration complete: temperature=%d", overview.temperature)
    except Exception:
        logger.warning("Startup hydration failed, system will serve cached/default data")

    if settings.REALTIME_ENABLED:
        batch_runner = StrategyBatchRunner(
            session_factory=async_session_factory,
            stock_service=deps._stock_service,
        )
        _observation_scheduler = ObservationModeScheduler(
            service=ingestion_service,
            fetch_provider=akshare_provider,
            batch_runner=batch_runner,
        )
        _observation_scheduler.start()
        logger.info("ObservationModeScheduler with pre-analysis started")

    _runtime_manager.register(Component(
        name="ingestion",
        dependencies=["database"],
        health_check_fn=lambda: True,
    ))

    _health_server.register_check(
        "runtime",
        _runtime_manager.is_all_running,
        "All runtime components are running",
    )
    _health_server.register_check(
        "ingestion",
        lambda: _ingestion_scheduler is not None,
        "Ingestion scheduler is active",
    )
    if _observation_scheduler is not None:
        _health_server.register_check(
            "observation",
            lambda: True,
            "Observation mode scheduler is active",
        )

    import os
    from app.production_deployment.deployment_config import deployment_config
    if deployment_config.FAILOVER_ENABLED and os.getenv("FAILOVER_ENABLED", "true").lower() != "false":
        await _failover_controller.start_heartbeat()

    _health_server.mark_ready()

    yield

    await _failover_controller.stop_heartbeat()

    if _observation_scheduler:
        _observation_scheduler.stop()

    if _ingestion_scheduler:
        _ingestion_scheduler.stop()

    await plugin_registry.shutdown_all()
    await _secret_manager.unload_environment(_env_switcher.current_type)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    lifespan=lifespan,
)

app.include_router(market.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(watchlist.router, prefix="/api/v1")
app.include_router(stock.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(recommendation.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(decision.router, prefix="/api/v1")
app.include_router(execution.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/health/deployment")
async def deployment_health():
    report = await _health_server.get_report()
    return {
        "status": "healthy" if report.overall else "degraded",
        "version": settings.APP_VERSION,
        "environment": _env_switcher.current_type.value,
        "components": {
            name: status.value
            for name, status in _runtime_manager.get_status().items()
        },
        "services": {
            name: svc.status.value
            for name, svc in _service_orchestrator.list_services()
        },
        "health_report": report.to_dict(),
    }
