import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.backtest_engine.return_calculator import ReturnCalculator
from app.domain.market.market_score import MarketScore
from app.feature_store.repository import FeatureRepository

FEATURE_NAMES = [
    "trend_strength",
    "market_turnover",
    "advancers_ratio",
    "volatility_index",
    "northbound_flow",
]

SYNTHETIC_BASE_PRICE = 3000.0
DAILY_DRIFT = 0.0003

FORWARD_HORIZONS = [5, 10, 20]


@dataclass
class BacktestRow:
    timestamp: datetime
    score: float
    state: str
    trend: float
    liquidity: float
    breadth: float
    volatility: float
    sentiment: float
    price: float
    forward_return_5d: float = 0.0
    forward_return_10d: float = 0.0
    forward_return_20d: float = 0.0


@dataclass
class BacktestDataset:
    rows: list[BacktestRow] = field(default_factory=list)

    @property
    def timestamps(self) -> list:
        return [r.timestamp for r in self.rows]

    @property
    def scores(self) -> list[float]:
        return [r.score for r in self.rows]

    @property
    def signals(self) -> list[int]:
        from app.backtest_engine.signal_generator import generate_signal
        return [generate_signal(r.score) for r in self.rows]

    @property
    def forward_returns_5d(self) -> list[float]:
        return [r.forward_return_5d for r in self.rows]

    @property
    def forward_returns_10d(self) -> list[float]:
        return [r.forward_return_10d for r in self.rows]

    @property
    def forward_returns_20d(self) -> list[float]:
        return [r.forward_return_20d for r in self.rows]


class DatasetBuilder:

    def __init__(self, feature_repo: FeatureRepository):
        self._repo = feature_repo

    async def build(self, since: datetime, until: datetime, prices: Optional[list[float]] = None) -> BacktestDataset:
        features_by_name: dict[str, list] = {}
        for name in FEATURE_NAMES:
            features_by_name[name] = await self._repo.get_history(name, since, until)

        grouped: dict[datetime, dict[str, float]] = {}
        for name, items in features_by_name.items():
            for item in items:
                ts = item.timestamp.replace(second=0, microsecond=0)
                if ts not in grouped:
                    grouped[ts] = {}
                grouped[ts][name] = item.value

        sorted_ts = sorted(grouped.keys())
        if not sorted_ts:
            return BacktestDataset()

        rows = []
        for ts in sorted_ts:
            factors = grouped[ts]
            if len(factors) < 5:
                continue

            ms = MarketScore(
                trend=factors["trend_strength"],
                liquidity=factors["market_turnover"],
                breadth=factors["advancers_ratio"],
                volatility=factors["volatility_index"],
                sentiment=factors["northbound_flow"],
            )
            rows.append(BacktestRow(
                timestamp=ts,
                score=ms.total,
                state=ms.state,
                trend=factors["trend_strength"],
                liquidity=factors["market_turnover"],
                breadth=factors["advancers_ratio"],
                volatility=factors["volatility_index"],
                sentiment=factors["northbound_flow"],
                price=0.0,
            ))

        n = len(rows)
        if prices is not None and len(prices) >= n:
            raw_prices = prices[:n]
        else:
            raw_prices = _generate_prices(n)

        for i, row in enumerate(rows):
            row.price = raw_prices[i]

        fwd = ReturnCalculator.compute(raw_prices, FORWARD_HORIZONS)
        for i, row in enumerate(rows):
            row.forward_return_5d = fwd[5][i]
            row.forward_return_10d = fwd[10][i]
            row.forward_return_20d = fwd[20][i]

        max_h = max(FORWARD_HORIZONS)
        rows = [r for i, r in enumerate(rows) if i + max_h < n and r.forward_return_20d != 0.0]

        return BacktestDataset(rows=rows)


def _generate_prices(n: int) -> list[float]:
    prices = [SYNTHETIC_BASE_PRICE]
    for i in range(n - 1):
        noise = math.sin(i * 0.5) * 0.005
        daily_return = DAILY_DRIFT + noise
        next_price = round(prices[-1] * (1 + daily_return), 2)
        prices.append(next_price)
    return prices
