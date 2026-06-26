import pytest

from app.execution.liquidity_model import (
    LiquidityConfig,
    LiquidityModel,
    LiquidityProfile,
)


class TestLiquidityModel:

    def test_default_config_creates_valid_profile(self):
        model = LiquidityModel()
        profile = model.profile("s1", trade_size=1_000_000, volatility=0.01)

        assert isinstance(profile, LiquidityProfile)
        assert profile.strategy_id == "s1"
        assert profile.daily_volume > 0
        assert profile.available_liquidity > 0
        assert profile.bid_ask_spread_bps > 0

    def test_zero_trade_size(self):
        model = LiquidityModel()
        profile = model.profile("s1", trade_size=0.0, volatility=0.01)

        assert profile.depth_ratio == 1.0
        assert profile.is_liquid
        assert profile.max_fill_ratio == pytest.approx(1.0, rel=1e-4)

    def test_large_trade_reduces_liquidity(self):
        model = LiquidityModel()
        small = model.profile("s1", trade_size=1_000_000, volatility=0.01)
        large = model.profile("s1", trade_size=50_000_000, volatility=0.01)

        assert large.depth_ratio < small.depth_ratio
        assert large.available_liquidity < small.available_liquidity

    def test_high_volatility_increases_spread(self):
        model = LiquidityModel()
        low_vol = model.profile("s1", trade_size=1_000_000, volatility=0.005)
        high_vol = model.profile("s1", trade_size=1_000_000, volatility=0.05)

        assert high_vol.bid_ask_spread_bps > low_vol.bid_ask_spread_bps

    def test_very_large_trade_makes_illiquid(self):
        config = LiquidityConfig(daily_volume=1e6, min_liquidity_ratio=0.5)
        model = LiquidityModel(config=config)
        profile = model.profile("s1", trade_size=10_000_000, volatility=0.01)

        assert not profile.is_liquid
        assert profile.depth_ratio < 0.5

    def test_fill_ratio_no_liquidity(self):
        model = LiquidityModel()
        profile = LiquidityProfile(
            strategy_id="s1",
            daily_volume=0.0,
            available_liquidity=0.0,
            bid_ask_spread_bps=2.0,
            depth_ratio=0.0,
            is_liquid=False,
        )
        ratio = model.compute_fill_ratio(profile, intended_size=1_000_000)
        assert ratio == 0.0

    def test_fill_ratio_fully_available(self):
        model = LiquidityModel()
        profile = LiquidityProfile(
            strategy_id="s1",
            daily_volume=1e8,
            available_liquidity=5_000_000,
            bid_ask_spread_bps=2.0,
            depth_ratio=1.0,
            is_liquid=True,
        )
        ratio = model.compute_fill_ratio(profile, intended_size=1_000_000)
        assert ratio == 1.0

    def test_fill_ratio_partial(self):
        model = LiquidityModel()
        profile = LiquidityProfile(
            strategy_id="s1",
            daily_volume=1e8,
            available_liquidity=500_000,
            bid_ask_spread_bps=2.0,
            depth_ratio=0.5,
            is_liquid=True,
        )
        ratio = model.compute_fill_ratio(profile, intended_size=1_000_000)
        assert 0.0 < ratio < 1.0

    def test_effective_spread_with_participation(self):
        model = LiquidityModel()
        profile = LiquidityProfile(
            strategy_id="s1",
            daily_volume=1e8,
            available_liquidity=1e7,
            bid_ask_spread_bps=5.0,
            depth_ratio=0.9,
            is_liquid=True,
        )
        spread = model.effective_spread(profile, participation_rate=0.05)
        assert spread > profile.bid_ask_spread_bps

    def test_max_fill_ratio_property(self):
        profile = LiquidityProfile(
            strategy_id="s1",
            daily_volume=1e8,
            available_liquidity=5e7,
            bid_ask_spread_bps=2.0,
            depth_ratio=0.9,
            is_liquid=True,
        )
        assert profile.max_fill_ratio == 0.5

    def test_spread_capped_at_maximum(self):
        config = LiquidityConfig(bid_ask_spread_bps=2.0, spread_vol_scaling=10.0)
        model = LiquidityModel(config=config)
        profile = model.profile("s1", trade_size=50_000_000, volatility=0.10)

        assert profile.bid_ask_spread_bps <= 100.0

    def test_custom_config(self):
        config = LiquidityConfig(
            daily_volume=5e7,
            bid_ask_spread_bps=5.0,
            min_liquidity_ratio=0.05,
            volume_decay_factor=0.3,
            spread_vol_scaling=1.0,
        )
        model = LiquidityModel(config=config)
        profile = model.profile("s1", trade_size=1_000_000, volatility=0.01)

        assert profile.daily_volume == pytest.approx(5e7 * 0.9, rel=1e-2)
        assert profile.bid_ask_spread_bps > 0
