from unittest.mock import AsyncMock

import pytest

from app.api.deps import get_market_score_service, get_market_service
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


@pytest.fixture
def mock_market_score_svc():
    svc = AsyncMock()
    svc.get_score = AsyncMock(return_value={
        "score": 65,
        "regime": "Bull",
        "components": {
            "csi300": {"value": 1.2, "score": 62.0, "weight": 0.30},
            "turnover": {"value": 8500.0, "score": 65.0, "weight": 0.20},
            "breadth": {"value": 2800, "decliners": 1200, "score": 70.0, "weight": 0.25},
            "northbound": {"value": 5.8, "score": 59.67, "weight": 0.25},
        },
        "source": "real_data_v1",
        "updatedAt": "2025-01-01T12:00:00",
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


class TestMarketScoreAPI:

    def test_get_market_score_returns_structured_response(self, client, mock_market_score_svc):
        from app.main import app
        app.dependency_overrides[get_market_score_service] = lambda: mock_market_score_svc

        response = client.get("/api/v1/market/score")
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "components" in data
        assert "source" in data
        assert "updatedAt" in data

    def test_market_score_source_is_real_data_v1(self, client, mock_market_score_svc):
        from app.main import app
        app.dependency_overrides[get_market_score_service] = lambda: mock_market_score_svc

        response = client.get("/api/v1/market/score")
        data = response.json()
        assert data["source"] == "real_data_v1"

    def test_market_score_components_have_weights(self, client, mock_market_score_svc):
        from app.main import app
        app.dependency_overrides[get_market_score_service] = lambda: mock_market_score_svc

        response = client.get("/api/v1/market/score")
        data = response.json()
        components = data["components"]
        assert "csi300" in components
        assert "turnover" in components
        assert "breadth" in components
        assert "northbound" in components
        for key in components:
            assert "weight" in components[key]
            assert "score" in components[key]

    def test_market_score_breadth_has_decliners(self, client, mock_market_score_svc):
        from app.main import app
        app.dependency_overrides[get_market_score_service] = lambda: mock_market_score_svc

        response = client.get("/api/v1/market/score")
        data = response.json()
        assert data["components"]["breadth"]["decliners"] == 1200
