from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import deps
from app.api.v1 import auth, dashboard, market, portfolio, recommendation, stock, watchlist
from app.config import settings
from app.plugins import PluginRegistry

plugin_registry = PluginRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENV == "test":
        yield
        return
    await deps.ensure_default_user()
    await plugin_registry.discover_and_load()
    yield
    await plugin_registry.shutdown_all()


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
app.include_router(auth.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
