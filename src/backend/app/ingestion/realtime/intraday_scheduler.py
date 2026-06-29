import asyncio
import logging
from typing import Optional

from app.ingestion.realtime.realtime_pipeline import RealtimePipeline
from app.ingestion.realtime.trading_calendar import TradingCalendar

logger = logging.getLogger(__name__)

DEFAULT_TICK_INTERVAL = 5
DEFAULT_FEATURE_INTERVAL = 15
DEFAULT_OVERVIEW_INTERVAL = 60


class IntradayScheduler:

    def __init__(
        self,
        pipeline: RealtimePipeline,
        calendar: TradingCalendar | None = None,
        tick_interval: int = DEFAULT_TICK_INTERVAL,
        feature_interval: int = DEFAULT_FEATURE_INTERVAL,
        overview_interval: int = DEFAULT_OVERVIEW_INTERVAL,
    ):
        self._pipeline = pipeline
        self._calendar = calendar or TradingCalendar()
        self._tick_interval = tick_interval
        self._feature_interval = feature_interval
        self._overview_interval = overview_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._feature_count = 0
        self._overview_count = 0

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Intraday scheduler started: tick=%ds feature=%ds overview=%ds",
            self._tick_interval, self._feature_interval, self._overview_interval,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Intraday scheduler stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def feature_count(self) -> int:
        return self._feature_count

    @property
    def overview_count(self) -> int:
        return self._overview_count

    async def _run_loop(self) -> None:
        tick_elapsed = 0
        feature_elapsed = 0
        overview_elapsed = 0

        while self._running:
            phase = self._calendar.session_phase()

            if phase in ("open_morning", "open_afternoon"):
                if tick_elapsed >= self._tick_interval:
                    await self._pipeline.run_cycle()
                    self._tick_count += 1
                    tick_elapsed = 0
                    feature_elapsed += self._tick_interval
                    overview_elapsed += self._tick_interval

            elif phase in ("closed", "pre_market", "lunch_break"):
                tick_elapsed = 0
                feature_elapsed = 0
                overview_elapsed = 0
                sleep_time = 30
                await asyncio.sleep(sleep_time)
                continue

            await asyncio.sleep(1)
            tick_elapsed += 1
