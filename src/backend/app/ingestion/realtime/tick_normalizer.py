import logging
from datetime import datetime, timezone

from app.feature_store.repository import FeatureItem
from app.ingestion.realtime.schemas import MarketTick

logger = logging.getLogger(__name__)

REALTIME_FEATURE_DEFINITIONS: list[dict] = [
    {"name": "price_momentum", "category": "momentum"},
    {"name": "volume_spike", "category": "liquidity"},
    {"name": "bid_ask_spread", "category": "microstructure"},
    {"name": "intraday_volatility", "category": "volatility"},
]

REALTIME_FEATURE_VERSION = "1.0.0"
REALTIME_FEATURE_SOURCE = "realtime_v1"
REALTIME_FEATURE_CONFIDENCE = 0.90


class TickNormalizer:

    def __init__(
        self,
        version: str = REALTIME_FEATURE_VERSION,
        source: str = REALTIME_FEATURE_SOURCE,
        confidence: float = REALTIME_FEATURE_CONFIDENCE,
    ):
        self._version = version
        self._source = source
        self._confidence = confidence

    def normalize(
        self, tick: MarketTick, avg_volume: float | None = None
    ) -> list[FeatureItem]:
        now = datetime.now(timezone.utc)
        items: list[FeatureItem] = []

        momentum = self._compute_momentum(tick)
        volume_spike = self._compute_volume_spike(tick, avg_volume)
        spread = self._compute_spread(tick)
        intraday_vol = self._compute_intraday_volatility(tick)

        raw_values = {
            "price_momentum": momentum,
            "volume_spike": volume_spike,
            "bid_ask_spread": spread,
            "intraday_volatility": intraday_vol,
        }

        for defn in REALTIME_FEATURE_DEFINITIONS:
            name = defn["name"]
            value = self._clamp(raw_values.get(name, 0.0))
            items.append(FeatureItem(
                name=f"{tick.symbol}:{name}",
                value=value,
                category=defn["category"],
                timestamp=now,
                version=self._version,
                source=self._source,
                confidence=self._confidence,
            ))

        logger.debug(
            "Normalized tick %s → %d features: %s",
            tick.symbol,
            len(items),
            {item.name: round(item.value, 2) for item in items},
        )
        return items

    def normalize_batch(
        self, ticks: list[MarketTick], avg_volumes: dict[str, float] | None = None
    ) -> list[FeatureItem]:
        all_items: list[FeatureItem] = []
        avg_volumes = avg_volumes or {}
        for tick in ticks:
            avg_vol = avg_volumes.get(tick.symbol)
            items = self.normalize(tick, avg_vol)
            all_items.extend(items)
        return all_items

    @staticmethod
    def _compute_momentum(tick: MarketTick) -> float:
        if tick.pre_close <= 0:
            return 50.0
        raw = tick.change_pct
        return 50.0 + raw * 5.0

    @staticmethod
    def _compute_volume_spike(tick: MarketTick, avg_volume: float | None) -> float:
        if avg_volume is None or avg_volume <= 0:
            return 50.0
        ratio = tick.volume / avg_volume
        return TickNormalizer._clamp(ratio * 50.0)

    @staticmethod
    def _compute_spread(tick: MarketTick) -> float:
        if tick.price <= 0:
            return 50.0
        spread_pct = (tick.ask_price - tick.bid_price) / tick.price * 100
        return 100.0 - TickNormalizer._clamp(spread_pct * 50.0)

    @staticmethod
    def _compute_intraday_volatility(tick: MarketTick) -> float:
        if tick.pre_close <= 0:
            return 50.0
        range_pct = (tick.high - tick.low) / tick.pre_close * 100
        return TickNormalizer._clamp(range_pct * 20.0)

    @staticmethod
    def _clamp(value: float) -> float:
        return round(max(0.0, min(100.0, value)), 2)
