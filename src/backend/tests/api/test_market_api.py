from unittest.mock import AsyncMock

import pytest

from app.api.deps import get_market_service
from app.providers.market.base import (
    HotItem,
    IndexData,
    Indices,
    MarketOverview,
    MarketRegime,
)


@pytest.fixture
def mock_market_svc():
    svc = AsyncMock()
    svc.get_market_overview = AsyncMock(return_value=MarketOverview(
        marketRegime=MarketRegime.BULL,
        temperature=78,
        indices=Indices(
            shanghai=IndexData(code="000001", name="上证指数", price=3150.42, change_pct=0.85),
            shenzhen=IndexData(code="399001", name="深证成指", price=10420.35, change_pct=1.23),
            chi_next=IndexData(code="399006", name="创业板指", price=2150.18, change_pct=1.56),
        ),
        turnover=15600.0,
        upCount=3812,
        downCount=1286,
        northbound=58.7,
        hotIndustries=[HotItem(name="半导体", change_pct=4.2)],
        hotConcepts=[HotItem(name="光刻机", change_pct=3.1)],
        summary="市场震荡上行",
    ))
    svc.get_dashboard = AsyncMock(return_value={
        "marketRegime": "Bull",
        "temperature": 78,
        "summary": "市场震荡上行",
    })
    return svc


class TestMarketAPI:

    def test_get_market_overview(self, client, mock_market_svc):
        from app.main import app
        app.dependency_overrides[get_market_service] = lambda: mock_market_svc

        response = client.get("/api/v1/market/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["marketRegime"] == "Bull"
        assert data["temperature"] == 78

    def test_get_dashboard(self, client, mock_market_svc):
        from app.main import app
        app.dependency_overrides[get_market_service] = lambda: mock_market_svc

        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["marketRegime"] == "Bull"

    def test_market_overview_has_indices(self, client, mock_market_svc):
        from app.main import app
        app.dependency_overrides[get_market_service] = lambda: mock_market_svc

        response = client.get("/api/v1/market/overview")
        data = response.json()
        assert "indices" in data
        assert data["indices"]["shanghai"]["code"] == "000001"
