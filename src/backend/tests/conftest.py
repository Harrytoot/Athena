import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    startup_handlers = app.router.on_startup[:]
    shutdown_handlers = app.router.on_shutdown[:]
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    with TestClient(app) as c:
        yield c
    app.router.on_startup = startup_handlers
    app.router.on_shutdown = shutdown_handlers


@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
