import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class LatencyConfig:
    base_latency_ms: float = 50.0
    network_jitter_ms: float = 10.0
    processing_delay_ms: float = 5.0
    max_queue_depth: int = 100
    seed: int | None = None


@dataclass
class ExecutionDelay:
    strategy_id: str
    intended_time: datetime
    actual_time: datetime
    delay_ms: float
    delay_type: str = "normal"

    @property
    def delay_seconds(self) -> float:
        return self.delay_ms / 1000.0


@dataclass
class ScheduledTrade:
    strategy_id: str
    side: str
    notional: float
    quantity: float
    scheduled_time: datetime
    executed_time: datetime | None = None
    delay: ExecutionDelay | None = None
    status: str = "pending"
    priority: int = 0

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"


@dataclass
class ScheduleResult:
    trades: list[ScheduledTrade] = field(default_factory=list)
    total_execution_time_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    @property
    def trade_count(self) -> int:
        return len(self.trades)

    @property
    def completed_count(self) -> int:
        return len([t for t in self.trades if t.is_completed])


class TradeScheduler:

    def __init__(self, config: LatencyConfig | None = None):
        self.config = config or LatencyConfig()
        self._rng = random.Random(self.config.seed)
        self._queue: list[ScheduledTrade] = []

    def schedule(
        self,
        trades: list[tuple[str, str, float, float]],
        start_time: datetime | None = None,
    ) -> ScheduleResult:
        if start_time is None:
            start_time = datetime.now(timezone.utc)

        self._queue = []
        scheduled: list[ScheduledTrade] = []

        for i, (strategy_id, side, notional, quantity) in enumerate(trades):
            base_delay = self._compute_base_delay()
            scheduled_time = start_time + timedelta(milliseconds=base_delay * (i + 1))

            priority = 1 if side == "sell" else 0

            trade = ScheduledTrade(
                strategy_id=strategy_id,
                side=side,
                notional=notional,
                quantity=quantity,
                scheduled_time=scheduled_time,
                priority=priority,
            )
            self._queue.append(trade)

        self._queue.sort(key=lambda t: (t.priority, t.scheduled_time))

        for trade in self._queue:
            delay = self._compute_delay(trade, start_time)
            executed_time = start_time + timedelta(milliseconds=delay.delay_ms)

            trade.executed_time = executed_time
            trade.delay = delay
            trade.status = "completed"
            scheduled.append(trade)

        total_ms = 0.0
        max_ms = 0.0
        completed = [t for t in scheduled if t.delay is not None]
        for t in completed:
            d = t.delay.delay_ms
            total_ms += d
            max_ms = max(max_ms, d)

        avg_ms = total_ms / len(completed) if completed else 0.0

        return ScheduleResult(
            trades=scheduled,
            total_execution_time_ms=round(total_ms, 2),
            avg_latency_ms=round(avg_ms, 2),
            max_latency_ms=round(max_ms, 2),
        )

    def _compute_base_delay(self) -> float:
        return (
            self.config.base_latency_ms
            + self.config.processing_delay_ms
            + self._rng.gauss(0, self.config.network_jitter_ms)
        )

    def _compute_delay(self, trade: ScheduledTrade, start_time: datetime) -> ExecutionDelay:
        base = self._compute_base_delay()

        delay_type = "normal"
        if self._rng.random() < 0.05:
            base *= 2.0
            delay_type = "congestion"
        if self._rng.random() < 0.01:
            base *= 5.0
            delay_type = "anomalous"

        delay_ms = max(1.0, base)

        actual_time = start_time + timedelta(milliseconds=delay_ms)

        return ExecutionDelay(
            strategy_id=trade.strategy_id,
            intended_time=trade.scheduled_time,
            actual_time=actual_time,
            delay_ms=round(delay_ms, 2),
            delay_type=delay_type,
        )

    def queue_depth(self) -> int:
        return len([t for t in self._queue if t.status == "pending"])

    def reset_seed(self, seed: int):
        self._rng = random.Random(seed)
