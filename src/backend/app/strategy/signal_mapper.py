from dataclasses import dataclass
from datetime import datetime

from app.backtest_engine.dataset_builder import BacktestDataset

LONG_THRESHOLD = 60.0
SHORT_THRESHOLD = 40.0
SCORE_MAX = 100.0
SCORE_MIN = 0.0


@dataclass
class SizedSignal:
    timestamp: datetime
    score: float
    direction: int
    weight: float


class SignalMapper:

    def __init__(
        self,
        long_threshold: float = LONG_THRESHOLD,
        short_threshold: float = SHORT_THRESHOLD,
    ):
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold

    def map_score(self, score: float, timestamp: datetime) -> SizedSignal:
        direction = 0
        weight = 0.0
        if score >= self.long_threshold:
            direction = 1
            weight = min(1.0, (score - self.long_threshold) / (SCORE_MAX - self.long_threshold))
        elif score <= self.short_threshold:
            direction = -1
            weight = min(1.0, (self.short_threshold - score) / self.short_threshold)
        return SizedSignal(timestamp=timestamp, score=score, direction=direction, weight=weight)

    def map_batch(self, scores: list[float], timestamps: list[datetime]) -> list[SizedSignal]:
        return [self.map_score(s, ts) for s, ts in zip(scores, timestamps)]

    def map_dataset(self, dataset: BacktestDataset) -> list[SizedSignal]:
        return [self.map_score(r.score, r.timestamp) for r in dataset.rows]
