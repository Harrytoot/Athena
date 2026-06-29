import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.strategy_repository import StrategyRepository
from app.infrastructure.persistence.models.strategy import StrategyModel


class StrategyRepositoryImpl(StrategyRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_user(self, user_id: uuid.UUID) -> list[StrategyModel]:
        stmt = select(StrategyModel).where(
            StrategyModel.user_id == user_id,
            StrategyModel.is_template == False,
        ).order_by(StrategyModel.updated_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, strategy_id: uuid.UUID, user_id: uuid.UUID) -> Optional[StrategyModel]:
        stmt = select(StrategyModel).where(
            StrategyModel.id == strategy_id,
            StrategyModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def create(self, strategy: StrategyModel) -> StrategyModel:
        self._session.add(strategy)
        await self._session.flush()
        return strategy

    async def update(self, strategy: StrategyModel) -> StrategyModel:
        await self._session.flush()
        return strategy

    async def delete(self, strategy_id: uuid.UUID, user_id: uuid.UUID) -> None:
        strategy = await self.get_by_id(strategy_id, user_id)
        if strategy:
            await self._session.delete(strategy)
            await self._session.flush()

    async def list_templates(self) -> list[StrategyModel]:
        stmt = select(StrategyModel).where(
            StrategyModel.is_template == True,
            StrategyModel.is_active == True,
        ).order_by(StrategyModel.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(StrategyModel).where(
            StrategyModel.user_id == user_id,
            StrategyModel.is_template == False,
        )
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))
