from datetime import datetime, timezone

import pytest

from app.strategy_robustness.transaction_cost import (
    CostEvent,
    TransactionCostConfig,
    TransactionCostSimulator,
    CostAdjustedHistory,
)
from tests.strategy_robustness import _build_history, _risk_result


class TestTransactionCostConfig:

    def test_default_config(self):
        cfg = TransactionCostConfig()
        assert cfg.commission_rate == 0.0003
        assert cfg.stamp_duty_rate == 0.0005
        assert cfg.apply_stamp_duty_sell_only is True

    def test_custom_config(self):
        cfg = TransactionCostConfig(
            commission_rate=0.0005,
            stamp_duty_rate=0.001,
            apply_stamp_duty_sell_only=False,
        )
        assert cfg.commission_rate == 0.0005
        assert cfg.stamp_duty_rate == 0.001
        assert cfg.apply_stamp_duty_sell_only is False


class TestTransactionCostSimulator:

    def test_empty_history(self):
        sim = TransactionCostSimulator()
        history = _build_history([], [])
        risk = _risk_result([])
        events = sim.simulate(history, risk)
        assert len(events) == 0

    def test_single_snapshot_no_costs(self):
        sim = TransactionCostSimulator()
        history = _build_history([1.0], [100.0])
        risk = _risk_result([1.0])
        events = sim.simulate(history, risk)
        assert len(events) == 0

    def test_no_position_change_no_costs(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [1.0, 1.0, 1.0],
            [100.0, 101.0, 102.0],
        )
        risk = _risk_result([1.0, 1.0, 1.0])
        events = sim.simulate(history, risk)
        assert len(events) == 2
        assert events[0].total_cost == 0.0
        assert events[1].total_cost == 0.0

    def test_turnover_generates_costs(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0])
        events = sim.simulate(history, risk)
        assert len(events) == 1
        assert events[0].turnover > 0
        assert events[0].commission > 0
        assert events[0].total_cost > 0

    def test_sell_generates_stamp_duty(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [1.0, 0.5],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0, 0.5])
        events = sim.simulate(history, risk)
        assert len(events) == 1
        assert events[0].stamp_duty > 0

    def test_buy_no_stamp_duty(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.5, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.5, 1.0])
        events = sim.simulate(history, risk)
        assert len(events) == 1
        assert events[0].stamp_duty == 0.0
        assert events[0].commission > 0

    def test_double_sided_stamp_duty(self):
        cfg = TransactionCostConfig(apply_stamp_duty_sell_only=False)
        sim = TransactionCostSimulator(config=cfg)
        history = _build_history(
            [0.5, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.5, 1.0])
        events = sim.simulate(history, risk)
        assert len(events) == 1
        assert events[0].stamp_duty > 0

    def test_min_commission_applied(self):
        cfg = TransactionCostConfig(min_commission=5.0, commission_rate=0.0)
        sim = TransactionCostSimulator(config=cfg)
        history = _build_history(
            [0.0, 0.001],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 0.001])
        events = sim.simulate(history, risk)
        assert events[0].commission == 5.0

    def test_compute_total_costs(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0, 0.5, 0.0],
            [100.0, 101.0, 102.0, 103.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5, 0.0])
        events = sim.simulate(history, risk)
        total = sim.compute_total_costs(events)
        assert total > 0
        assert total == pytest.approx(sum(e.total_cost for e in events), rel=1e-6)

    def test_cost_ratio(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0])
        events = sim.simulate(history, risk)
        ratio = sim.cost_ratio(history, events)
        assert ratio > 0
        assert ratio < 1.0

    def test_adjust_history_reduces_nav(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0, 1.0],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 1.0])
        events = sim.simulate(history, risk)
        adjusted = sim.adjust_history(history, events)

        assert len(adjusted.snapshots) == 3
        assert adjusted.snapshots[0].nav == history.snapshots[0].nav
        assert adjusted.snapshots[1].nav < history.snapshots[1].nav

    def test_cost_adjusted_sharpe_lower_than_raw(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0, 0.5, 1.0, 0.0] * 5,
            [100.0 + i * 0.5 for i in range(25)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5, 1.0, 0.0] * 5)
        events = sim.simulate(history, risk)
        adj_sharpe = sim.compute_cost_adjusted_sharpe(history, events)

        from app.strategy.pnl_analyzer import PnLAnalyzer
        analyzer = PnLAnalyzer()
        perf = analyzer.analyze(history)

        assert adj_sharpe <= perf.sharpe_ratio

    def test_cost_ratio_zero_nav(self):
        sim = TransactionCostSimulator()
        history = _build_history([], [], initial_nav=0.0)
        risk = _risk_result([])
        ratio = sim.cost_ratio(history, [])
        assert ratio == 0.0

    def test_multiple_turnover_events_accumulate(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0, -1.0, 0.5, -0.5],
            [100.0, 101.0, 99.0, 100.0, 98.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, -1.0, 0.5, -0.5])
        events = sim.simulate(history, risk)
        assert len(events) == 4
        total = sim.compute_total_costs(events)
        assert total > 0

    def test_cost_adjusted_history_daily_returns(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0, 1.0],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 1.0])
        events = sim.simulate(history, risk)
        adjusted = sim.adjust_history(history, events)
        assert len(adjusted.daily_returns) == 3

    def test_cost_adjusted_history_total_return(self):
        sim = TransactionCostSimulator()
        history = _build_history(
            [0.0, 1.0, 0.5],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5])
        events = sim.simulate(history, risk)
        adjusted = sim.adjust_history(history, events)
        assert adjusted.total_return < history.total_return
