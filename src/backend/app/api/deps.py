import uuid
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.market_service import MarketService
from app.application.services.watchlist_service import WatchlistService
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.watchlist import WatchlistModel
from app.infrastructure.persistence.repositories.watchlist_repository import WatchlistRepositoryImpl
from app.infrastructure.persistence.session import async_session_factory
from app.providers.market.mock_provider import MockMarketProvider
from app.providers.stock.mock_provider import MockStockSearchProvider

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_EMAIL = "alpha@athena.local"

_market_service = MarketService(provider=MockMarketProvider())
_stock_search_provider = MockStockSearchProvider()


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
