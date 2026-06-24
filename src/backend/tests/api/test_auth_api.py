from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import get_auth_service
from app.application.dtos.auth_dtos import TokenResponse
from app.application.services.auth_service import AuthService


@pytest.fixture
def mock_auth_svc():
    svc = MagicMock(spec=AuthService)
    svc.register = AsyncMock(return_value=TokenResponse(
        accessToken="test-token",
        userId="user-123",
        username="testuser",
        displayName="Test User",
    ))
    svc.login = AsyncMock(return_value=TokenResponse(
        accessToken="test-token",
        userId="user-123",
        username="testuser",
        displayName="Test User",
    ))
    return svc


class TestAuthAPI:

    def test_login_success(self, client, mock_auth_svc):
        from app.main import app
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_svc

        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["accessToken"] == "test-token"
        assert data["username"] == "testuser"

    def test_login_wrong_password(self, client, mock_auth_svc):
        mock_auth_svc.login = AsyncMock(return_value=None)
        from app.main import app
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_svc

        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrong",
        })
        assert response.status_code == 401

    def test_register_success(self, client, mock_auth_svc):
        from app.main import app
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_svc

        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password123",
            "displayName": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["accessToken"] == "test-token"

    def test_register_duplicate(self, client, mock_auth_svc):
        mock_auth_svc.register = AsyncMock(return_value=None)
        from app.main import app
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_svc

        response = client.post("/api/v1/auth/register", json={
            "username": "existing",
            "email": "existing@test.com",
            "password": "password123",
        })
        assert response.status_code == 409

    def test_me_unauthorized(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
