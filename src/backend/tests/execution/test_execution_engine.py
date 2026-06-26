import pytest

from app.execution.execution_engine import (
    ExecutionConfig,
    ExecutionEngine,
    ExecutionResult,
    ExecutedTrade,
)
from app.execution.liquidity_model import LiquidityConfig
from app.execution.slippage_engine import SlippageConfig
from app.execution.order_book_simulator import OrderBookConfig
from app.execution.trade_scheduler import LatencyConfig

from app.portfolio.portfolio_engine import (
    PortfolioReport,
    PortfolioComposition,
    PortfolioMetrics,
)
from app.portfolio.allocator import CapitalAllocation
from app.portfolio.rebalancer import RebalanceResult, RebalanceAction


def _make_rebalance_result(actions=None):
    if actions is None:
        actions = []
    return RebalanceResult(
        actions=actions,
        triggered=len(actions) > 0,
        trigger_reason="drift" if actions else "",
    )


def _make_action(strategy_id, side, delta=0.1):
    return RebalanceAction(
        strategy_id=strategy_id,
        action=side,
        from_capital=0.0,
        to_capital=0.0,
        delta=delta * (1 if side == "buy" else -1),
        delta_pct=abs(delta),
    )


def _make_portfolio_report(allocations=None):
    if allocations is None:
        allocations = []
    report = PortfolioReport()
    report.composition = PortfolioComposition(allocations=allocations)
    report.metrics = PortfolioMetrics()
    return report


def _make_allocation(strategy_id, weight=0.5, capital=500_000.0):
    return CapitalAllocation(
        strategy_id=strategy_id,
        weight=weight,
        capital=capital,
        risk_budget=0.0,
    )


class TestExecutedTrade:

    def test_execution_cost_from_slippage(self):
        from app.execution.slippage_engine import SlippageEstimate
        trade = ExecutedTrade(
            strategy_id="s1",
            action="buy",
            requested_notional=100_000,
            executed_notional=98_000,
            slippage=SlippageEstimate("s1", 100_000, 0.01, 0.001, 10.0, 10.0, "buy"),
        )
        assert trade.execution_cost == pytest.approx(10.0, rel=1e-4)

    def test_execution_cost_no_slippage(self):
        trade = ExecutedTrade(
            strategy_id="s1",
            action="buy",
            requested_notional=100_000,
            executed_notional=100_000,
        )
        assert trade.execution_cost == 0.0

    def test_is_filled_with_fill(self):
        from app.execution.order_book_simulator import FillResult
        from datetime import datetime
        trade = ExecutedTrade(
            strategy_id="s1",
            action="buy",
            requested_notional=100_000,
            executed_notional=100_000,
            fill_result=FillResult(
                order_id="o1", strategy_id="s1", side="buy",
                requested_quantity=1000, filled_quantity=1000,
                fill_ratio=1.0, average_price=100.0,
                execution_timestamp=datetime.now(),
            ),
        )
        assert trade.is_filled

    def test_is_filled_no_fill(self):
        trade = ExecutedTrade(
            strategy_id="s1",
            action="buy",
            requested_notional=100_000,
            executed_notional=0.0,
        )
        assert not trade.is_filled


class TestExecutionResult:

    def test_empty_trades(self):
        result = ExecutionResult()
        assert result.total_executed_notional == 0.0
        assert result.total_slippage_cost == 0.0
        assert result.total_fills == 0
        assert result.overall_fill_rate == 0.0

    def test_with_trades(self):
        from app.execution.order_book_simulator import FillResult
        from app.execution.slippage_engine import SlippageEstimate
        from datetime import datetime

        trades = [
            ExecutedTrade(
                strategy_id="s1", action="buy", requested_notional=100_000,
                executed_notional=95_000,
                fill_result=FillResult(
                    "o1", "s1", "buy", 1000, 950, 0.95, 100.0, datetime.now(),
                    partial_fill=True,
                ),
                slippage=SlippageEstimate("s1", 100_000, 0.01, 0.001, 5.0, 5.0, "buy"),
            ),
            ExecutedTrade(
                strategy_id="s2", action="sell", requested_notional=50_000,
                executed_notional=50_000,
                fill_result=FillResult(
                    "o2", "s2", "sell", 500, 500, 1.0, 100.0, datetime.now(),
                ),
                slippage=SlippageEstimate("s2", 50_000, 0.01, 0.001, 2.0, 1.0, "sell"),
            ),
        ]
        result = ExecutionResult(trades=trades)

        assert result.total_executed_notional == pytest.approx(145_000, rel=1e-4)
        assert result.total_slippage_cost == pytest.approx(6.0, rel=1e-4)
        assert result.total_fills == 2
        assert result.total_partial_fills == 1
        assert result.overall_fill_rate == pytest.approx(145000/150000, rel=1e-4)


class TestExecutionEngine:

    def test_execute_empty_rebalance(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report()
        rebalance = _make_rebalance_result([])
        result = engine.execute(report, rebalance)

        assert isinstance(result, ExecutionResult)
        assert len(result.trades) == 0

    def test_execute_no_rebalance(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report()
        result = engine.execute(report, None)

        assert isinstance(result, ExecutionResult)
        assert len(result.trades) == 0

    def test_execute_single_buy(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.5, 500_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "buy", 0.2),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0},
            volatility_map={"s1": 0.01},
        )

        assert len(result.trades) == 1
        assert result.trades[0].strategy_id == "s1"
        assert result.trades[0].action == "buy"
        assert result.trades[0].requested_notional > 0
        assert result.report is not None

    def test_execute_single_sell(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.5, 500_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "sell", 0.1),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0},
            volatility_map={"s1": 0.01},
        )

        assert len(result.trades) == 1
        assert result.trades[0].action == "sell"

    def test_execute_multiple_trades(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.4, 400_000),
            _make_allocation("s2", 0.6, 600_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "buy", 0.15),
            _make_action("s2", "sell", 0.10),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0, "s2": 100.0},
            volatility_map={"s1": 0.01, "s2": 0.02},
        )

        assert len(result.trades) == 2
        assert result.report is not None
        assert result.report.total_orders == 2

    def test_execute_with_schedule(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.5, 500_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "buy", 0.1),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0},
            volatility_map={"s1": 0.01},
        )

        assert result.schedule is not None
        trade = result.trades[0]
        assert trade.delay is not None
        assert trade.delay.delay_ms > 0

    def test_execute_fills_have_liquidity(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.5, 500_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "buy", 0.1),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0},
            volatility_map={"s1": 0.01},
        )

        trade = result.trades[0]
        assert trade.liquidity is not None
        assert trade.liquidity.strategy_id == "s1"
        assert trade.liquidity.daily_volume > 0

    def test_execute_fills_have_slippage(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.5, 500_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "buy", 0.1),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0},
            volatility_map={"s1": 0.01},
        )

        trade = result.trades[0]
        assert trade.slippage is not None
        assert trade.slippage.strategy_id == "s1"

    def test_execute_skips_hold_actions(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        report = _make_portfolio_report([
            _make_allocation("s1", 0.5, 500_000),
            _make_allocation("s2", 0.5, 500_000),
        ])
        rebalance = _make_rebalance_result([
            _make_action("s1", "buy", 0.1),
            _make_action("s2", "hold", 0.0),
        ])
        result = engine.execute(
            report, rebalance,
            target_prices={"s1": 100.0, "s2": 100.0},
            volatility_map={"s1": 0.01, "s2": 0.01},
        )

        assert len(result.trades) == 1
        assert result.trades[0].strategy_id == "s1"

    def test_execute_deterministic_seed(self):
        config = ExecutionConfig(seed=42)
        engine1 = ExecutionEngine(config=config)
        engine2 = ExecutionEngine(config=config)

        report1 = _make_portfolio_report([_make_allocation("s1", 0.5, 500_000)])
        report2 = _make_portfolio_report([_make_allocation("s1", 0.5, 500_000)])
        rebalance1 = _make_rebalance_result([_make_action("s1", "buy", 0.1)])
        rebalance2 = _make_rebalance_result([_make_action("s1", "buy", 0.1)])

        result1 = engine1.execute(report1, rebalance1, target_prices={"s1": 100.0}, volatility_map={"s1": 0.01})
        result2 = engine2.execute(report2, rebalance2, target_prices={"s1": 100.0}, volatility_map={"s1": 0.01})

        assert result1.trades[0].fill_result.fill_ratio == result2.trades[0].fill_result.fill_ratio

    def test_execute_allocations(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        current = [_make_allocation("s1", 0.4, 400_000), _make_allocation("s2", 0.6, 600_000)]
        target = [_make_allocation("s1", 0.6, 600_000), _make_allocation("s2", 0.4, 400_000)]

        result = engine.execute_allocations(
            current, target,
            target_prices={"s1": 100.0, "s2": 100.0},
            volatility_map={"s1": 0.01, "s2": 0.01},
        )

        assert len(result.trades) == 2
        actions = {t.strategy_id: t.action for t in result.trades}
        assert actions["s1"] == "buy"
        assert actions["s2"] == "sell"

    def test_execute_allocations_no_change(self):
        engine = ExecutionEngine(config=ExecutionConfig(seed=42))
        allocations = [_make_allocation("s1", 0.5, 500_000)]

        result = engine.execute_allocations(allocations, allocations)

        assert len(result.trades) == 0
