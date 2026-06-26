import math
import random
from dataclasses import dataclass, field


@dataclass
class SlippageConfig:
    base_slippage_bps: float = 1.0
    vol_sensitivity: float = 0.2
    size_sensitivity: float = 0.05
    max_slippage_bps: float = 100.0
    seed: int | None = None


@dataclass
class SlippageEstimate:
    strategy_id: str
    trade_notional: float
    daily_volatility: float
    participation_rate: float
    slippage_bps: float
    slippage_amount: float
    direction: str = "buy"


class SlippageEngine:

    def __init__(self, config: SlippageConfig | None = None):
        self.config = config or SlippageConfig()
        self._rng = random.Random(self.config.seed)

    def estimate(
        self,
        strategy_id: str,
        trade_notional: float,
        daily_volatility: float,
        daily_volume: float,
        direction: str = "buy",
    ) -> SlippageEstimate:
        if trade_notional <= 0 or daily_volume <= 0:
            return SlippageEstimate(
                strategy_id=strategy_id,
                trade_notional=trade_notional,
                daily_volatility=daily_volatility,
                participation_rate=0.0,
                slippage_bps=0.0,
                slippage_amount=0.0,
                direction=direction,
            )

        participation_rate = trade_notional / daily_volume

        slippage_bps = self.config.base_slippage_bps

        if daily_volatility > 0:
            slippage_bps += self.config.vol_sensitivity * daily_volatility * 10000

        if participation_rate > 0:
            slippage_bps += self.config.size_sensitivity * participation_rate * 10000

        noise = self._rng.gauss(0, 0.3)
        slippage_bps += noise

        slippage_bps = max(0.0, min(slippage_bps, self.config.max_slippage_bps))

        slippage_amount = trade_notional * (slippage_bps / 10000.0)

        return SlippageEstimate(
            strategy_id=strategy_id,
            trade_notional=round(trade_notional, 2),
            daily_volatility=round(daily_volatility, 6),
            participation_rate=round(participation_rate, 8),
            slippage_bps=round(slippage_bps, 4),
            slippage_amount=round(slippage_amount, 4),
            direction=direction,
        )

    def compute_price_slippage(
        self,
        reference_price: float,
        slippage_estimate: SlippageEstimate,
    ) -> float:
        slippage_pct = slippage_estimate.slippage_bps / 10000.0
        if slippage_estimate.direction == "buy":
            return reference_price * (1.0 + slippage_pct)
        return reference_price * (1.0 - slippage_pct)

    def aggregate_slippage(
        self,
        estimates: list[SlippageEstimate],
    ) -> float:
        return round(sum(e.slippage_amount for e in estimates), 4)

    def reset_seed(self, seed: int):
        self._rng = random.Random(seed)
