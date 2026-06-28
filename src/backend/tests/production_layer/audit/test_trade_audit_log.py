from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.audit.trade_audit_log import (
    TradeAuditLog,
    TradeRecord,
    TradeAction,
    TradeStatus,
)


class TestTradeRecord:
    def test_create(self):
        tr = TradeRecord.create(
            order_id="ord-001",
            strategy_id="strat-a",
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=Decimal("100"),
            price=Decimal("150"),
            broker="alpaca",
        )
        assert tr.symbol == "AAPL"
        assert tr.action == TradeAction.BUY
        assert tr.status == TradeStatus.PENDING
        assert tr.filled_quantity == Decimal("0")
        assert len(tr.id) > 0

    def test_is_complete(self):
        tr = TradeRecord.create(
            order_id="o1", strategy_id="s1", symbol="AAPL",
            action=TradeAction.BUY, quantity=Decimal("100"),
            price=Decimal("150"), broker="a",
        )
        assert not tr.is_complete()


class TestTradeAuditLog:
    def test_record_trade(self):
        log = TradeAuditLog()
        tr = TradeRecord.create(
            order_id="o1", strategy_id="s1", symbol="AAPL",
            action=TradeAction.BUY, quantity=Decimal("100"),
            price=Decimal("150"), broker="alpaca",
        )
        log.record(tr)
        assert len(log.records) == 1

    def test_get_by_order_id(self):
        log = TradeAuditLog()
        tr = TradeRecord.create(
            order_id="o1", strategy_id="s1", symbol="AAPL",
            action=TradeAction.BUY, quantity=Decimal("100"),
            price=Decimal("150"), broker="a",
        )
        log.record(tr)
        found = log.get_by_order_id("o1")
        assert found is not None
        assert found.symbol == "AAPL"
        assert log.get_by_order_id("nonexistent") is None

    def test_get_by_symbol(self):
        log = TradeAuditLog()
        for i in range(5):
            log.record(TradeRecord.create(
                order_id=f"o{i}", strategy_id="s", symbol="AAPL",
                action=TradeAction.BUY, quantity=Decimal("10"),
                price=Decimal("100"), broker="a",
            ))
        for i in range(3):
            log.record(TradeRecord.create(
                order_id=f"g{i}", strategy_id="s", symbol="GOOG",
                action=TradeAction.SELL, quantity=Decimal("5"),
                price=Decimal("200"), broker="a",
            ))
        aapl = log.get_by_symbol("AAPL")
        goog = log.get_by_symbol("GOOG")
        assert len(aapl) == 5
        assert len(goog) == 3

    def test_get_by_strategy(self):
        log = TradeAuditLog()
        log.record(TradeRecord.create(
            order_id="o1", strategy_id="algo1", symbol="X",
            action=TradeAction.BUY, quantity=Decimal("1"),
            price=Decimal("10"), broker="a",
        ))
        log.record(TradeRecord.create(
            order_id="o2", strategy_id="algo2", symbol="Y",
            action=TradeAction.SELL, quantity=Decimal("1"),
            price=Decimal("20"), broker="a",
        ))
        assert len(log.get_by_strategy("algo1")) == 1
        assert len(log.get_by_strategy("algo2")) == 1

    def test_get_by_status(self):
        log = TradeAuditLog()
        tr = TradeRecord.create(
            order_id="o1", strategy_id="s", symbol="X",
            action=TradeAction.BUY, quantity=Decimal("1"),
            price=Decimal("10"), broker="a",
        )
        log.record(tr)
        pending = log.get_by_status(TradeStatus.PENDING)
        filled = log.get_by_status(TradeStatus.FILLED)
        assert len(pending) == 1
        assert len(filled) == 0

    def test_total_filled(self):
        log = TradeAuditLog()
        tr = TradeRecord.create(
            order_id="o1", strategy_id="s", symbol="AAPL",
            action=TradeAction.BUY, quantity=Decimal("100"),
            price=Decimal("150"), broker="a",
        )
        log.record(tr)
        assert log.get_total_filled("AAPL") == Decimal("0")

    def test_max_records(self):
        log = TradeAuditLog(max_records=10)
        for i in range(20):
            log.record(TradeRecord.create(
                order_id=f"o{i}", strategy_id="s", symbol="X",
                action=TradeAction.BUY, quantity=Decimal("1"),
                price=Decimal("10"), broker="a",
            ))
        assert len(log.records) <= 10

    def test_clear(self):
        log = TradeAuditLog()
        log.record(TradeRecord.create(
            order_id="o", strategy_id="s", symbol="X",
            action=TradeAction.BUY, quantity=Decimal("1"),
            price=Decimal("10"), broker="a",
        ))
        log.clear()
        assert len(log.records) == 0
