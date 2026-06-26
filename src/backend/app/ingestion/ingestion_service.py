import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ingestion.feature_writer import FeatureWriter
from app.ingestion.market_fetcher import MarketDataFetcher
from app.ingestion.transformer import FEATURE_SOURCE, FEATURE_VERSION, DataTransformer
from app.providers.market.base import MarketProvider

logger = logging.getLogger(__name__)


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
