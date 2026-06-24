from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import get_recommendation_service
from app.application.dtos.recommendation_dtos import RecommendationDTO, RecommendationItemDTO
from app.domain.entities.recommendation import RecommendationAction, RecommendationPriority, RecommendationSource


def _make_mock_recommendation():
    return RecommendationDTO(
        generatedAt=None,
        marketRegime="Bull",
        marketTemperature=65,
        items=[
            RecommendationItemDTO(
                symbol="MARKET", name="大盘",
                action=RecommendationAction.BUY,
                priority=RecommendationPriority.MEDIUM,
                source=RecommendationSource.MARKET,
                confidence=Decimal("75"),
                reason="市场处于牛市环境，适合增加仓位",
            ),
            RecommendationItemDTO(
                symbol="600519", name="贵州茅台",
                action=RecommendationAction.BUY,
                priority=RecommendationPriority.LOW,
                source=RecommendationSource.FUNDAMENTAL,
                confidence=Decimal("50"),
                reason="该股票在自选列表中但尚未持仓",
            ),
        ],
        summary="市场环境向好，可适度积极操作。",
    )


@pytest.fixture
def mock_recommendation_svc():
    svc = MagicMock()
    svc.get_recommendations = AsyncMock(return_value=_make_mock_recommendation())
    return svc


class TestRecommendationAPI:

    def test_get_recommendations_returns_200(self, client, mock_recommendation_svc):
        from app.main import app
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_svc

        response = client.get("/api/v1/recommendations")
        assert response.status_code == 200

    def test_get_recommendations_structure(self, client, mock_recommendation_svc):
        from app.main import app
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_svc

        response = client.get("/api/v1/recommendations")
        data = response.json()
        assert "marketRegime" in data
        assert "marketTemperature" in data
        assert "items" in data
        assert "summary" in data
        assert isinstance(data["items"], list)

    def test_recommendation_items_have_required_fields(self, client, mock_recommendation_svc):
        from app.main import app
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_svc

        response = client.get("/api/v1/recommendations")
        items = response.json()["items"]
        assert len(items) > 0
        for item in items:
            assert "symbol" in item
            assert "action" in item
            assert "confidence" in item
            assert "reason" in item
            assert "priority" in item
