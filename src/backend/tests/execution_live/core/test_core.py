import pytest
from decimal import Decimal

from app.execution_live.core.risk_guard import RiskGuard, RiskGuardConfig, RiskCheckResult
from app.execution_live.core.execution_router import ExecutionRouter, RoutingConfig
from app.execution_live.core.position_sync import PositionSync, SyncAction
from app.domain.entities.portfolio import Portfolio, Position
from app.execution_live.broker.base import BrokerPosition, OrderSide


class TestRiskGuard:
    @pytest.fixture
    def guard(self):
        return RiskGuard(RiskGuardConfig(
            max_position_pct=Decimal("20"),
            max_single_order_pct=Decimal("10"),
            max_daily_loss_pct=Decimal("5"),
        ))

    def test_pass_normal_order(self, guard):
        result = guard.pre_trade_check(
            symbol="600000",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("50"),
            current_equity=Decimal("1000000"),
            current_cash=Decimal("500000"),
        )
        assert result.passed

    def test_large_order_rejected(self, guard):
        result = guard.pre_trade_check(
            symbol="600000",
            side="buy",
            quantity=Decimal("50000"),
            price=Decimal("50"),
            current_equity=Decimal("1000000"),
            current_cash=Decimal("500000"),
        )
        assert not result.passed
        assert len(result.violations) > 0

    def test_insufficient_cash(self, guard):
        result = guard.pre_trade_check(
            symbol="600000",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("100"),
            current_equity=Decimal("1000000"),
            current_cash=Decimal("1000"),
        )
        assert not result.passed

    def test_kill_switch_blocks(self, guard):
        guard.activate_kill_switch("Test emergency")
        result = guard.pre_trade_check(
            symbol="600000",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("50"),
            current_equity=Decimal("1000000"),
            current_cash=Decimal("500000"),
        )
        assert not result.passed
        assert any("Kill switch" in v for v in result.violations)

    def test_deactivate_kill_switch(self, guard):
        guard.activate_kill_switch("Test")
        guard.deactivate_kill_switch()
        result = guard.pre_trade_check(
            symbol="600000",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("50"),
            current_equity=Decimal("1000000"),
            current_cash=Decimal("500000"),
        )
        assert result.passed

    def test_position_limit(self, guard):
        result = guard.pre_trade_check(
            symbol="600000",
            side="buy",
            quantity=Decimal("50000"),
            price=Decimal("50"),
            current_positions={"600000": Decimal("150000")},
            current_equity=Decimal("1000000"),
            current_cash=Decimal("500000"),
        )
        assert not result.passed

    def test_record_trade_updates_turnover(self, guard):
        guard.record_trade(Decimal("50000"))
        stats = guard.get_daily_stats()
        assert Decimal(stats["daily_turnover"]) == Decimal("50000")

    def test_reset_daily(self, guard):
        guard.record_trade(Decimal("50000"))
        guard.record_pnl(Decimal("-1000"))
        guard.reset_daily()
        stats = guard.get_daily_stats()
        assert Decimal(stats["daily_pnl"]) == Decimal("0")
        assert Decimal(stats["daily_turnover"]) == Decimal("0")


class TestExecutionRouter:
    @pytest.fixture
    def router(self):
        return ExecutionRouter(RoutingConfig(max_slices=3, min_slice_notional=Decimal("500")))

    def test_route_portfolio_positions_buy(self):
        router = ExecutionRouter()
        portfolio = Portfolio(
            name="Test",
            cash=Decimal("1000000"),
            positions=[
                Position(symbol="600000", shares=Decimal("0"), cost_price=Decimal("0"), current_price=Decimal("50")),
            ],
        )
        target = {"600000": Decimal("100000")}
        orders = router.route_portfolio_positions(portfolio, target, {"600000": Decimal("50")})
        assert len(orders) > 0
        assert orders[0].symbol == "600000"
        assert orders[0].side == OrderSide.BUY

    def test_route_portfolio_positions_sell(self):
        router = ExecutionRouter()
        portfolio = Portfolio(
            name="Test",
            cash=Decimal("1000000"),
            positions=[
                Position(symbol="600000", shares=Decimal("1000"), cost_price=Decimal("40"), current_price=Decimal("50")),
            ],
        )
        target = {"600000": Decimal("10000")}
        orders = router.route_portfolio_positions(portfolio, target, {"600000": Decimal("50")})
        assert len(orders) > 0
        assert orders[0].side == OrderSide.SELL

    def test_slicing(self):
        router = ExecutionRouter(RoutingConfig(max_slices=3, min_slice_notional=Decimal("100")))
        portfolio = Portfolio(
            name="Test",
            cash=Decimal("1000000"),
            positions=[],
        )
        target = {"600000": Decimal("30000")}
        orders = router.route_portfolio_positions(portfolio, target, {"600000": Decimal("50")})
        assert len(orders) <= 3

    def test_route_batch(self):
        router = ExecutionRouter(RoutingConfig(max_slices=1, min_slice_notional=Decimal("100")))
        decisions = [
            {"symbol": "A", "side": OrderSide.BUY, "notional": "5000", "price": "50"},
            {"symbol": "B", "side": OrderSide.SELL, "notional": "3000", "price": "30"},
        ]
        orders = router.route_batch(decisions)
        assert len(orders) == 2
        assert orders[0].symbol == "A"
        assert orders[1].symbol == "B"

    def test_route_below_min_notional(self):
        router = ExecutionRouter(RoutingConfig(min_slice_notional=Decimal("10000")))
        portfolio = Portfolio(
            name="Test",
            cash=Decimal("1000000"),
            positions=[],
        )
        target = {"600000": Decimal("100")}
        orders = router.route_portfolio_positions(portfolio, target)
        assert len(orders) == 0


class TestPositionSync:
    def test_reconcile_no_diff(self):
        sync = PositionSync()
        portfolio = Portfolio(
            name="Test",
            positions=[Position(symbol="600000", shares=Decimal("100"), cost_price=Decimal("50"))],
        )
        broker_positions = [BrokerPosition(symbol="600000", quantity=Decimal("100"), average_price=Decimal("50"))]
        result = sync.reconcile(portfolio, broker_positions)
        assert result.reconciled

    def test_reconcile_add(self):
        sync = PositionSync()
        portfolio = Portfolio(name="Test", positions=[])
        broker_positions = [BrokerPosition(symbol="600000", quantity=Decimal("100"), average_price=Decimal("50"))]
        result = sync.reconcile(portfolio, broker_positions)
        assert not result.reconciled
        assert result.diffs[0].action == SyncAction.ADD
        assert result.diffs[0].broker_quantity == Decimal("100")

    def test_reconcile_remove(self):
        sync = PositionSync()
        portfolio = Portfolio(
            name="Test",
            positions=[Position(symbol="600000", shares=Decimal("100"), cost_price=Decimal("50"))],
        )
        result = sync.reconcile(portfolio, [])
        assert not result.reconciled
        assert result.diffs[0].action == SyncAction.REMOVE

    def test_reconcile_update_different_quantity(self):
        sync = PositionSync()
        portfolio = Portfolio(
            name="Test",
            positions=[Position(symbol="600000", shares=Decimal("100"), cost_price=Decimal("50"))],
        )
        broker_positions = [BrokerPosition(symbol="600000", quantity=Decimal("120"), average_price=Decimal("50"))]
        result = sync.reconcile(portfolio, broker_positions)
        assert not result.reconciled
        assert result.diffs[0].action == SyncAction.UPDATE
        assert result.diffs[0].delta_quantity == Decimal("20")

    def test_apply_sync_add(self):
        sync = PositionSync()
        portfolio = Portfolio(name="Test", positions=[])
        broker_positions = [BrokerPosition(symbol="600000", quantity=Decimal("100"), average_price=Decimal("50"))]
        sync_result = sync.reconcile(portfolio, broker_positions)
        updated = sync.apply_sync(portfolio, sync_result)
        assert len(updated.positions) == 1
        assert updated.positions[0].symbol == "600000"

    def test_apply_sync_remove(self):
        sync = PositionSync()
        portfolio = Portfolio(
            name="Test",
            positions=[Position(id="pos-1", symbol="600000", shares=Decimal("100"), cost_price=Decimal("50"))],
        )
        sync_result = sync.reconcile(portfolio, [])
        updated = sync.apply_sync(portfolio, sync_result)
        assert len(updated.positions) == 0

    def test_has_changes(self):
        sync = PositionSync()
        portfolio = Portfolio(name="Test", positions=[])
        result = sync.reconcile(portfolio, [])
        assert not result.has_changes
