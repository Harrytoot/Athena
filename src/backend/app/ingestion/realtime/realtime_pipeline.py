import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ingestion.feature_writer import FeatureWriter
from app.ingestion.realtime.event_bus import IngestionEventBus
from app.ingestion.realtime.realtime_tick_provider import RealtimeTickProvider
from app.ingestion.realtime.runtime_bridge import RuntimeBridge
from app.ingestion.realtime.tick_normalizer import TickNormalizer

logger = logging.getLogger(__name__)


class RealtimePipeline:

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        provider: RealtimeTickProvider,
        symbols: list[str],
        normalizer: TickNormalizer | None = None,
        writer: FeatureWriter | None = None,
        runtime_bridge: RuntimeBridge | None = None,
        event_bus: IngestionEventBus | None = None,
    ):
        self._session_factory = session_factory
        self._provider = provider
        self._symbols = symbols
        self._normalizer = normalizer or TickNormalizer()
        self._writer = writer or FeatureWriter()
        self._runtime_bridge = runtime_bridge or RuntimeBridge()
        self._event_bus = event_bus or IngestionEventBus()
        self._running = False
        self._cycle_count = 0

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def event_bus(self) -> IngestionEventBus:
        return self._event_bus

    @property
    def runtime_bridge(self) -> RuntimeBridge:
        return self._runtime_bridge

    async def run_cycle(self) -> dict:
        start = datetime.now(timezone.utc)
        features_written = 0
        symbols_triggered = 0
        error = None

        try:
            ticks = await self._provider.get_realtime_ticks(self._symbols)
            if not ticks:
                logger.debug("No ticks returned for symbols %s", self._symbols)
                return {"status": "no_data", "elapsed_seconds": 0}

            all_features = self._normalizer.normalize_batch(ticks)

            async with self._session_factory() as session:
                await self._writer.write_features(all_features, session)

            features_written = len(all_features)

            triggered_symbols: set[str] = set()
            for tick in ticks:
                await self._runtime_bridge.map_and_trigger(all_features, tick.symbol)
                triggered_symbols.add(tick.symbol)

            symbols_triggered = len(triggered_symbols)

            for tick in ticks:
                self._event_bus.publish(
                    event_type="market_tick",
                    symbol=tick.symbol,
                    payload={
                        "price": tick.price,
                        "change_pct": tick.change_pct,
                        "volume": tick.volume,
                    },
                )

            self._cycle_count += 1

        except Exception as e:
            logger.exception("Realtime pipeline cycle failed")
            error = str(e)

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        result = {
            "status": "error" if error else "ok",
            "cycle": self._cycle_count,
            "ticks_received": len(ticks) if "ticks" in dir() else 0,
            "features_written": features_written,
            "symbols_triggered": symbols_triggered,
            "elapsed_seconds": round(elapsed, 3),
            "timestamp": start.isoformat(),
        }
        if error:
            result["error"] = error

        logger.info("Realtime cycle %d: %s", self._cycle_count, result)
        return result

    def set_provider(self, provider: RealtimeTickProvider) -> None:
        self._provider = provider

    def get_event_log(self) -> list:
        return self._event_bus.to_replay_events()
