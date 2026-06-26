from app.domain.market.market_score import MarketScore
from app.feature_store.repository import FeatureRepository

FEATURE_NAMES = [
    "trend_strength",
    "market_turnover",
    "advancers_ratio",
    "volatility_index",
    "northbound_flow",
]


class MarketScoreService:

    def __init__(self, feature_repo: FeatureRepository):
        self._feature_repo = feature_repo

    async def get_score(self) -> dict:
        features: dict[str, float] = {}
        for name in FEATURE_NAMES:
            item = await self._feature_repo.get_latest(name)
            features[name] = item.value if item is not None else 50.0

        score = MarketScore(
            trend=features["trend_strength"],
            liquidity=features["market_turnover"],
            breadth=features["advancers_ratio"],
            volatility=features["volatility_index"],
            sentiment=features["northbound_flow"],
        )

        return {
            "score": score.total,
            "state": score.state,
            "trend": features["trend_strength"],
            "liquidity": features["market_turnover"],
            "breadth": features["advancers_ratio"],
            "volatility": features["volatility_index"],
            "sentiment": features["northbound_flow"],
            "source": "feature_store",
        }
