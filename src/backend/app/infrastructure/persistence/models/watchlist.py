import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base, TimestampMixin


class WatchlistModel(Base, TimestampMixin):
    __tablename__ = "watchlists"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#3b82f6")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    items: Mapped[list["WatchlistItemModel"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan", order_by="WatchlistItemModel.sort_order"
    )


class WatchlistItemModel(Base, TimestampMixin):
    __tablename__ = "watchlist_items"

    watchlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("watchlists.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=[])
    note: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    watchlist: Mapped["WatchlistModel"] = relationship(back_populates="items")
