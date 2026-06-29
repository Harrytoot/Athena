import json
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.ingestion.ingestion_service import IngestionService
from app.observation_preanalysis.pre_observation_report import (
    PreObservationReport,
    PreObservationReportGenerator,
)
from app.observation_preanalysis.performance_attribution_engine import (
    PerformanceAttributionEngine,
)
from app.observation_preanalysis.strategy_batch_runner import StrategyBatchRunner
from app.observation_preanalysis.strategy_ranker import StrategyRanker
from app.providers.market.akshare_provider import AkShareMarketProvider
from app.providers.market.base import MarketProvider

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8))

REDIS_KEY_PREANALYSIS_REPORT = "athena:preanalysis:latest"


class ObservationModeScheduler:

    def __init__(
        self,
        service: IngestionService,
        fetch_provider: MarketProvider | None = None,
        batch_runner: StrategyBatchRunner | None = None,
    ):
        self._scheduler = AsyncIOScheduler()
        self._service = service
        self._fetch_provider = fetch_provider or AkShareMarketProvider()
        self._batch_runner = batch_runner
        self._attribution_engine = PerformanceAttributionEngine()
        self._ranker = StrategyRanker()
        self._report_generator = PreObservationReportGenerator()

    def start(self) -> None:
        self._scheduler.add_job(
            self._morning_burst,
            CronTrigger(hour=8, minute=50, day_of_week="mon-fri", timezone=BEIJING_TZ),
            id="obs_morning",
            name="Morning pre-analysis (08:50)",
            misfire_grace_time=600,
        )
        self._scheduler.add_job(
            self._midday_burst,
            CronTrigger(hour=10, minute=50, day_of_week="mon-fri", timezone=BEIJING_TZ),
            id="obs_midday",
            name="Midday pre-analysis (10:50)",
            misfire_grace_time=600,
        )
        self._scheduler.add_job(
            self._close_burst,
            CronTrigger(hour=14, minute=45, day_of_week="mon-fri", timezone=BEIJING_TZ),
            id="obs_close",
            name="Close pre-analysis (14:45)",
            misfire_grace_time=600,
        )
        self._scheduler.add_job(
            self._evening_burst,
            CronTrigger(hour=20, minute=30, day_of_week="mon-fri", timezone=BEIJING_TZ),
            id="obs_evening",
            name="Evening report (20:30)",
            misfire_grace_time=600,
        )
        self._scheduler.start()
        logger.info(
            "ObservationModeScheduler started: 08:50 | 10:50 | 14:45 | 20:30 Mon-Fri"
        )

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("ObservationModeScheduler stopped")

    async def trigger_now(self) -> dict:
        logger.info("Manual observation burst triggered")
        return await self._burst("manual")

    async def _morning_burst(self) -> None:
        await self._burst("morning")

    async def _midday_burst(self) -> None:
        await self._burst("midday")

    async def _close_burst(self) -> None:
        await self._burst("close")

    async def _evening_burst(self) -> None:
        await self._burst("evening")

    async def _burst(self, label: str) -> dict:
        start = datetime.now(timezone.utc)
        result = {
            "label": label,
            "status": "ok",
            "ingestion": {},
            "preanalysis": {},
            "report_cached": False,
        }
        try:
            logger.info("Observation burst [%s] — Phase 1: Ingestion", label)
            ingestion_result = await self._service.run_pipeline(
                provider=self._fetch_provider
            )
            result["ingestion"] = {
                "features_written": ingestion_result["features_written"],
                "elapsed_seconds": ingestion_result["elapsed_seconds"],
            }

            overview = await self._fetch_provider.get_overview()
            await self._service.cache_overview_to_redis(overview)

            logger.info("Observation burst [%s] — Phase 2: Pre-Analysis", label)
            preanalysis = await self._run_preanalysis(label)
            result["preanalysis"] = {
                "confidence_score": preanalysis.confidence_score,
                "market_regime": preanalysis.market_regime_summary.regime,
                "risk_level": preanalysis.risk_state.overall_level,
                "actions_count": len(preanalysis.action_recommendations),
            }

            await self._cache_report(preanalysis)
            result["report_cached"] = True

        except Exception:
            logger.exception("Observation burst [%s] failed", label)
            result["status"] = "error"

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        result["elapsed_seconds"] = round(elapsed, 3)
        result["timestamp"] = start.isoformat()
        logger.info("Observation burst [%s] complete: %s", label, result)
        return result

    async def _run_preanalysis(self, window: str) -> PreObservationReport:
        if not self._batch_runner:
            logger.warning("No batch runner configured, skipping pre-analysis for [%s]", window)
            return await self._report_generator.generate(
                window=window,
                batch_result=None,
                ranked_list=None,
                attribution=None,
            )

        batch_result = await self._batch_runner.run_batch(window)

        from app.infrastructure.persistence.session import async_session_factory
        from app.feature_store.repository import SQLAlchemyFeatureRepository
        async with async_session_factory() as session:
            feature_repo = SQLAlchemyFeatureRepository(session)
            attribution = await self._attribution_engine.attribute(feature_repo)

        ranked = self._ranker.rank(batch_result)

        return await self._report_generator.generate(
            window=window,
            batch_result=batch_result,
            ranked_list=ranked,
            attribution=attribution,
        )

    async def _cache_report(self, report: PreObservationReport) -> None:
        try:
            from app.infrastructure.cache.redis import get_redis
            r = await get_redis()
            payload = json.dumps({
                "window": report.window,
                "timestamp": report.timestamp.isoformat(),
                "market_regime": report.market_regime_summary.regime,
                "temperature": report.market_regime_summary.temperature,
                "risk_level": report.risk_state.overall_level,
                "confidence_score": report.confidence_score,
                "top_pick": report.strategy_ranking.top_pick,
                "top_actions": [
                    {"symbol": a.symbol, "name": a.name, "action": a.action}
                    for a in report.action_recommendations[:3]
                ],
                "warnings": report.risk_state.warnings,
                "summary": report.summary,
            }, ensure_ascii=False)
            await r.set(REDIS_KEY_PREANALYSIS_REPORT, payload, ex=86400)
            logger.info("Pre-analysis report cached to Redis")
        except Exception as e:
            logger.error("Failed to cache pre-analysis report: %s", e)
