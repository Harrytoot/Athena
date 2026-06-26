import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.ingestion.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class IngestionScheduler:
    def __init__(self, service: IngestionService):
        self._scheduler = AsyncIOScheduler()
        self._service = service

    def start(self) -> None:
        self._scheduler.add_job(
            self._run,
            CronTrigger(hour=15, minute=30, day_of_week="mon-fri"),
            id="market_ingestion",
            name="Daily market data ingestion",
            misfire_grace_time=3600,
        )
        self._scheduler.start()
        logger.info("Ingestion scheduler started: daily@15:30 Mon-Fri")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Ingestion scheduler stopped")

    async def run_once(self) -> None:
        await self._service.run_manual()

    async def _run(self) -> None:
        try:
            logger.info("Ingestion pipeline triggered")
            await self._service.run_pipeline()
            logger.info("Ingestion pipeline completed successfully")
        except Exception:
            logger.exception("Ingestion pipeline failed")
