from app.domain.aggregates.watchlist import WatchlistAggregate
from app.domain.entities.watchlist import WatchlistItem


class TestWatchlistAggregate:
    def test_create_watchlist(self):
        wl = WatchlistAggregate(user_id="user-1", name="核心持仓")
        assert wl.name == "核心持仓"
        assert wl.item_count == 0

    def test_add_item(self):
        wl = WatchlistAggregate(user_id="user-1", name="自选")
        item = WatchlistItem(symbol="600519", name="贵州茅台")
        wl.add_item(item)
        assert wl.item_count == 1

    def test_duplicate_item_not_added(self):
        wl = WatchlistAggregate(user_id="user-1", name="自选")
        wl.add_item(WatchlistItem(symbol="600519", name="贵州茅台"))
        wl.add_item(WatchlistItem(symbol="600519", name="贵州茅台"))
        assert wl.item_count == 1

    def test_remove_item(self):
        wl = WatchlistAggregate(user_id="user-1", name="自选")
        item = WatchlistItem(id="item-1", symbol="600519", name="贵州茅台")
        wl.add_item(item)
        wl.remove_item("item-1")
        assert wl.item_count == 0

    def test_find_by_symbol(self):
        wl = WatchlistAggregate(user_id="user-1", name="自选")
        wl.add_item(WatchlistItem(symbol="600519", name="贵州茅台"))
        found = wl.get_item_by_symbol("600519")
        assert found is not None
        assert found.name == "贵州茅台"

    def test_not_found_symbol(self):
        wl = WatchlistAggregate(user_id="user-1", name="自选")
        assert wl.get_item_by_symbol("000001") is None
