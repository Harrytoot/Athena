import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ingestion.feature_writer import FeatureWriter
from app.ingestion.market_fetcher import MarketDataFetcher
from app.ingestion.transformer import FEATURE_SOURCE, FEATURE_VERSION, DataTransformer
from app.providers.market.base import MarketOverview, MarketProvider

logger = logging.getLogger(__name__)

REDIS_KEY_MARKET_OVERVIEW = "athena:market:overview"
REDIS_KEY_HOT_SECTORS = "athena:market:hot_sectors"


class IngestionService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        fetcher: Optional[MarketDataFetcher] = None,
        transformer: Optional[DataTransformer] = None,
        writer: Optional[FeatureWriter] = None,
    ):
        self._session_factory = session_factory
        self._fetcher = fetcher or MarketDataFetcher()
        self._transformer = transformer or DataTransformer()
        self._writer = writer or FeatureWriter()

    async def run_pipeline(
        self, provider: Optional[MarketProvider] = None
    ) -> dict:
        start = datetime.now(timezone.utc)

        if provider is not None:
            self._fetcher = MarketDataFetcher(provider=provider)

        raw = await self._fetcher.fetch_raw()
        items = self._transformer.transform(raw)

        async with self._session_factory() as session:
            await self._writer.write_features(items, session)

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        result = {
            "status": "ok",
            "features_written": len(items),
            "source": FEATURE_SOURCE,
            "version": FEATURE_VERSION,
            "elapsed_seconds": round(elapsed, 3),
            "timestamp": start.isoformat(),
        }

        logger.info("Ingestion pipeline completed: %s", result)
        return result

    async def run_manual(
        self, provider: Optional[MarketProvider] = None
    ) -> dict:
        logger.info("Manual ingestion triggered")
        result = await self.run_pipeline(provider=provider)
        result["mode"] = "manual"
        logger.info(
            "Manual ingestion result: %d features in %.3fs",
            result["features_written"],
            result["elapsed_seconds"],
        )
        return result

    async def cache_overview_to_redis(self, overview: MarketOverview) -> None:
        try:
            from app.infrastructure.cache.redis import get_redis
            r = await get_redis()

            mapping = {
                "indices": json.dumps({
                    "shanghai": overview.indices.shanghai.model_dump(),
                    "shenzhen": overview.indices.shenzhen.model_dump(),
                    "chi_next": overview.indices.chi_next.model_dump(),
                }),
                "market_regime": overview.market_regime.value,
                "temperature": str(overview.temperature),
                "turnover": str(overview.turnover),
                "up_count": str(overview.up_count),
                "down_count": str(overview.down_count),
                "northbound": str(overview.northbound),
                "summary": overview.summary,
                "updated_at": overview.updated_at.isoformat() if overview.updated_at else "",
                "data_quality": "cached",
            }
            await r.hset(REDIS_KEY_MARKET_OVERVIEW, mapping=mapping)

            if overview.hot_industries:
                await r.delete(REDIS_KEY_HOT_SECTORS)
                items = [json.dumps(i.model_dump()) for i in overview.hot_industries]
                await r.rpush(REDIS_KEY_HOT_SECTORS, *items)

            logger.info("Market overview cached to Redis")
        except Exception as e:
            logger.error("Failed to cache market overview to Redis: %s", e)
