from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.config import settings
from app.plugins import PluginRegistry

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


plugin_registry = PluginRegistry()


@app.on_event("startup")
async def startup():
    await plugin_registry.discover_and_load()


@app.on_event("shutdown")
async def shutdown():
    await plugin_registry.shutdown_all()
