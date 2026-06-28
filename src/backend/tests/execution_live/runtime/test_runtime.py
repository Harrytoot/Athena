import pytest
from decimal import Decimal
from datetime import datetime, time, timezone

from app.execution_live.runtime.kill_switch import KillSwitch, KillSwitchState
from app.execution_live.runtime.scheduler import ExecutionScheduler, ScheduleConfig, ScheduleCycle
from app.execution_live.runtime.trading_engine import (
    TradingEngine,
    TradingEngineConfig,
    EngineCycleResult,
)
from app.execution_live.broker.mock_broker import MockBroker, MockBrokerConfig
from app.execution_live.broker.base import OrderSide
from app.domain.entities.portfolio import Portfolio, Position
from app.portfolio.portfolio_engine import PortfolioReport
from app.portfolio.allocator import CapitalAllocation
from app.portfolio.rebalancer import RebalanceResult, RebalanceAction
from app.execution_live.monitoring.execution_logger import ExecutionLogger


class TestKillSwitch:
    def test_initial_state(self):
        ks = KillSwitch()
        assert ks.state == KillSwitchState.DISARMED
        assert not ks.is_active()

    def test_arm_and_trigger(self):
        ks = KillSwitch()
        ks.arm()
        assert ks.is_armed()
        ks.trigger("Max daily loss reached")
        assert ks.is_active()
        assert ks.should_block()

    def test_reset(self):
        ks = KillSwitch()
        ks.arm()
        ks.trigger("Test")
        ks.reset()
        assert ks.state == KillSwitchState.DISARMED

    def test_check_conditions_daily_loss(self):
        ks = KillSwitch()
        ks.arm()
        triggered = ks.check_conditions(
            daily_pnl=Decimal("-60000"),
            max_daily_loss=Decimal("50000"),
        )
        assert triggered
        assert ks.is_active()

    def test_check_conditions_consecutive_failures(self):
        ks = KillSwitch()
        ks.arm()
        triggered = ks.check_conditions(
            consecutive_failures=10,
            max_consecutive_failures=10,
        )
        assert triggered

    def test_check_conditions_not_armed(self):
        ks = KillSwitch()
        triggered = ks.check_conditions(
            daily_pnl=Decimal("-999999"),
            max_daily_loss=Decimal("1"),
        )
        assert not triggered

    def test_auto_triggers_disabled(self):
        ks = KillSwitch()
        ks.arm()
        ks.disable_auto_triggers()
        triggered = ks.check_conditions(
            daily_pnl=Decimal("-999999"),
            max_daily_loss=Decimal("1"),
        )
        assert not triggered

    def test_status_report(self):
        ks = KillSwitch()
        ks.arm()
        ks.trigger("Test trigger")
        report = ks.status_report()
        assert report["state"] == "triggered"
        assert report["trigger_count"] == 1

    def test_position_anomaly_triggers(self):
        ks = KillSwitch()
        ks.arm()
        triggered = ks.check_conditions(position_anomaly=True)
        assert triggered
        assert "Position anomaly" in ks.get_last_trigger().reason


class TestExecutionScheduler:
    def _make_test_now(self):
        from datetime import datetime, timezone
        return datetime(2026, 6, 24, 10, 0, tzinfo=timezone.utc)

    def test_should_run_first_time(self):
        scheduler = ExecutionScheduler()
        now = self._make_test_now()
        assert scheduler.should_run(now=now)

    def test_should_not_run_if_paused(self):
        scheduler = ExecutionScheduler()
        now = self._make_test_now()
        scheduler.pause()
        assert not scheduler.should_run(now=now)

    def test_resume(self):
        scheduler = ExecutionScheduler()
        now = self._make_test_now()
        scheduler.pause()
        scheduler.resume()
        assert scheduler.should_run(now=now)

    def test_interval_wait(self):
        config = ScheduleConfig(cycle=ScheduleCycle.INTRADAY, interval_seconds=300)
        scheduler = ExecutionScheduler(config=config)
        now = self._make_test_now()
        scheduler.mark_run(now=now)
        assert not scheduler.should_run(now=now)

    def test_continuous_always_runs(self):
        config = ScheduleConfig(cycle=ScheduleCycle.CONTINUOUS)
        scheduler = ExecutionScheduler(config=config)
        now = self._make_test_now()
        assert scheduler.should_run(now=now)
        scheduler.mark_run(now=now)
        assert scheduler.should_run(now=now)

    def test_manual_never_runs(self):
        config = ScheduleConfig(cycle=ScheduleCycle.MANUAL)
        scheduler = ExecutionScheduler(config=config)
        assert not scheduler.should_run()

    def test_weekend_skip(self):
        config = ScheduleConfig(cycle=ScheduleCycle.CONTINUOUS, skip_weekends=True)
        scheduler = ExecutionScheduler(config=config)
        from datetime import datetime, timezone
        saturday = datetime(2026, 6, 27, 10, 0, tzinfo=timezone.utc)
        assert saturday.weekday() == 5
        should = scheduler.should_run(now=saturday)
        assert not should

    def test_is_trading_hours(self):
        config = ScheduleConfig(
            trading_start=time(9, 30),
            trading_end=time(15, 0),
            skip_weekends=False,
        )
        scheduler = ExecutionScheduler(config=config)
        import datetime as dt
        mid_day = dt.datetime(2026, 6, 24, 14, 0, tzinfo=timezone.utc)
        assert scheduler.is_trading_hours(now=mid_day)

    def test_reset_daily(self):
        scheduler = ExecutionScheduler()
        scheduler.mark_run()
        assert scheduler.total_cycles == 1
        scheduler.reset_daily()
        assert scheduler.total_cycles == 0


class TestTradingEngine:
    @pytest.fixture
    def mock_broker(self):
        return MockBroker(config=MockBrokerConfig(initial_cash=Decimal("1000000")))

    @pytest.fixture
    def engine(self, mock_broker):
        logger = ExecutionLogger()
        return TradingEngine(
            broker=mock_broker,
            config=TradingEngineConfig(),
            logger=logger,
        )

    def test_engine_status(self, engine):
        status = engine.get_status()
        assert status["connected"] is True
        assert "account" in status
        assert "orders" in status

    def test_run_cycle_no_orders(self, engine):
        result = engine.run_cycle()
        assert result.status == "no_orders"
        assert result.orders_routed == 0

    def test_run_cycle_with_targets(self, engine):
        target_positions = {"600000": Decimal("50000")}
        target_prices = {"600000": Decimal("50")}
        result = engine.run_cycle(
            target_positions=target_positions,
            target_prices=target_prices,
        )
        assert result.orders_routed > 0
        assert result.orders_filled >= 0

    def test_run_cycle_dry_run(self, mock_broker):
        logger = ExecutionLogger()
        engine = TradingEngine(
            broker=mock_broker,
            config=TradingEngineConfig(dry_run=True),
            logger=logger,
        )
        target_positions = {"600000": Decimal("50000")}
        target_prices = {"600000": Decimal("50")}
        result = engine.run_cycle(
            target_positions=target_positions,
            target_prices=target_prices,
        )
        assert result.orders_routed > 0
        assert result.orders_submitted == 0

    def test_kill_switch_blocks_cycle(self, engine):
        engine.kill_switch.arm()
        engine.kill_switch.trigger("Test block")
        target_positions = {"600000": Decimal("50000")}
        result = engine.run_cycle(target_positions=target_positions)
        assert result.status == "blocked_kill_switch"

    def test_run_scheduled_cycle(self, engine):
        from datetime import datetime, timezone
        now = datetime(2026, 6, 24, 10, 0, tzinfo=timezone.utc)
        target_positions = {"600000": Decimal("50000")}
        target_prices = {"600000": Decimal("50")}
        result = engine.run_scheduled_cycle(
            target_positions=target_positions,
            target_prices=target_prices,
            now=now,
        )
        assert result is not None
        assert engine.scheduler.total_cycles == 1

    def test_cycle_result_timing(self, engine):
        target_positions = {"600000": Decimal("50000")}
        target_prices = {"600000": Decimal("50")}
        result = engine.run_cycle(
            target_positions=target_positions,
            target_prices=target_prices,
        )
        assert result.duration_seconds >= 0
        assert result.completed_at is not None

    def test_get_cycle_history(self, engine):
        target_positions = {"600000": Decimal("50000")}
        target_prices = {"600000": Decimal("50")}
        engine.run_cycle(target_positions=target_positions, target_prices=target_prices)
        history = engine.get_cycle_history()
        assert len(history) >= 1

    def test_get_latency_stats(self, engine):
        target_positions = {"600000": Decimal("50000")}
        target_prices = {"600000": Decimal("50")}
        engine.run_cycle(target_positions=target_positions, target_prices=target_prices)
        stats = engine.get_latency_stats()
        assert "order_submit_mean_ms" in stats

    def test_execute_rebalance(self, engine):
        actions = [
            RebalanceAction(
                strategy_id="strat-1",
                action="buy",
                from_capital=0,
                to_capital=50000,
                delta=50000,
                delta_pct=0.05,
            ),
        ]
        rebalance_result = RebalanceResult(
            actions=actions,
            triggered=True,
            trigger_reason="new_allocation",
        )
        target_prices = {"strat-1": Decimal("50")}
        result = engine.execute_rebalance(
            rebalance_result=rebalance_result,
            target_prices=target_prices,
        )
        assert result.orders_routed > 0
        assert result.orders_filled >= 0

    def test_max_orders_per_cycle(self, mock_broker):
        logger = ExecutionLogger()
        config = TradingEngineConfig(max_orders_per_cycle=3)
        engine = TradingEngine(broker=mock_broker, config=config, logger=logger)
        target_positions = {
            "A": Decimal("10000"),
            "B": Decimal("10000"),
            "C": Decimal("10000"),
            "D": Decimal("10000"),
            "E": Decimal("10000"),
        }
        target_prices = {"A": Decimal("50"), "B": Decimal("50"), "C": Decimal("50"), "D": Decimal("50"), "E": Decimal("50")}
        result = engine.run_cycle(target_positions=target_positions, target_prices=target_prices)
        assert result.orders_submitted <= 3
