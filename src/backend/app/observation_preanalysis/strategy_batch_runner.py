import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.services.decision_service import DecisionService
from app.application.services.market_score_service import MarketScoreService
from app.application.services.stock_service import StockService
from app.feature_store.repository import SQLAlchemyFeatureRepository

logger = logging.getLogger(__name__)

DEFAULT_TRACKED_SYMBOLS = [
    "000001", "000300", "399001", "399006",
    "600519", "000858", "601318", "600036",
    "000333", "300750", "002594", "601899",
]


@dataclass
class StrategyPerformanceSnapshot:
    symbol: str
    name: str
    signal: str
    signal_label: str
    confidence: float
    action: str
    action_label: str
    trend: float
    liquidity: float
    breadth: float
    volatility: float
    sentiment: float
    timestamp: datetime


@dataclass
class BatchResult:
    window: str
    timestamp: datetime
    snapshots: list[StrategyPerformanceSnapshot] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.snapshots)

    @property
    def bullish_count(self) -> int:
        return sum(1 for s in self.snapshots if s.signal in ("STRONG_BUY", "BUY"))

    @property
    def bearish_count(self) -> int:
        return sum(1 for s in self.snapshots if s.signal in ("STRONG_SELL", "SELL"))

    @property
    def neutral_count(self) -> int:
        return sum(1 for s in self.snapshots if s.signal == "NEUTRAL")

    @property
    def avg_confidence(self) -> float:
        if not self.snapshots:
            return 0.0
        return round(sum(s.confidence for s in self.snapshots) / len(self.snapshots), 2)


class StrategyBatchRunner:

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        stock_service: StockService,
        symbols: list[str] | None = None,
    ):
        self._session_factory = session_factory
        self._stock_service = stock_service
        self._symbols = symbols or DEFAULT_TRACKED_SYMBOLS

    async def run_batch(self, window: str) -> BatchResult:
        logger.info("Strategy batch run [%s] starting for %d symbols", window, len(self._symbols))
        result = BatchResult(
            window=window,
            timestamp=datetime.now(timezone.utc),
        )

        async with self._session_factory() as session:
            feature_repo = SQLAlchemyFeatureRepository(session)
            market_score_service = MarketScoreService(feature_repo=feature_repo)
            decision_service = DecisionService(
                market_score_service=market_score_service,
                stock_service=self._stock_service,
            )

            for symbol in self._symbols:
                try:
                    decision = await decision_service.get_decision(symbol)
                    result.snapshots.append(StrategyPerformanceSnapshot(
                        symbol=symbol,
                        name=decision.name,
                        signal=decision.signal.value if decision.signal else "UNKNOWN",
                        signal_label=decision.signal_label,
                        confidence=decision.confidence,
                        action=decision.action.value if decision.action else "UNKNOWN",
                        action_label=decision.action_label,
                        trend=0.0,
                        liquidity=0.0,
                        breadth=0.0,
                        volatility=0.0,
                        sentiment=0.0,
                        timestamp=result.timestamp,
                    ))
                except Exception as e:
                    logger.warning("Batch run failed for %s: %s", symbol, e)
                    result.errors.append(f"{symbol}: {e}")

        result.summary = {
            "total": result.total_count,
            "bullish": result.bullish_count,
            "bearish": result.bearish_count,
            "neutral": result.neutral_count,
            "avg_confidence": result.avg_confidence,
            "errors": len(result.errors),
        }
        logger.info(
            "Strategy batch [%s] complete: %d symbols, %d errors",
            window, result.total_count, len(result.errors),
        )
        return result
