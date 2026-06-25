from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import get_stock_service
from app.providers.stock.detail_base import StockDetail


@pytest.fixture
def mock_stock_svc():
    svc = MagicMock()
    svc.get_stock_detail = AsyncMock(return_value=StockDetail(
        symbol="600519",
        name="贵州茅台",
        price=1650.00,
        changePct=1.25,
        open=1630.00,
        high=1660.00,
        low=1625.00,
        volume=5000000,
        turnover=8250000000.0,
        marketCap=25000000000000.0,
        peRatio=30.5,
        pbRatio=8.2,
    ))
    return svc


class TestStockAPI:

    def test_get_stock_detail(self, client, mock_stock_svc):
        from app.main import app
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_svc

        response = client.get("/api/v1/stocks/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "600519"
        assert data["name"] == "贵州茅台"

    def test_get_stock_detail_not_found(self, client, mock_stock_svc):
        mock_stock_svc.get_stock_detail = AsyncMock(return_value=None)
        from app.main import app
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_svc

        response = client.get("/api/v1/stocks/UNKNOWN")
        assert response.status_code == 404
