from abc import ABC, abstractmethod
from typing import Optional

from app.application.dtos.watchlist_dtos import Watchlist


class WatchlistRepository(ABC):

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[Watchlist]:
        ...

    @abstractmethod
    async def get_by_id(self, watchlist_id: str, user_id: str) -> Optional[Watchlist]:
        ...

    @abstractmethod
    async def create(self, user_id: str, name: str, color: str) -> Watchlist:
        ...

    @abstractmethod
    async def update(self, watchlist_id: str, user_id: str, name: Optional[str], color: Optional[str], sort_order: Optional[int]) -> Optional[Watchlist]:
        ...

    @abstractmethod
    async def delete(self, watchlist_id: str, user_id: str) -> bool:
        ...

    @abstractmethod
    async def add_item(self, watchlist_id: str, user_id: str, symbol: str, name: str, tags: list[str], note: str) -> Optional[Watchlist]:
        ...

    @abstractmethod
    async def remove_item(self, watchlist_id: str, item_id: str, user_id: str) -> bool:
        ...
