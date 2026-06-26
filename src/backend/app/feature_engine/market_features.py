from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.feature_store.repository import FeatureItem
from app.providers.market.base import MarketProvider

FEATURE_VERSION = "1.0.0"
FEATURE_SOURCE = "mock_v1"
FEATURE_CONFIDENCE = 1.0

FEATURE_DEFINITIONS: list[dict] = [
    {"name": "market_turnover", "category": "liquidity"},
    {"name": "northbound_flow", "category": "sentiment"},
    {"name": "advancers_ratio", "category": "breadth"},
    {"name": "volatility_index", "category": "volatility"},
    {"name": "trend_strength", "category": "trend"},
]


@dataclass
class MarketFeatures:
    items: list[FeatureItem] = field(default_factory=list)

    @property
    def trend_strength(self) -> float:
        return self._get("trend_strength")

    @property
    def market_turnover(self) -> float:
        return self._get("market_turnover")

    @property
    def advancers_ratio(self) -> float:
        return self._get("advancers_ratio")

    @property
    def volatility_index(self) -> float:
        return self._get("volatility_index")

    @property
    def northbound_flow(self) -> float:
        return self._get("northbound_flow")

    def _get(self, name: str) -> float:
        for item in self.items:
            if item.name == name:
                return item.value
        raise KeyError(name)

    def get(self, name: str) -> Optional[FeatureItem]:
        for item in self.items:
            if item.name == name:
                return item
        return None


class MarketFeatureEngine:

    def __init__(self, provider: MarketProvider):
        self._provider = provider

    async def collect_features(self) -> MarketFeatures:
        import asyncio

        trend, liquidity, breadth, volatility, sentiment = await asyncio.gather(
            self._provider.get_trend(),
            self._provider.get_liquidity(),
            self._provider.get_breadth(),
            self._provider.get_volatility(),
            self._provider.get_sentiment(),
        )

        raw_values = {
            "trend_strength": trend,
            "market_turnover": liquidity,
            "advancers_ratio": breadth,
            "volatility_index": volatility,
            "northbound_flow": sentiment,
        }

        now = datetime.now(timezone.utc)
        items = []
        for feature_def in FEATURE_DEFINITIONS:
            name = feature_def["name"]
            items.append(FeatureItem(
                name=name,
                value=raw_values[name],
                category=feature_def["category"],
                timestamp=now,
                version=FEATURE_VERSION,
                source=FEATURE_SOURCE,
                confidence=FEATURE_CONFIDENCE,
            ))

        return MarketFeatures(items=items)
