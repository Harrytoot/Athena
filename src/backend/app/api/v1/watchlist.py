
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import DEFAULT_USER_ID, get_watchlist_service
from app.application.dtos.watchlist_dtos import (
    Watchlist,
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistUpdate,
)
from app.application.services.watchlist_service import WatchlistService
from app.providers.stock.base import StockSearchResult

router = APIRouter(prefix="/watchlists", tags=["Watchlist"])


@router.get("", response_model=list[Watchlist])
async def list_watchlists(
    service: WatchlistService = Depends(get_watchlist_service),
):
    return await service.list_watchlists(DEFAULT_USER_ID)


@router.post("", response_model=Watchlist, status_code=201)
async def create_watchlist(
    data: WatchlistCreate,
    service: WatchlistService = Depends(get_watchlist_service),
):
    return await service.create_watchlist(DEFAULT_USER_ID, data)


@router.get("/{watchlist_id}", response_model=Watchlist)
async def get_watchlist(
    watchlist_id: str,
    service: WatchlistService = Depends(get_watchlist_service),
):
    result = await service.get_watchlist(watchlist_id, DEFAULT_USER_ID)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.put("/{watchlist_id}", response_model=Watchlist)
async def update_watchlist(
    watchlist_id: str,
    data: WatchlistUpdate,
    service: WatchlistService = Depends(get_watchlist_service),
):
    result = await service.update_watchlist(watchlist_id, DEFAULT_USER_ID, data)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(
    watchlist_id: str,
    service: WatchlistService = Depends(get_watchlist_service),
):
    ok = await service.delete_watchlist(watchlist_id, DEFAULT_USER_ID)
    if not ok:
        raise HTTPException(status_code=404, detail="Watchlist not found")


@router.post("/{watchlist_id}/items", response_model=Watchlist, status_code=201)
async def add_item(
    watchlist_id: str,
    data: WatchlistItemCreate,
    service: WatchlistService = Depends(get_watchlist_service),
):
    result = await service.add_item(watchlist_id, DEFAULT_USER_ID, data)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/{watchlist_id}/items/{item_id}", status_code=204)
async def remove_item(
    watchlist_id: str,
    item_id: str,
    service: WatchlistService = Depends(get_watchlist_service),
):
    ok = await service.remove_item(watchlist_id, item_id, DEFAULT_USER_ID)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")


@router.get("/stock/search", response_model=list[StockSearchResult])
async def search_stocks(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, le=50),
    service: WatchlistService = Depends(get_watchlist_service),
):
    return await service.search_stocks(q, limit)
