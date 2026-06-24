from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.watchlist import Watchlist, WatchlistItem as DomainItem
from app.domain.repositories.watchlist_repository import WatchlistRepository
from app.infrastructure.persistence.models.watchlist import WatchlistItemModel, WatchlistModel


class WatchlistRepositoryImpl(WatchlistRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_user(self, user_id: str) -> list[Watchlist]:
        stmt = (
            select(WatchlistModel)
            .where(WatchlistModel.user_id == UUID(user_id))
            .options(selectinload(WatchlistModel.items))
            .order_by(WatchlistModel.sort_order)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().unique().all()
        return [_to_domain(m) for m in models]

    async def get_by_id(self, watchlist_id: str, user_id: str) -> Optional[Watchlist]:
        stmt = (
            select(WatchlistModel)
            .where(WatchlistModel.id == UUID(watchlist_id), WatchlistModel.user_id == UUID(user_id))
            .options(selectinload(WatchlistModel.items))
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return _to_domain(model) if model else None

    async def create(self, user_id: str, name: str, color: str) -> Watchlist:
        model = WatchlistModel(user_id=UUID(user_id), name=name, color=color)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def update(self, watchlist_id: str, user_id: str, name: Optional[str], color: Optional[str], sort_order: Optional[int]) -> Optional[Watchlist]:
        stmt = select(WatchlistModel).where(
            WatchlistModel.id == UUID(watchlist_id), WatchlistModel.user_id == UUID(user_id)
        ).options(selectinload(WatchlistModel.items))
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        if name is not None:
            model.name = name
        if color is not None:
            model.color = color
        if sort_order is not None:
            model.sort_order = sort_order
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def delete(self, watchlist_id: str, user_id: str) -> bool:
        stmt = select(WatchlistModel).where(
            WatchlistModel.id == UUID(watchlist_id), WatchlistModel.user_id == UUID(user_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def add_item(self, watchlist_id: str, user_id: str, symbol: str, name: str, tags: list[str], note: str) -> Optional[Watchlist]:
        stmt = (
            select(WatchlistModel)
            .where(WatchlistModel.id == UUID(watchlist_id), WatchlistModel.user_id == UUID(user_id))
            .options(selectinload(WatchlistModel.items))
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        max_order = max((i.sort_order for i in model.items), default=-1)
        item = WatchlistItemModel(
            watchlist_id=model.id, symbol=symbol, name=name, tags=list(tags), note=note, sort_order=max_order + 1,
        )
        model.items.append(item)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def remove_item(self, watchlist_id: str, item_id: str, user_id: str) -> bool:
        stmt = select(WatchlistItemModel).join(WatchlistModel).where(
            WatchlistItemModel.id == UUID(item_id),
            WatchlistItemModel.watchlist_id == UUID(watchlist_id),
            WatchlistModel.user_id == UUID(user_id),
        )
        result = await self._session.execute(stmt)
        item = result.scalars().first()
        if not item:
            return False
        await self._session.delete(item)
        await self._session.flush()
        return True


def _to_domain(model: WatchlistModel) -> Watchlist:
    items = [_item_to_domain(i) for i in model.items] if model.items else []
    return Watchlist(
        id=str(model.id),
        name=model.name,
        color=model.color or "#3b82f6",
        sort_order=model.sort_order or 0,
        items=items,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _item_to_domain(item: WatchlistItemModel) -> DomainItem:
    return DomainItem(
        id=str(item.id),
        symbol=item.symbol,
        name=item.name,
        tags=item.tags or [],
        note=item.note or "",
        sort_order=item.sort_order,
        created_at=item.created_at,
    )
