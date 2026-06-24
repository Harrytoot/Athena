from app.application.dtos.watchlist_dtos import Watchlist, WatchlistCreate, WatchlistItemCreate, WatchlistUpdate
from app.domain.repositories.watchlist_repository import WatchlistRepository
from app.providers.stock.base import StockSearchProvider, StockSearchResult


class WatchlistService:

    def __init__(self, repository: WatchlistRepository, stock_provider: StockSearchProvider):
        self._repo = repository
        self._stock_provider = stock_provider

    async def list_watchlists(self, user_id: str) -> list[Watchlist]:
        return await self._repo.list_by_user(user_id)

    async def get_watchlist(self, watchlist_id: str, user_id: str) -> Watchlist | None:
        return await self._repo.get_by_id(watchlist_id, user_id)

    async def create_watchlist(self, user_id: str, data: WatchlistCreate) -> Watchlist:
        return await self._repo.create(user_id, data.name, data.color)

    async def update_watchlist(self, watchlist_id: str, user_id: str, data: WatchlistUpdate) -> Watchlist | None:
        return await self._repo.update(watchlist_id, user_id, data.name, data.color, data.sort_order)

    async def delete_watchlist(self, watchlist_id: str, user_id: str) -> bool:
        return await self._repo.delete(watchlist_id, user_id)

    async def add_item(self, watchlist_id: str, user_id: str, data: WatchlistItemCreate) -> Watchlist | None:
        return await self._repo.add_item(watchlist_id, user_id, data.symbol, data.name, data.tags, data.note)

    async def remove_item(self, watchlist_id: str, item_id: str, user_id: str) -> bool:
        return await self._repo.remove_item(watchlist_id, item_id, user_id)

    async def search_stocks(self, query: str, limit: int = 20) -> list[StockSearchResult]:
        return await self._stock_provider.search(query, limit)
