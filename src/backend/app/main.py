from fastapi import FastAPI

from app.api import deps
from app.api.v1 import dashboard, market, portfolio, recommendation, stock, watchlist
from app.config import settings
from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.models.portfolio import PortfolioModel, PositionModel  # noqa: F401
from app.infrastructure.persistence.models.user import UserModel  # noqa: F401
from app.infrastructure.persistence.models.watchlist import WatchlistModel, WatchlistItemModel  # noqa: F401
from app.infrastructure.persistence.session import engine
from app.plugins import PluginRegistry

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)

app.include_router(market.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(watchlist.router, prefix="/api/v1")
app.include_router(stock.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(recommendation.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


plugin_registry = PluginRegistry()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await deps.ensure_default_user()
    await plugin_registry.discover_and_load()


@app.on_event("shutdown")
async def shutdown():
    await plugin_registry.shutdown_all()
