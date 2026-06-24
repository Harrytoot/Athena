from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    id: Optional[str] = None
    symbol: str
    name: str
    tags: list[str] = Field(default_factory=list)
    note: str = ""
    sort_order: int = Field(default=0, alias="sortOrder")
    current_price: Optional[float] = Field(default=None, alias="currentPrice")
    change_pct: Optional[float] = Field(default=None, alias="changePct")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    model_config = {"populate_by_name": True}


class Watchlist(BaseModel):
    id: Optional[str] = None
    name: str
    color: str = "#3b82f6"
    sort_order: int = Field(default=0, alias="sortOrder")
    items: list[WatchlistItem] = Field(default_factory=list)
    item_count: int = Field(default=0, alias="itemCount")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class WatchlistCreate(BaseModel):
    name: str
    color: str = "#3b82f6"


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")

    model_config = {"populate_by_name": True}


class WatchlistItemCreate(BaseModel):
    symbol: str
    name: str
    tags: list[str] = Field(default_factory=list)
    note: str = ""
