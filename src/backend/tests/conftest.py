import os

os.environ["ENV"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    from app.main import lifespan
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
