from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import get_portfolio_service
from app.application.dtos.portfolio_dtos import PortfolioDTO, PositionDTO


@pytest.fixture
def mock_portfolio_svc():
    svc = MagicMock()
    svc.get_portfolio = AsyncMock(return_value=PortfolioDTO(
        id="pf-1",
        name="我的组合",
        cash=Decimal("100000"),
        totalAssets=Decimal("125000"),
        totalCost=Decimal("120000"),
        totalMarketValue=Decimal("25000"),
        totalPnl=Decimal("5000"),
        totalPnlPct=Decimal("4.17"),
        positionCount=2,
        positions=[
            PositionDTO(
                id="pos-1", symbol="600519", name="贵州茅台",
                shares=Decimal("10"), costPrice=Decimal("1600"),
                currentPrice=Decimal("1650"),
                marketValue=Decimal("16500"), pnl=Decimal("500"),
                pnlPct=Decimal("3.125"), weightPct=Decimal("13.2"),
            ),
        ],
    ))
    svc.create_portfolio = AsyncMock(return_value=PortfolioDTO(
        id="pf-new", name="新建组合", cash=Decimal("50000"),
        totalAssets=Decimal("50000"), totalCost=Decimal("0"),
        totalMarketValue=Decimal("0"), totalPnl=Decimal("0"),
        totalPnlPct=Decimal("0"), positionCount=0, positions=[],
    ))
    svc.add_position = AsyncMock(return_value=None)
    svc.update_position = AsyncMock(return_value=None)
    svc.remove_position = AsyncMock(return_value=True)
    return svc


class TestPortfolioAPI:

    def test_get_portfolio(self, client, mock_portfolio_svc):
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "我的组合"
        assert data["positionCount"] == 2
        assert len(data["positions"]) == 1

    def test_get_portfolio_not_found(self, client, mock_portfolio_svc):
        mock_portfolio_svc.get_portfolio = AsyncMock(return_value=None)
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.get("/api/v1/portfolio")
        assert response.status_code == 404

    def test_create_portfolio(self, client, mock_portfolio_svc):
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.post("/api/v1/portfolio", json={
            "name": "新建组合", "cash": 50000,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "新建组合"

    def test_add_position(self, client, mock_portfolio_svc):
        mock_portfolio_svc.add_position = AsyncMock(return_value=PortfolioDTO(
            id="pf-1", name="我的组合", cash=Decimal("100000"),
            totalAssets=Decimal("141500"), totalCost=Decimal("136500"),
            totalMarketValue=Decimal("41500"), totalPnl=Decimal("5000"),
            totalPnlPct=Decimal("3.66"), positionCount=2, positions=[],
        ))
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.post("/api/v1/portfolio/positions", json={
            "symbol": "000001", "name": "平安银行",
            "shares": 100, "costPrice": 15.00,
        })
        assert response.status_code == 201

    def test_update_position(self, client, mock_portfolio_svc):
        mock_portfolio_svc.update_position = AsyncMock(return_value=PortfolioDTO(
            id="pf-1", name="我的组合", cash=Decimal("100000"),
            totalAssets=Decimal("140500"), totalCost=Decimal("136000"),
            totalMarketValue=Decimal("40500"), totalPnl=Decimal("4500"),
            totalPnlPct=Decimal("3.31"), positionCount=2, positions=[],
        ))
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.patch("/api/v1/portfolio/positions/pos-1", json={
            "shares": 15,
        })
        assert response.status_code == 200

    def test_remove_position(self, client, mock_portfolio_svc):
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.delete("/api/v1/portfolio/positions/pos-1")
        assert response.status_code == 204

    def test_remove_position_not_found(self, client, mock_portfolio_svc):
        mock_portfolio_svc.remove_position = AsyncMock(return_value=False)
        from app.main import app
        app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_svc

        response = client.delete("/api/v1/portfolio/positions/nonexistent")
        assert response.status_code == 404
