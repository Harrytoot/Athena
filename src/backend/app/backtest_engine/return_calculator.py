from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ReturnSeries:
    timestamps: list[datetime]
    prices: list[float]
    forward_returns: dict[int, list[float]] = field(default_factory=dict)


class ReturnCalculator:

    @staticmethod
    def compute(
        prices: list[float],
        horizons: list[int],
    ) -> dict[int, list[float]]:
        n = len(prices)
        result: dict[int, list[float]] = {}
        for h in horizons:
            fwd = [0.0] * n
            for i in range(n - h):
                p0 = prices[i]
                p1 = prices[i + h]
                if p0 != 0:
                    fwd[i] = round((p1 - p0) / p0, 6)
            result[h] = fwd
        return result

    @staticmethod
    def compute_from_prices(
        price_series: list[float],
        score_timestamps: list[datetime],
        score_prices: Optional[list[float]] = None,
        horizons: Optional[list[int]] = None,
    ) -> dict[int, list[float]]:
        if horizons is None:
            horizons = [5, 10, 20]
        prices = score_prices if score_prices is not None else price_series
        return ReturnCalculator.compute(prices, horizons)
