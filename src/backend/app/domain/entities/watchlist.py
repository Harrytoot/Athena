from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class WatchlistItem:
    id: Optional[str] = None
    symbol: str = ""
    name: str = ""
    tags: list[str] = field(default_factory=list)
    note: str = ""
    sort_order: int = 0
    created_at: Optional[datetime] = None

    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        if tag in self.tags:
            self.tags.remove(tag)


@dataclass
class Watchlist:
    id: Optional[str] = None
    name: str = ""
    color: str = "#3b82f6"
    sort_order: int = 0
    items: list[WatchlistItem] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def item_count(self) -> int:
        return len(self.items)

    def add_item(self, item: WatchlistItem):
        existing = [i for i in self.items if i.symbol == item.symbol]
        if existing:
            return
        item.sort_order = len(self.items)
        self.items.append(item)

    def remove_item(self, item_id: str):
        self.items = [i for i in self.items if i.id != item_id]

    def get_item(self, item_id: str) -> Optional[WatchlistItem]:
        for i in self.items:
            if i.id == item_id:
                return i
        return None
