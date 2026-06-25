
from app.application.dtos.portfolio_dtos import PortfolioCreate, PortfolioDTO, PositionCreate, PositionDTO, PositionUpdate
from app.domain.entities.portfolio import Portfolio
from app.domain.repositories.portfolio_repository import PortfolioRepository


def _to_dto(p: Portfolio) -> PortfolioDTO:
    positions = []
    for pos in p.positions:
        weight = p.get_weight(pos)
        positions.append(PositionDTO(
            id=pos.id, symbol=pos.symbol, name=pos.name,
            shares=pos.shares, cost_price=pos.cost_price,
            current_price=pos.current_price,
            market_value=pos.market_value,
            pnl=pos.pnl, pnl_pct=pos.pnl_pct,
            weight_pct=weight, created_at=pos.created_at,
        ))
    return PortfolioDTO(
        id=p.id, name=p.name, cash=p.cash,
        total_assets=p.total_assets, total_cost=p.total_cost,
        total_market_value=p.total_market_value,
        total_pnl=p.total_pnl, total_pnl_pct=p.total_pnl_pct,
        position_count=p.position_count,
        positions=positions,
        created_at=p.created_at, updated_at=p.updated_at,
    )


class PortfolioService:

    def __init__(self, repository: PortfolioRepository):
        self._repo = repository

    async def get_portfolio(self, user_id: str) -> PortfolioDTO | None:
        result = await self._repo.get_by_user(user_id)
        return _to_dto(result) if result else None

    async def create_portfolio(self, user_id: str, data: PortfolioCreate) -> PortfolioDTO:
        result = await self._repo.create(user_id, data.name, data.cash)
        return _to_dto(result)

    async def add_position(self, user_id: str, data: PositionCreate) -> PortfolioDTO | None:
        portfolio = await self._repo.get_by_user(user_id)
        if not portfolio:
            return None
        result = await self._repo.add_position(
            portfolio.id, user_id, data.symbol, data.name, data.shares, data.cost_price,
        )
        return _to_dto(result) if result else None

    async def update_position(self, position_id: str, user_id: str, data: PositionUpdate) -> PortfolioDTO | None:
        result = await self._repo.update_position(position_id, user_id, data.shares, data.cost_price)
        return _to_dto(result) if result else None

    async def remove_position(self, position_id: str, user_id: str) -> bool:
        return await self._repo.remove_position(position_id, user_id)
