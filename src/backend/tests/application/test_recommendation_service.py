from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.dtos.portfolio_dtos import PortfolioDTO, PositionDTO
from app.application.dtos.watchlist_dtos import Watchlist, WatchlistItem
from app.application.services.recommendation_service import RecommendationService
from app.domain.entities.recommendation import RecommendationAction, RecommendationPriority
from app.providers.market.base import IndexData, Indices, MarketOverview, MarketRegime


def _make_market_overview(regime: MarketRegime = MarketRegime.BULL, temperature: int = 65):
    return MarketOverview(
        marketRegime=regime,
        temperature=temperature,
        indices=Indices(
            shanghai=IndexData(code="000001", name="上证指数", price=3300.0, change_pct=1.5),
            shenzhen=IndexData(code="399001", name="深证成指", price=11000.0, change_pct=2.0),
            chi_next=IndexData(code="399006", name="创业板指", price=2200.0, change_pct=1.8),
        ),
        turnover=8500.0,
        upCount=2500,
        downCount=1800,
        northbound=50.0,
        hotIndustries=[],
        hotConcepts=[],
        summary="",
    )


def _make_portfolio():
    return PortfolioDTO(
        id="p1", name="我的组合", cash=Decimal("500000"),
        totalAssets=Decimal("704000"), totalCost=Decimal("190000"),
        totalMarketValue=Decimal("204000"), totalPnl=Decimal("14000"),
        totalPnlPct=Decimal("7.37"), positionCount=2,
        positions=[
            PositionDTO(
                id="pos1", symbol="600519", name="贵州茅台",
                shares=Decimal("100"), costPrice=Decimal("1500"),
                currentPrice=Decimal("1600"), marketValue=Decimal("160000"),
                pnl=Decimal("10000"), pnlPct=Decimal("6.67"),
                weightPct=Decimal("22.73"),
            ),
            PositionDTO(
                id="pos2", symbol="000858", name="五粮液",
                shares=Decimal("200"), costPrice=Decimal("200"),
                currentPrice=Decimal("220"), marketValue=Decimal("44000"),
                pnl=Decimal("4000"), pnlPct=Decimal("10"),
                weightPct=Decimal("6.25"),
            ),
        ],
    )


def _make_loss_portfolio():
    return PortfolioDTO(
        id="p1", name="亏损组合", cash=Decimal("100000"),
        totalAssets=Decimal("160000"), totalCost=Decimal("200000"),
        totalMarketValue=Decimal("60000"), totalPnl=Decimal("-140000"),
        totalPnlPct=Decimal("-70"), positionCount=1,
        positions=[
            PositionDTO(
                id="pos1", symbol="000001", name="平安银行",
                shares=Decimal("5000"), costPrice=Decimal("25"),
                currentPrice=Decimal("12"), marketValue=Decimal("60000"),
                pnl=Decimal("-65000"), pnlPct=Decimal("-52"),
                weightPct=Decimal("37.50"),
            ),
        ],
    )


def _make_watchlist():
    return Watchlist(
        id="wl1", name="我的关注", color="#3b82f6", sortOrder=0,
        items=[
            WatchlistItem(id="wi1", symbol="300750", name="宁德时代", tags=[], note="", sortOrder=0),
        ],
        itemCount=1,
    )


@pytest.mark.asyncio
async def test_bull_market_recommendation():
    market_svc = MagicMock()
    market_svc.get_market_overview = AsyncMock(return_value=_make_market_overview(MarketRegime.BULL))

    portfolio_svc = MagicMock()
    portfolio_svc.get_portfolio = AsyncMock(return_value=None)

    watchlist_svc = MagicMock()
    watchlist_svc.list_watchlists = AsyncMock(return_value=[])
    watchlist_svc.get_watchlist = AsyncMock(return_value=None)

    svc = RecommendationService(market_svc, portfolio_svc, watchlist_svc)
    result = await svc.get_recommendations("user1")

    assert len(result.items) >= 1
    market_item = next(i for i in result.items if i.symbol == "MARKET")
    assert market_item.action == RecommendationAction.BUY
    assert "牛市" in market_item.reason


@pytest.mark.asyncio
async def test_bear_market_recommendation():
    market_svc = MagicMock()
    market_svc.get_market_overview = AsyncMock(return_value=_make_market_overview(MarketRegime.BEAR))

    portfolio_svc = MagicMock()
    portfolio_svc.get_portfolio = AsyncMock(return_value=None)

    watchlist_svc = MagicMock()
    watchlist_svc.list_watchlists = AsyncMock(return_value=[])
    watchlist_svc.get_watchlist = AsyncMock(return_value=None)

    svc = RecommendationService(market_svc, portfolio_svc, watchlist_svc)
    result = await svc.get_recommendations("user1")

    market_item = next(i for i in result.items if i.symbol == "MARKET")
    assert market_item.action == RecommendationAction.WATCH
    assert "熊市" in market_item.reason


@pytest.mark.asyncio
async def test_concentration_risk():
    market_svc = MagicMock()
    market_svc.get_market_overview = AsyncMock(return_value=_make_market_overview())

    portfolio_svc = MagicMock()
    portfolio_svc.get_portfolio = AsyncMock(return_value=_make_loss_portfolio())

    watchlist_svc = MagicMock()
    watchlist_svc.list_watchlists = AsyncMock(return_value=[])
    watchlist_svc.get_watchlist = AsyncMock(return_value=None)

    svc = RecommendationService(market_svc, portfolio_svc, watchlist_svc)
    result = await svc.get_recommendations("user1")

    concentration_items = [i for i in result.items if "30%" in i.reason and i.symbol == "000001"]
    assert len(concentration_items) >= 1
    assert concentration_items[0].action == RecommendationAction.SELL


@pytest.mark.asyncio
async def test_stop_loss():
    market_svc = MagicMock()
    market_svc.get_market_overview = AsyncMock(return_value=_make_market_overview())

    portfolio_svc = MagicMock()
    portfolio_svc.get_portfolio = AsyncMock(return_value=_make_loss_portfolio())

    watchlist_svc = MagicMock()
    watchlist_svc.list_watchlists = AsyncMock(return_value=[])
    watchlist_svc.get_watchlist = AsyncMock(return_value=None)

    svc = RecommendationService(market_svc, portfolio_svc, watchlist_svc)
    result = await svc.get_recommendations("user1")

    stop_loss_items = [i for i in result.items if "止损" in i.reason and i.symbol == "000001"]
    assert len(stop_loss_items) >= 1
    assert stop_loss_items[0].action == RecommendationAction.SELL


@pytest.mark.asyncio
async def test_watchlist_not_held_recommended():
    market_svc = MagicMock()
    market_svc.get_market_overview = AsyncMock(return_value=_make_market_overview(MarketRegime.BULL))

    portfolio_svc = MagicMock()
    portfolio_svc.get_portfolio = AsyncMock(return_value=_make_portfolio())

    watchlist_svc = MagicMock()
    watchlist_svc.list_watchlists = AsyncMock(return_value=[_make_watchlist()])
    watchlist_svc.get_watchlist = AsyncMock(return_value=_make_watchlist())

    svc = RecommendationService(market_svc, portfolio_svc, watchlist_svc)
    result = await svc.get_recommendations("user1")

    watchlist_items = [i for i in result.items if i.symbol == "300750"]
    assert len(watchlist_items) >= 1
    assert watchlist_items[0].action == RecommendationAction.BUY
    assert "自选" in watchlist_items[0].reason


@pytest.mark.asyncio
async def test_items_sorted_by_priority():
    market_svc = MagicMock()
    market_svc.get_market_overview = AsyncMock(return_value=_make_market_overview())

    portfolio_svc = MagicMock()
    portfolio_svc.get_portfolio = AsyncMock(return_value=_make_loss_portfolio())

    watchlist_svc = MagicMock()
    watchlist_svc.list_watchlists = AsyncMock(return_value=[_make_watchlist()])
    watchlist_svc.get_watchlist = AsyncMock(return_value=_make_watchlist())

    svc = RecommendationService(market_svc, portfolio_svc, watchlist_svc)
    result = await svc.get_recommendations("user1")

    priorities = [i.priority.value for i in result.items]
    assert priorities == sorted(priorities)
