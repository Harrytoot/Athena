from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import get_watchlist_service
from app.application.dtos.watchlist_dtos import Watchlist, WatchlistItem


@pytest.fixture
def mock_watchlist_svc():
    svc = MagicMock()
    svc.list_watchlists = AsyncMock(return_value=[
        Watchlist(id="wl-1", name="我的关注", color="#3b82f6", sortOrder=0, items=[], itemCount=0),
        Watchlist(id="wl-2", name="长线", color="#22c55e", sortOrder=1, items=[], itemCount=0),
    ])
    svc.get_watchlist = AsyncMock(return_value=Watchlist(
        id="wl-1", name="我的关注", color="#3b82f6", sortOrder=0,
        items=[
            WatchlistItem(id="item-1", symbol="600519", name="贵州茅台", tags=["白酒"]),
        ],
        itemCount=1,
    ))
    svc.create_watchlist = AsyncMock(return_value=Watchlist(
        id="wl-new", name="新建分组", color="#ef4444", sortOrder=0, items=[], itemCount=0,
    ))
    svc.update_watchlist = AsyncMock(return_value=Watchlist(
        id="wl-1", name="更新后的分组", color="#f59e0b", sortOrder=1, items=[], itemCount=0,
    ))
    svc.delete_watchlist = AsyncMock(return_value=True)
    svc.add_item = AsyncMock(return_value=Watchlist(
        id="wl-1", name="我的关注", color="#3b82f6", sortOrder=0,
        items=[
            WatchlistItem(id="item-new", symbol="000001", name="平安银行"),
        ],
        itemCount=1,
    ))
    svc.remove_item = AsyncMock(return_value=True)
    svc.search_stocks = AsyncMock(return_value=[])
    return svc


class TestWatchlistAPI:

    def test_list_watchlists(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.get("/api/v1/watchlists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "我的关注"

    def test_create_watchlist(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.post("/api/v1/watchlists", json={"name": "新建分组"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "新建分组"

    def test_get_watchlist(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.get("/api/v1/watchlists/wl-1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "我的关注"
        assert data["itemCount"] == 1

    def test_get_watchlist_not_found(self, client, mock_watchlist_svc):
        mock_watchlist_svc.get_watchlist = AsyncMock(return_value=None)
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.get("/api/v1/watchlists/nonexistent")
        assert response.status_code == 404

    def test_update_watchlist(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.put("/api/v1/watchlists/wl-1", json={"name": "更新后的分组"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的分组"

    def test_delete_watchlist(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.delete("/api/v1/watchlists/wl-1")
        assert response.status_code == 204

    def test_delete_watchlist_not_found(self, client, mock_watchlist_svc):
        mock_watchlist_svc.delete_watchlist = AsyncMock(return_value=False)
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.delete("/api/v1/watchlists/nonexistent")
        assert response.status_code == 404

    def test_add_item(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.post("/api/v1/watchlists/wl-1/items", json={
            "symbol": "000001", "name": "平安银行",
        })
        assert response.status_code == 201

    def test_remove_item(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.delete("/api/v1/watchlists/wl-1/items/item-1")
        assert response.status_code == 204

    def test_search_stocks(self, client, mock_watchlist_svc):
        from app.main import app
        app.dependency_overrides[get_watchlist_service] = lambda: mock_watchlist_svc

        response = client.get("/api/v1/watchlists/stock/search?q=平安")
        assert response.status_code == 200
