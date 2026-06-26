import math
from dataclasses import dataclass, field


@dataclass
class LiquidityConfig:
    daily_volume: float = 1e8
    bid_ask_spread_bps: float = 2.0
    min_liquidity_ratio: float = 0.01
    volume_decay_factor: float = 0.5
    spread_vol_scaling: float = 0.5


@dataclass
class LiquidityProfile:
    strategy_id: str
    daily_volume: float
    available_liquidity: float
    bid_ask_spread_bps: float
    depth_ratio: float
    is_liquid: bool

    @property
    def max_fill_ratio(self) -> float:
        if self.daily_volume <= 0:
            return 0.0
        return min(1.0, self.available_liquidity / self.daily_volume)


class LiquidityModel:

    def __init__(self, config: LiquidityConfig | None = None):
        self.config = config or LiquidityConfig()

    def profile(
        self,
        strategy_id: str,
        trade_size: float,
        volatility: float = 0.01,
    ) -> LiquidityProfile:
        base_volume = self.config.daily_volume

        vol_factor = max(0.1, 1.0 - volatility * 10.0)
        effective_volume = base_volume * vol_factor

        participation_rate = 0.0
        if effective_volume > 0:
            participation_rate = trade_size / effective_volume

        depth_ratio = max(0.0, 1.0 - participation_rate * self.config.volume_decay_factor)

        available_liquidity = effective_volume * depth_ratio

        spread_bps = self.config.bid_ask_spread_bps
        if volatility > 0 and trade_size > 0:
            spread_bps += volatility * self.config.spread_vol_scaling * 10000
            spread_bps += trade_size / effective_volume * 10.0 if effective_volume > 0 else 0.0

        spread_bps = min(spread_bps, 100.0)

        is_liquid = depth_ratio >= self.config.min_liquidity_ratio

        return LiquidityProfile(
            strategy_id=strategy_id,
            daily_volume=round(effective_volume, 2),
            available_liquidity=round(available_liquidity, 2),
            bid_ask_spread_bps=round(spread_bps, 4),
            depth_ratio=round(depth_ratio, 6),
            is_liquid=is_liquid,
        )

    def compute_fill_ratio(
        self,
        profile: LiquidityProfile,
        intended_size: float,
    ) -> float:
        if intended_size <= 0 or profile.available_liquidity <= 0:
            return 0.0
        max_fill = profile.available_liquidity
        return round(min(1.0, max_fill / intended_size), 6)

    def effective_spread(
        self,
        profile: LiquidityProfile,
        participation_rate: float,
    ) -> float:
        spread = profile.bid_ask_spread_bps
        if participation_rate > 0:
            spread += participation_rate * 10000 * 0.05
        return round(spread, 4)
