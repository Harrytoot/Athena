from datetime import datetime, timezone

import pytest

from app.strategy_robustness.market_impact import (
    ImpactConfig,
    ImpactEstimate,
    MarketImpactModel,
)
from tests.strategy_robustness import _build_history, _risk_result


class TestImpactConfig:

    def test_default_config(self):
        cfg = ImpactConfig()
        assert cfg.impact_coefficient == 0.1
        assert cfg.sqroot_alpha == 0.5
        assert cfg.daily_volume_estimate == 1e8
        assert cfg.max_impact_bps == 100.0


class TestMarketImpactModel:

    def test_empty_history(self):
        model = MarketImpactModel()
        history = _build_history([], [])
        risk = _risk_result([])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 0

    def test_single_snapshot(self):
        model = MarketImpactModel()
        history = _build_history([1.0], [100.0])
        risk = _risk_result([1.0])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 0

    def test_no_trade_no_impact(self):
        model = MarketImpactModel()
        history = _build_history(
            [1.0, 1.0, 1.0],
            [100.0, 101.0, 102.0],
        )
        risk = _risk_result([1.0, 1.0, 1.0])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 2
        assert estimates[0].impact_amount == 0.0
        assert estimates[1].impact_amount == 0.0

    def test_trade_generates_impact(self):
        model = MarketImpactModel()
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 1
        assert estimates[0].impact_amount > 0
        assert estimates[0].impact_bps > 0

    def test_larger_trade_larger_impact(self):
        model = MarketImpactModel()
        history_small = _build_history(
            [0.0, 0.25],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        history_large = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk_small = _risk_result([0.0, 0.25])
        risk_large = _risk_result([0.0, 1.0])

        est_small = model.estimate(history_small, risk_small)
        est_large = model.estimate(history_large, risk_large)

        assert est_large[0].impact_bps > est_small[0].impact_bps

    def test_impact_capped(self):
        cfg = ImpactConfig(max_impact_bps=5.0, impact_coefficient=100.0)
        model = MarketImpactModel(config=cfg)
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=1e9,
        )
        risk = _risk_result([0.0, 1.0])
        estimates = model.estimate(history, risk)
        assert estimates[0].impact_bps <= 5.0

    def test_total_impact(self):
        model = MarketImpactModel()
        history = _build_history(
            [0.0, 1.0, 0.5],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5])
        estimates = model.estimate(history, risk)
        total = model.total_impact(estimates)
        assert total > 0

    def test_impact_ratio(self):
        model = MarketImpactModel()
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0])
        estimates = model.estimate(history, risk)
        ratio = model.impact_ratio(history, estimates)
        assert ratio > 0
        assert ratio < 1.0

    def test_sensitivity_analysis(self):
        model = MarketImpactModel()
        history = _build_history(
            [0.0, 1.0, 0.5, 0.0] * 3,
            [100.0 + i for i in range(12)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5, 0.0] * 3)
        sens = model.sensitivity_analysis(history, risk)
        assert "0.1x_volume" in sens
        assert "1.0x_volume" in sens
        assert "5.0x_volume" in sens
        assert sens["0.1x_volume"] > sens["1.0x_volume"]

    def test_short_trade_impact(self):
        model = MarketImpactModel()
        history = _build_history(
            [1.0, -0.5],
            [100.0, 99.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0, -0.5])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 1
        assert estimates[0].impact_amount > 0

    def test_estimate_fields_populated(self):
        model = MarketImpactModel()
        history = _build_history(
            [0.0, 0.5],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 0.5])
        estimates = model.estimate(history, risk)
        est = estimates[0]
        assert isinstance(est.participation_rate, float)
        assert isinstance(est.impact_bps, float)
        assert isinstance(est.impact_amount, float)
        assert isinstance(est.trade_notional, float)

    def test_impact_ratio_zero_nav(self):
        model = MarketImpactModel()
        history = _build_history([], [], initial_nav=0.0)
        risk = _risk_result([])
        ratio = model.impact_ratio(history, [])
        assert ratio == 0.0
