from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.domain.entities.portfolio import Portfolio


class PortfolioRepository(ABC):

    @abstractmethod
    async def get_by_user(self, user_id: str) -> Optional[Portfolio]:
        ...

    @abstractmethod
    async def create(self, user_id: str, name: str, cash: Decimal) -> Portfolio:
        ...

    @abstractmethod
    async def add_position(self, portfolio_id: str, user_id: str, symbol: str, name: str, shares: Decimal, cost_price: Decimal) -> Optional[Portfolio]:
        ...

    @abstractmethod
    async def update_position(self, position_id: str, user_id: str, shares: Optional[Decimal], cost_price: Optional[Decimal]) -> Optional[Portfolio]:
        ...

    @abstractmethod
    async def remove_position(self, position_id: str, user_id: str) -> bool:
        ...
