import logging
from datetime import datetime, timezone

from app.feature_store.repository import FeatureItem

logger = logging.getLogger(__name__)

FEATURE_DEFINITIONS: list[dict] = [
    {"name": "market_turnover", "category": "liquidity"},
    {"name": "northbound_flow", "category": "sentiment"},
    {"name": "advancers_ratio", "category": "breadth"},
    {"name": "volatility_index", "category": "volatility"},
    {"name": "trend_strength", "category": "trend"},
]

FEATURE_VERSION = "1.0.0"
FEATURE_SOURCE = "akshare_v1"
FEATURE_CONFIDENCE = 0.95


class DataTransformer:
    def __init__(
        self,
        version: str = FEATURE_VERSION,
        source: str = FEATURE_SOURCE,
        confidence: float = FEATURE_CONFIDENCE,
    ):
        self._version = version
        self._source = source
        self._confidence = confidence

    def transform(self, raw_data: dict[str, float]) -> list[FeatureItem]:
        now = datetime.now(timezone.utc)
        items = []

        missing: list[str] = []

        for defn in FEATURE_DEFINITIONS:
            name = defn["name"]
            raw_value = raw_data.get(name)
            if raw_value is None:
                missing.append(name)
                value = 0.0
            else:
                value = self._normalize(raw_value)

            items.append(
                FeatureItem(
                    name=name,
                    value=value,
                    category=defn["category"],
                    timestamp=now,
                    version=self._version,
                    source=self._source,
                    confidence=self._confidence,
                )
            )

        if missing:
            logger.warning("Features missing raw data, defaulting to 0: %s", missing)

        logger.info(
            "Transformed %d FeatureItems: %s",
            len(items),
            {item.name: round(item.value, 2) for item in items},
        )
        return items

    @staticmethod
    def _normalize(value: float) -> float:
        return round(max(0.0, min(100.0, value)), 2)
