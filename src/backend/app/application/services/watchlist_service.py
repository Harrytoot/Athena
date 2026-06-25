from app.application.dtos.watchlist_dtos import Watchlist as WatchlistDTO, WatchlistCreate, WatchlistItemCreate, WatchlistUpdate, WatchlistItem as WatchlistItemDTO
from app.domain.entities.watchlist import Watchlist
from app.domain.repositories.watchlist_repository import WatchlistRepository
from app.providers.stock.base import StockSearchProvider, StockSearchResult


def _to_dto(w: Watchlist) -> WatchlistDTO:
    items = [
        WatchlistItemDTO(
            id=i.id, symbol=i.symbol, name=i.name, tags=i.tags,
            note=i.note, sort_order=i.sort_order, created_at=i.created_at,
        )
        for i in w.items
    ]
    return WatchlistDTO(
        id=w.id, name=w.name, color=w.color, sort_order=w.sort_order,
        items=items, item_count=len(items), created_at=w.created_at, updated_at=w.updated_at,
    )


class WatchlistService:

    def __init__(self, repository: WatchlistRepository, stock_provider: StockSearchProvider):
        self._repo = repository
        self._stock_provider = stock_provider

    async def list_watchlists(self, user_id: str) -> list[WatchlistDTO]:
        result = await self._repo.list_by_user(user_id)
        return [_to_dto(r) for r in result]

    async def get_watchlist(self, watchlist_id: str, user_id: str) -> WatchlistDTO | None:
        result = await self._repo.get_by_id(watchlist_id, user_id)
        return _to_dto(result) if result else None

    async def create_watchlist(self, user_id: str, data: WatchlistCreate) -> WatchlistDTO:
        result = await self._repo.create(user_id, data.name, data.color)
        return _to_dto(result)

    async def update_watchlist(self, watchlist_id: str, user_id: str, data: WatchlistUpdate) -> WatchlistDTO | None:
        result = await self._repo.update(watchlist_id, user_id, data.name, data.color, data.sort_order)
        return _to_dto(result) if result else None

    async def delete_watchlist(self, watchlist_id: str, user_id: str) -> bool:
        return await self._repo.delete(watchlist_id, user_id)

    async def add_item(self, watchlist_id: str, user_id: str, data: WatchlistItemCreate) -> WatchlistDTO | None:
        result = await self._repo.add_item(watchlist_id, user_id, data.symbol, data.name, data.tags, data.note)
        return _to_dto(result) if result else None

    async def remove_item(self, watchlist_id: str, item_id: str, user_id: str) -> bool:
        return await self._repo.remove_item(watchlist_id, item_id, user_id)

    async def search_stocks(self, query: str, limit: int = 20) -> list[StockSearchResult]:
        return await self._stock_provider.search(query, limit)
