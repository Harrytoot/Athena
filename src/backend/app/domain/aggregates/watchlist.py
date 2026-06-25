from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.entities.watchlist import WatchlistItem


@dataclass
class WatchlistAggregate:
    id: Optional[str] = None
    user_id: str = ""
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
        exists = any(i.symbol == item.symbol for i in self.items)
        if not exists:
            item.sort_order = len(self.items)
            self.items.append(item)

    def remove_item(self, item_id: str):
        self.items = [i for i in self.items if i.id != item_id]

    def reorder_item(self, item_id: str, new_order: int):
        item = self._find_item(item_id)
        if item:
            item.sort_order = new_order

    def get_item_by_symbol(self, symbol: str) -> Optional[WatchlistItem]:
        for i in self.items:
            if i.symbol == symbol:
                return i
        return None

    def _find_item(self, item_id: str) -> Optional[WatchlistItem]:
        for i in self.items:
            if i.id == item_id:
                return i
        return None
