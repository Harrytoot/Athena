import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import deps
from app.api.v1 import auth, backtest, dashboard, decision, execution, market, portfolio, recommendation, stock, strategy, watchlist
from app.config import settings
from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.session import async_session_factory, engine
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.observation_scheduler import ObservationModeScheduler
from app.ingestion.scheduler import IngestionScheduler
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


def _import_all_models():
    import app.infrastructure.persistence.models.user  # noqa
    import app.infrastructure.persistence.models.portfolio  # noqa
    import app.infrastructure.persistence.models.watchlist  # noqa
    import app.infrastructure.persistence.models.strategy  # noqa
    import app.feature_store.models  # noqa


async def _dev_init_db():
    if settings.DEV_MODE and settings.DATABASE_URL.startswith("sqlite"):
        _import_all_models()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Dev mode: database tables created via metadata.create_all()")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ingestion_scheduler, _observation_scheduler
    if settings.ENV == "test":
        yield
        return

    _import_all_models()
    await _dev_init_db()

    _env_switcher.detect_from_env()
    await _secret_manager.load_for_environment(_env_switcher.current_type)

    await deps.ensure_default_user()
    await plugin_registry.discover_and_load()

    if settings.BOOTSTRAP_ON_STARTUP:
        try:
            from app.system_bootstrap.universe_loader import get_universe_loader
            from app.providers.market.mock_provider import MockMarketProvider
            from app.application.dtos.watchlist_dtos import WatchlistItemCreate
            from app.application.dtos.portfolio_dtos import PortfolioCreate, PositionCreate
            from app.application.services.portfolio_service import PortfolioService
            from app.application.services.watchlist_service import WatchlistService
            from app.infrastructure.persistence.repositories.portfolio_repository import PortfolioRepositoryImpl
            from app.infrastructure.persistence.repositories.watchlist_repository import WatchlistRepositoryImpl
            from decimal import Decimal

            loader = get_universe_loader()
            symbols = await asyncio.wait_for(loader.load(), timeout=60)
            logger.info("bootstrap: universe loaded %d symbols", len(symbols))

            async with async_session_factory() as session:
                from app.system_bootstrap.strategy_seeder import StrategySeeder
                seeder = StrategySeeder()
                strategy_ids = await seeder.seed(session, deps.DEFAULT_USER_ID)
                logger.info("bootstrap: seeded %d strategies", len(strategy_ids))

                wl_repo = WatchlistRepositoryImpl(session)
                wl_service = WatchlistService(wl_repo, deps._stock_search_provider)
                watchlists = await wl_service.list_watchlists(deps.DEFAULT_USER_ID)
                if watchlists:
                    target_wl = watchlists[0]
                    full = await wl_service.get_watchlist(target_wl.id, deps.DEFAULT_USER_ID)
                    if full and len(full.items) == 0:
                        for s in symbols[:10]:
                            try:
                                await wl_service.add_item(target_wl.id, deps.DEFAULT_USER_ID, WatchlistItemCreate(symbol=s["symbol"], name=s["name"]))
                            except Exception:
                                pass
                        logger.info("bootstrap: watchlist seeded")

                pt_repo = PortfolioRepositoryImpl(session)
                pt_service = PortfolioService(pt_repo)
                existing_portfolio = await pt_service.get_portfolio(deps.DEFAULT_USER_ID)
                if existing_portfolio is None:
                    await pt_service.create_portfolio(deps.DEFAULT_USER_ID, PortfolioCreate(name="初始组合", cash=Decimal("1000000")))
                    default_positions = [
                        {"symbol": "600519", "name": "贵州茅台", "shares": Decimal("100"), "costPrice": Decimal("1680.00")},
                        {"symbol": "300750", "name": "宁德时代", "shares": Decimal("500"), "costPrice": Decimal("185.00")},
                        {"symbol": "000858", "name": "五粮液", "shares": Decimal("300"), "costPrice": Decimal("142.00")},
                        {"symbol": "601318", "name": "中国平安", "shares": Decimal("1000"), "costPrice": Decimal("42.50")},
                        {"symbol": "002415", "name": "海康威视", "shares": Decimal("800"), "costPrice": Decimal("32.80")},
                    ]
                    for pos in default_positions:
                        await pt_service.add_position(deps.DEFAULT_USER_ID, PositionCreate(symbol=pos["symbol"], name=pos["name"], shares=pos["shares"], costPrice=pos["costPrice"]))
                    logger.info("bootstrap: portfolio seeded")
                await session.commit()

            provider = MockMarketProvider()
            ingestion = IngestionService(session_factory=async_session_factory)
            result = await asyncio.wait_for(
                ingestion.run_manual(provider=provider),
                timeout=30,
            )
            logger.info("bootstrap: ingestion pipeline done, features=%d", result.get("features_written", 0))
        except asyncio.TimeoutError:
            logger.warning("Bootstrap timed out")
        except Exception as e:
            logger.error("Bootstrap failed: %s", e, exc_info=True)

    ingestion_service = IngestionService(session_factory=async_session_factory)
    _ingestion_scheduler = IngestionScheduler(service=ingestion_service)
    _ingestion_scheduler.start()

    if not settings.DEV_MODE:
        akshare_provider = AkShareMarketProvider()
        try:
            logger.info("Running startup hydration (30s timeout)...")
            await asyncio.wait_for(
                ingestion_service.run_manual(provider=akshare_provider),
                timeout=30,
            )
            overview = await asyncio.wait_for(
                akshare_provider.get_overview(),
                timeout=15,
            )
            await asyncio.wait_for(
                ingestion_service.cache_overview_to_redis(overview),
                timeout=10,
            )
            logger.info("Startup hydration complete: temperature=%d", overview.temperature)
        except asyncio.TimeoutError:
            logger.warning("Startup hydration timed out, continuing with cached/default data")
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
app.include_router(strategy.router, prefix="/api/v1")
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
