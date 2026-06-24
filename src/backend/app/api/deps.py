from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.market_service import MarketService
from app.infrastructure.persistence.session import async_session_factory
from app.providers.market.mock_provider import MockMarketProvider

_market_service = MarketService(provider=MockMarketProvider())


def get_market_service() -> MarketService:
    return _market_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
