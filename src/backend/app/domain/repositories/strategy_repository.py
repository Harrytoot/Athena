import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.infrastructure.persistence.models.strategy import StrategyModel


class StrategyRepository(ABC):

    @abstractmethod
    async def list_by_user(self, user_id: uuid.UUID) -> list[StrategyModel]:
        ...

    @abstractmethod
    async def get_by_id(self, strategy_id: uuid.UUID, user_id: uuid.UUID) -> Optional[StrategyModel]:
        ...

    @abstractmethod
    async def create(self, strategy: StrategyModel) -> StrategyModel:
        ...

    @abstractmethod
    async def update(self, strategy: StrategyModel) -> StrategyModel:
        ...

    @abstractmethod
    async def delete(self, strategy_id: uuid.UUID, user_id: uuid.UUID) -> None:
        ...

    @abstractmethod
    async def list_templates(self) -> list[StrategyModel]:
        ...

    @abstractmethod
    async def count_by_user(self, user_id: uuid.UUID) -> int:
        ...
