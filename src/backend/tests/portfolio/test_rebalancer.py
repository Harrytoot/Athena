from datetime import datetime, timezone, timedelta

import pytest

from app.portfolio.weight_optimizer import StrategyWeight, WeightResult
from app.portfolio.allocator import CapitalAllocation
from app.portfolio.rebalancer import Rebalancer, RebalanceAction, RebalanceResult


def _make_weight_result(strategy_ids, weights):
    sws = [
        StrategyWeight(
            strategy_id=sid,
            raw_sharpe=1.0,
            cost_adjusted_sharpe=0.9,
            volatility=0.01,
            stability_score=0.7,
            raw_weight=w,
            constrained_weight=w,
        )
        for sid, w in zip(strategy_ids, weights)
    ]
    return WeightResult(weights=sws)


def _make_allocations(strategy_ids, weights):
    return [
        CapitalAllocation(
            strategy_id=sid,
            weight=w,
            capital=w * 1_000_000,
            risk_budget=0.0,
        )
        for sid, w in zip(strategy_ids, weights)
    ]


class TestRebalancer:

    def test_no_drift_no_rebalance(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        allocations = _make_allocations(["s1", "s2"], [0.5, 0.5])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert not result.triggered
        assert result.turnover_ratio == 0.0

    def test_drift_triggers_rebalance(self):
        wr = _make_weight_result(["s1", "s2"], [0.6, 0.4])
        allocations = _make_allocations(["s1", "s2"], [0.4, 0.6])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert result.triggered
        assert "drift" in result.trigger_reason
        assert result.turnover_ratio > 0

    def test_drift_below_threshold_no_rebalance(self):
        wr = _make_weight_result(["s1", "s2"], [0.51, 0.49])
        allocations = _make_allocations(["s1", "s2"], [0.50, 0.50])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert not result.triggered

    def test_calendar_trigger(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        allocations = _make_allocations(["s1", "s2"], [0.5, 0.5])

        rb = Rebalancer(drift_threshold=0.05, calendar_frequency_days=20)
        last_date = datetime.now(timezone.utc) - timedelta(days=25)
        current_date = datetime.now(timezone.utc)

        result = rb.check(allocations, wr, last_date, current_date)

        assert result.triggered
        assert "calendar" in result.trigger_reason

    def test_calendar_not_triggered_before_frequency(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        allocations = _make_allocations(["s1", "s2"], [0.5, 0.5])

        rb = Rebalancer(calendar_frequency_days=20)
        last_date = datetime.now(timezone.utc) - timedelta(days=10)
        current_date = datetime.now(timezone.utc)

        result = rb.check(allocations, wr, last_date, current_date)

        assert not result.triggered

    def test_rebalance_actions_buy_sell_hold(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.5, 0.3, 0.2])
        allocations = _make_allocations(["s1", "s2", "s3"], [0.5, 0.5, 0.0])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert result.triggered
        actions = {a.strategy_id: a.action for a in result.actions}

        assert actions["s1"] == "hold"
        assert actions["s2"] == "sell"
        assert actions["s3"] == "buy"

    def test_volatility_scales_drift_threshold(self):
        wr = _make_weight_result(["s1", "s2"], [0.555, 0.445])
        allocations = _make_allocations(["s1", "s2"], [0.50, 0.50])

        rb_low_vol = Rebalancer(drift_threshold=0.05, volatility_scale_factor=3.0)
        rb_high_vol = Rebalancer(drift_threshold=0.05, volatility_scale_factor=3.0)

        result_low = rb_low_vol.check(allocations, wr, recent_volatility=0.01)
        result_high = rb_high_vol.check(allocations, wr, recent_volatility=0.05)

        assert result_low.triggered
        assert not result_high.triggered

    def test_empty_inputs(self):
        rb = Rebalancer()
        result = rb.check([], WeightResult())
        assert not result.triggered
        assert result.action_count == 0

    def test_turnover_ratio_property(self):
        wr = _make_weight_result(["s1", "s2"], [0.6, 0.4])
        allocations = _make_allocations(["s1", "s2"], [0.4, 0.6])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert result.total_turnover > 0
        assert 0 <= result.turnover_ratio <= 1.0

    def test_max_single_trade(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.6, 0.3, 0.1])
        allocations = _make_allocations(["s1", "s2", "s3"], [0.2, 0.4, 0.4])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert result.max_single_trade > 0

    def test_previous_and_target_weights_populated(self):
        wr = _make_weight_result(["s1", "s2"], [0.6, 0.4])
        allocations = _make_allocations(["s1", "s2"], [0.5, 0.5])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert len(result.previous_weights) == 2
        assert len(result.target_weights) == 2
        assert sum(result.previous_weights) == pytest.approx(1.0, rel=1e-4)
        assert sum(result.target_weights) == pytest.approx(1.0, rel=1e-4)

    def test_single_strategy_zero_drift(self):
        wr = _make_weight_result(["s1"], [1.0])
        allocations = _make_allocations(["s1"], [1.0])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert not result.triggered

    def test_new_strategy_introduced(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.5, 0.3, 0.2])
        allocations = _make_allocations(["s1", "s2"], [0.6, 0.4])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert result.triggered
        s3_action = next(a for a in result.actions if a.strategy_id == "s3")
        assert s3_action.action == "buy"
        assert s3_action.delta > 0

    def test_strategy_removed(self):
        wr = _make_weight_result(["s1"], [1.0])
        allocations = _make_allocations(["s1", "s2"], [0.5, 0.5])

        rb = Rebalancer(drift_threshold=0.05)
        result = rb.check(allocations, wr)

        assert result.triggered
        s2_action = next(a for a in result.actions if a.strategy_id == "s2")
        assert s2_action.action == "sell"
        assert s2_action.delta < 0
