import pytest

from app.execution.slippage_engine import (
    SlippageConfig,
    SlippageEngine,
    SlippageEstimate,
)


class TestSlippageEngine:

    def test_default_estimate(self):
        engine = SlippageEngine()
        estimate = engine.estimate(
            strategy_id="s1",
            trade_notional=100_000,
            daily_volatility=0.01,
            daily_volume=1e8,
        )

        assert isinstance(estimate, SlippageEstimate)
        assert estimate.strategy_id == "s1"
        assert estimate.trade_notional > 0
        assert estimate.slippage_bps >= 0
        assert estimate.slippage_amount >= 0

    def test_zero_notional(self):
        engine = SlippageEngine()
        estimate = engine.estimate(
            strategy_id="s1",
            trade_notional=0.0,
            daily_volatility=0.01,
            daily_volume=1e8,
        )

        assert estimate.slippage_bps == 0.0
        assert estimate.slippage_amount == 0.0

    def test_zero_volume(self):
        engine = SlippageEngine()
        estimate = engine.estimate(
            strategy_id="s1",
            trade_notional=100_000,
            daily_volatility=0.01,
            daily_volume=0.0,
        )

        assert estimate.slippage_bps == 0.0
        assert estimate.slippage_amount == 0.0

    def test_higher_volatility_increases_slippage(self):
        engine = SlippageEngine(config=SlippageConfig(seed=42))
        low_vol = engine.estimate(
            strategy_id="s1",
            trade_notional=100_000,
            daily_volatility=0.005,
            daily_volume=1e8,
        )
        engine.reset_seed(42)
        high_vol = engine.estimate(
            strategy_id="s1",
            trade_notional=100_000,
            daily_volatility=0.05,
            daily_volume=1e8,
        )

        assert high_vol.slippage_bps > low_vol.slippage_bps

    def test_larger_trade_increases_slippage(self):
        engine = SlippageEngine(config=SlippageConfig(seed=42))
        small = engine.estimate(
            strategy_id="s1",
            trade_notional=10_000,
            daily_volatility=0.01,
            daily_volume=1e8,
        )
        engine.reset_seed(42)
        large = engine.estimate(
            strategy_id="s1",
            trade_notional=10_000_000,
            daily_volatility=0.01,
            daily_volume=1e8,
        )

        assert large.participation_rate > small.participation_rate
        assert large.slippage_bps > small.slippage_bps

    def test_deterministic_with_seed(self):
        config = SlippageConfig(seed=123)
        engine1 = SlippageEngine(config=config)
        engine2 = SlippageEngine(config=config)

        e1 = engine1.estimate("s1", 100_000, 0.01, 1e8)
        e2 = engine2.estimate("s1", 100_000, 0.01, 1e8)

        assert e1.slippage_bps == e2.slippage_bps
        assert e1.slippage_amount == e2.slippage_amount

    def test_slippage_not_exceed_max(self):
        config = SlippageConfig(max_slippage_bps=50.0, seed=42)
        engine = SlippageEngine(config=config)
        estimate = engine.estimate("s1", 50_000_000, 0.10, 1e7)

        assert estimate.slippage_bps <= 50.0

    def test_price_slippage_buy(self):
        engine = SlippageEngine()
        estimate = SlippageEstimate(
            strategy_id="s1",
            trade_notional=100_000,
            daily_volatility=0.01,
            participation_rate=0.001,
            slippage_bps=10.0,
            slippage_amount=10.0,
            direction="buy",
        )
        executed_price = engine.compute_price_slippage(100.0, estimate)
        assert executed_price > 100.0

    def test_price_slippage_sell(self):
        engine = SlippageEngine()
        estimate = SlippageEstimate(
            strategy_id="s1",
            trade_notional=100_000,
            daily_volatility=0.01,
            participation_rate=0.001,
            slippage_bps=10.0,
            slippage_amount=10.0,
            direction="sell",
        )
        executed_price = engine.compute_price_slippage(100.0, estimate)
        assert executed_price < 100.0

    def test_aggregate_slippage(self):
        engine = SlippageEngine()
        estimates = [
            SlippageEstimate("s1", 100_000, 0.01, 0.001, 5.0, 5.0, "buy"),
            SlippageEstimate("s2", 200_000, 0.02, 0.002, 8.0, 16.0, "sell"),
        ]
        total = engine.aggregate_slippage(estimates)
        assert total == pytest.approx(21.0, rel=1e-4)

    def test_direction_preserved(self):
        engine = SlippageEngine()
        buy = engine.estimate("s1", 100_000, 0.01, 1e8, direction="buy")
        sell = engine.estimate("s1", 100_000, 0.01, 1e8, direction="sell")

        assert buy.direction == "buy"
        assert sell.direction == "sell"
