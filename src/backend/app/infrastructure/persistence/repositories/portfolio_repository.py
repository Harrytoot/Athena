from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.portfolio import Portfolio, Position
from app.domain.repositories.portfolio_repository import PortfolioRepository
from app.infrastructure.persistence.models.portfolio import PortfolioModel, PositionModel


class PortfolioRepositoryImpl(PortfolioRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user(self, user_id: str) -> Optional[Portfolio]:
        stmt = (
            select(PortfolioModel)
            .where(PortfolioModel.user_id == UUID(user_id))
            .options(selectinload(PortfolioModel.positions))
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return _to_domain(model) if model else None

    async def create(self, user_id: str, name: str, cash: Decimal) -> Portfolio:
        model = PortfolioModel(user_id=UUID(user_id), name=name, cash=cash)
        self._session.add(model)
        await self._session.flush()
        return Portfolio(
            id=str(model.id),
            name=model.name,
            cash=model.cash,
            positions=[],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def add_position(self, portfolio_id: str, user_id: str, symbol: str, name: str, shares: Decimal, cost_price: Decimal) -> Optional[Portfolio]:
        stmt = (
            select(PortfolioModel)
            .where(PortfolioModel.id == UUID(portfolio_id), PortfolioModel.user_id == UUID(user_id))
            .options(selectinload(PortfolioModel.positions))
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        pos = PositionModel(symbol=symbol, name=name, shares=shares, cost_price=cost_price)
        model.positions.append(pos)
        await self._session.flush()
        return _to_domain(model)

    async def update_position(self, position_id: str, user_id: str, shares: Optional[Decimal], cost_price: Optional[Decimal]) -> Optional[Portfolio]:
        stmt = (
            select(PositionModel)
            .join(PortfolioModel)
            .where(PositionModel.id == UUID(position_id), PortfolioModel.user_id == UUID(user_id))
            .options(selectinload(PositionModel.portfolio).selectinload(PortfolioModel.positions))
        )
        result = await self._session.execute(stmt)
        pos = result.scalars().first()
        if not pos:
            return None
        if shares is not None:
            pos.shares = shares
        if cost_price is not None:
            pos.cost_price = cost_price
        await self._session.flush()
        return _to_domain(pos.portfolio)

    async def remove_position(self, position_id: str, user_id: str) -> bool:
        stmt = (
            select(PositionModel)
            .join(PortfolioModel)
            .where(PositionModel.id == UUID(position_id), PortfolioModel.user_id == UUID(user_id))
        )
        result = await self._session.execute(stmt)
        pos = result.scalars().first()
        if not pos:
            return False
        await self._session.delete(pos)
        await self._session.flush()
        return True


def _to_domain(model: PortfolioModel) -> Portfolio:
    positions = [_pos_to_domain(p) for p in model.positions] if model.positions else []
    return Portfolio(
        id=str(model.id),
        name=model.name,
        cash=model.cash,
        positions=positions,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _pos_to_domain(model: PositionModel) -> Position:
    return Position(
        id=str(model.id),
        symbol=model.symbol,
        name=model.name,
        shares=model.shares,
        cost_price=model.cost_price,
        current_price=model.current_price,
        created_at=model.created_at,
    )
