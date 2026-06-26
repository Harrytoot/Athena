from dataclasses import dataclass, field
from datetime import datetime

from app.backtest_engine.dataset_builder import BacktestDataset

BULL_STATES = {"Strong Bull", "Bull"}
BEAR_STATES = {"Extreme Bear", "Bear"}
SIDEWAYS_STATES = {"Neutral"}


def _map_regime(state: str) -> str:
    if state in BULL_STATES:
        return "Bull"
    if state in BEAR_STATES:
        return "Bear"
    return "Sideways"


@dataclass
class RegimeSegment:
    regime: str
    start_idx: int
    end_idx: int
    start_time: datetime
    end_time: datetime
    avg_score: float
    n_days: int


@dataclass
class RegimeReport:
    segments: list[RegimeSegment] = field(default_factory=list)

    @property
    def bull_ratio(self) -> float:
        total = sum(s.n_days for s in self.segments)
        if total == 0:
            return 0.0
        return round(
            sum(s.n_days for s in self.segments if s.regime == "Bull") / total, 6
        )

    @property
    def bear_ratio(self) -> float:
        total = sum(s.n_days for s in self.segments)
        if total == 0:
            return 0.0
        return round(
            sum(s.n_days for s in self.segments if s.regime == "Bear") / total, 6
        )

    @property
    def sideways_ratio(self) -> float:
        total = sum(s.n_days for s in self.segments)
        if total == 0:
            return 0.0
        return round(
            sum(s.n_days for s in self.segments if s.regime == "Sideways") / total, 6
        )

    @property
    def dominant_regime(self) -> str:
        if not self.segments:
            return "unknown"
        ratios = {
            "Bull": self.bull_ratio,
            "Bear": self.bear_ratio,
            "Sideways": self.sideways_ratio,
        }
        return max(ratios, key=ratios.get)

    @property
    def regime_count(self) -> int:
        return len(self.segments)

    @property
    def avg_segment_days(self) -> float:
        if not self.segments:
            return 0.0
        return round(sum(s.n_days for s in self.segments) / len(self.segments), 1)


class RegimeDetector:

    def __init__(self, min_segment_days: int = 5):
        self.min_segment_days = min_segment_days

    def detect(self, dataset: BacktestDataset) -> RegimeReport:
        if not dataset.rows:
            return RegimeReport()

        regimes = [_map_regime(r.state) for r in dataset.rows]
        scores = dataset.scores
        timestamps = dataset.timestamps

        segments = []
        i = 0
        n = len(regimes)
        while i < n:
            current_regime = regimes[i]
            j = i + 1
            while j < n and regimes[j] == current_regime:
                j += 1
            segment_len = j - i
            if segment_len >= self.min_segment_days:
                seg_scores = scores[i:j]
                segments.append(
                    RegimeSegment(
                        regime=current_regime,
                        start_idx=i,
                        end_idx=j - 1,
                        start_time=timestamps[i],
                        end_time=timestamps[j - 1],
                        avg_score=round(sum(seg_scores) / len(seg_scores), 2),
                        n_days=segment_len,
                    )
                )
            i = j

        return RegimeReport(segments=segments)
