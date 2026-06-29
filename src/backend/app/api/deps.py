import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.application.services.backtest_service import BacktestService
from app.application.services.decision_service import DecisionService
from app.application.services.execution_service import ExecutionService
from app.application.services.market_score_service import MarketScoreService
from app.application.services.market_service import MarketService
from app.feature_store.repository import SQLAlchemyFeatureRepository
from app.application.services.portfolio_service import PortfolioService
from app.application.services.recommendation_service import RecommendationService
from app.application.services.stock_service import StockService
from app.application.services.watchlist_service import WatchlistService
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.watchlist import WatchlistModel
from app.infrastructure.persistence.repositories.portfolio_repository import PortfolioRepositoryImpl
from app.infrastructure.persistence.repositories.watchlist_repository import WatchlistRepositoryImpl
from app.infrastructure.persistence.session import async_session_factory
from app.providers.market.akshare_provider import AkShareMarketProvider
from app.providers.market.base import MarketProvider
from app.providers.market.mock_provider import MockMarketProvider
from app.providers.market.redis_provider import RedisMarketProvider
from app.providers.stock.redis_provider import RedisStockDetailProvider, RedisStockSearchProvider

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_EMAIL = "alpha@athena.local"


def _create_market_provider() -> MarketProvider:
    from app.config import settings
    provider_type = settings.MARKET_PROVIDER
    if provider_type == "redis":
        return RedisMarketProvider()
    elif provider_type == "akshare":
        return AkShareMarketProvider()
    else:
        return MockMarketProvider()


_market_service = MarketService(provider=_create_market_provider())
_stock_search_provider = RedisStockSearchProvider()
_stock_service = StockService(provider=RedisStockDetailProvider())


def get_market_service() -> MarketService:
    return _market_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_market_score_service(
    session: AsyncSession = Depends(get_db),
) -> MarketScoreService:
    repo = SQLAlchemyFeatureRepository(session)
    return MarketScoreService(feature_repo=repo)


async def get_decision_service(
    session: AsyncSession = Depends(get_db),
) -> DecisionService:
    repo = SQLAlchemyFeatureRepository(session)
    market_score_service = MarketScoreService(feature_repo=repo)
    return DecisionService(
        market_score_service=market_score_service,
        stock_service=_stock_service,
    )


async def get_execution_service(
    session: AsyncSession = Depends(get_db),
) -> ExecutionService:
    repo = SQLAlchemyFeatureRepository(session)
    market_score_service = MarketScoreService(feature_repo=repo)
    return ExecutionService(
        market_score_service=market_score_service,
        stock_service=_stock_service,
    )


def get_stock_service() -> StockService:
    return _stock_service


async def get_portfolio_service(session: AsyncSession = Depends(get_db)) -> PortfolioService:
    repo = PortfolioRepositoryImpl(session)
    return PortfolioService(repo)


async def get_recommendation_service(
    session: AsyncSession = Depends(get_db),
) -> RecommendationService:
    return RecommendationService(
        market_service=_market_service,
        portfolio_service=PortfolioService(PortfolioRepositoryImpl(session)),
        watchlist_service=WatchlistService(WatchlistRepositoryImpl(session), _stock_search_provider),
    )


async def get_watchlist_service(
    session: AsyncSession = Depends(get_db),
) -> WatchlistService:
    repo = WatchlistRepositoryImpl(session)
    return WatchlistService(repo, _stock_search_provider)


async def ensure_default_user():
    async with async_session_factory() as session:
        stmt = select(UserModel).where(UserModel.id == uuid.UUID(DEFAULT_USER_ID))
        result = await session.execute(stmt)
        if result.scalars().first() is None:
            user = UserModel(
                id=uuid.UUID(DEFAULT_USER_ID),
                username="alpha",
                email=DEFAULT_USER_EMAIL,
                password_hash="",
                display_name="Alpha User",
                is_active=True,
            )
            session.add(user)
            await session.commit()

        default_groups = [
            ("我的关注", "#3b82f6", 0),
            ("长线", "#22c55e", 1),
            ("波段", "#f59e0b", 2),
            ("短线", "#ef4444", 3),
            ("观察池", "#8b5cf6", 4),
        ]
        for name, color, sort_order in default_groups:
            stmt = select(WatchlistModel).where(
                WatchlistModel.user_id == uuid.UUID(DEFAULT_USER_ID),
                WatchlistModel.name == name,
            )
            result = await session.execute(stmt)
            if result.scalars().first() is None:
                    session.add(
                        WatchlistModel(
                            user_id=uuid.UUID(DEFAULT_USER_ID),
                            name=name,
                            color=color,
                            sort_order=sort_order,
                        )
                    )
        await session.commit()


security_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


async def get_backtest_service(
    session: AsyncSession = Depends(get_db),
) -> BacktestService:
    repo = SQLAlchemyFeatureRepository(session)
    return BacktestService(feature_repo=repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    service = AuthService(session)
    user = await service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效或已过期")
    return user
