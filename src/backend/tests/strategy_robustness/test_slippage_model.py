from datetime import datetime, timezone

import pytest

from app.strategy_robustness.slippage_model import (
    SlippageConfig,
    SlippageEstimate,
    SlippageModel,
)
from tests.strategy_robustness import _build_history, _risk_result


class TestSlippageConfig:

    def test_default_config(self):
        cfg = SlippageConfig()
        assert cfg.base_spread_bps == 1.0
        assert cfg.vol_sensitivity == 0.1
        assert cfg.max_slippage_bps == 50.0


class TestSlippageModel:

    def test_empty_history(self):
        model = SlippageModel()
        history = _build_history([], [])
        risk = _risk_result([])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 0

    def test_single_snapshot(self):
        model = SlippageModel()
        history = _build_history([1.0], [100.0])
        risk = _risk_result([1.0])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 0

    def test_no_trade_no_slippage(self):
        model = SlippageModel()
        history = _build_history(
            [1.0, 1.0, 1.0],
            [100.0, 101.0, 102.0],
        )
        risk = _risk_result([1.0, 1.0, 1.0])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 2
        assert estimates[0].effective_slippage == 0.0
        assert estimates[1].effective_slippage == 0.0

    def test_trade_generates_slippage(self):
        model = SlippageModel()
        history = _build_history(
            [0.0, 1.0, 0.5],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 2
        assert estimates[0].effective_slippage > 0

    def test_slippage_increases_with_volatility(self):
        config = SlippageConfig(vol_sensitivity=1.0)
        model = SlippageModel(config=config)
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0])
        estimates = model.estimate(history, risk)
        assert estimates[0].slippage_bps >= config.base_spread_bps

    def test_slippage_capped(self):
        config = SlippageConfig(max_slippage_bps=2.0, vol_sensitivity=100.0)
        model = SlippageModel(config=config)
        history = _build_history(
            [0.0, 1.0],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0])
        estimates = model.estimate(history, risk)
        assert estimates[0].slippage_bps <= 2.0

    def test_total_slippage_impact(self):
        model = SlippageModel()
        history = _build_history(
            [0.0, 1.0, 0.0],
            [100.0, 101.0, 102.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.0])
        estimates = model.estimate(history, risk)
        total = model.total_slippage_impact(estimates)
        assert total > 0

    def test_sensitivity_analysis(self):
        model = SlippageModel()
        history = _build_history(
            [0.0, 1.0, 0.5, 0.0] * 3,
            [100.0 + i for i in range(12)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 1.0, 0.5, 0.0] * 3)
        sens = model.sensitivity_analysis(history, risk)
        assert "0.5x_spread" in sens
        assert "1.0x_spread" in sens
        assert "2.0x_spread" in sens
        assert sens["2.0x_spread"] >= sens["1.0x_spread"]

    def test_slippage_estimate_fields_populated(self):
        model = SlippageModel()
        history = _build_history(
            [0.0, 0.5],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 0.5])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 1
        est = estimates[0]
        assert isinstance(est.slippage_bps, float)
        assert isinstance(est.slippage_pct, float)
        assert isinstance(est.effective_slippage, float)
        assert isinstance(est.trade_size_pct, float)

    def test_short_position_slippage(self):
        model = SlippageModel()
        history = _build_history(
            [0.0, -0.5],
            [100.0, 99.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, -0.5])
        estimates = model.estimate(history, risk)
        assert len(estimates) == 1
        assert estimates[0].effective_slippage > 0

    def test_sensitivity_default_multipliers(self):
        model = SlippageModel()
        history = _build_history(
            [0.0, 0.5],
            [100.0, 101.0],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0, 0.5])
        sens = model.sensitivity_analysis(history, risk)
        assert len(sens) == 5
