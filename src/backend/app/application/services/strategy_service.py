import uuid

from app.application.dtos.strategy_dtos import (
    StrategyCreateRequest,
    StrategyResponse,
    StrategyUpdateRequest,
)
from app.domain.repositories.strategy_repository import StrategyRepository
from app.infrastructure.persistence.models.strategy import StrategyModel


class StrategyService:

    def __init__(self, repo: StrategyRepository):
        self._repo = repo

    async def list_strategies(self, user_id: str) -> list[StrategyResponse]:
        models = await self._repo.list_by_user(uuid.UUID(user_id))
        return [self._to_response(m) for m in models]

    async def get_strategy(self, strategy_id: str, user_id: str) -> StrategyResponse | None:
        model = await self._repo.get_by_id(uuid.UUID(strategy_id), uuid.UUID(user_id))
        if model is None:
            return None
        return self._to_response(model)

    async def create_strategy(self, user_id: str, data: StrategyCreateRequest) -> StrategyResponse:
        model = StrategyModel(
            user_id=uuid.UUID(user_id),
            name=data.name,
            description=data.description,
            category=data.category,
            nodes_json=data.nodes,
            edges_json=data.edges,
            is_template=data.is_template,
        )
        created = await self._repo.create(model)
        return self._to_response(created)

    async def update_strategy(self, strategy_id: str, user_id: str, data: StrategyUpdateRequest) -> StrategyResponse | None:
        model = await self._repo.get_by_id(uuid.UUID(strategy_id), uuid.UUID(user_id))
        if model is None:
            return None
        if data.name is not None:
            model.name = data.name
        if data.description is not None:
            model.description = data.description
        if data.nodes is not None:
            model.nodes_json = data.nodes
        if data.edges is not None:
            model.edges_json = data.edges
        if data.is_active is not None:
            model.is_active = data.is_active
        updated = await self._repo.update(model)
        return self._to_response(updated)

    async def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        model = await self._repo.get_by_id(uuid.UUID(strategy_id), uuid.UUID(user_id))
        if model is None:
            return False
        await self._repo.delete(uuid.UUID(strategy_id), uuid.UUID(user_id))
        return True

    async def list_templates(self) -> list[StrategyResponse]:
        models = await self._repo.list_templates()
        return [self._to_response(m) for m in models]

    async def count_strategies(self, user_id: str) -> int:
        return await self._repo.count_by_user(uuid.UUID(user_id))

    @staticmethod
    def _to_response(model: StrategyModel) -> StrategyResponse:
        return StrategyResponse(
            id=str(model.id),
            name=model.name,
            description=model.description,
            category=model.category,
            nodes=model.nodes_json,
            edges=model.edges_json,
            is_template=model.is_template,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
