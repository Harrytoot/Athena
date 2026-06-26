from dataclasses import dataclass, field
from datetime import datetime

from app.backtest_engine.dataset_builder import BacktestDataset
from app.backtest_engine.metrics import information_coefficient, rank_information_coefficient


@dataclass
class ICResult:
    ic: float
    rank_ic: float
    start_idx: int
    end_idx: int
    start_time: datetime
    end_time: datetime
    n_observations: int


@dataclass
class RollingICReport:
    horizon: str
    window_size: int
    results: list[ICResult] = field(default_factory=list)

    @property
    def mean_ic(self) -> float:
        if not self.results:
            return 0.0
        return round(sum(r.ic for r in self.results) / len(self.results), 6)

    @property
    def mean_rank_ic(self) -> float:
        if not self.results:
            return 0.0
        return round(sum(r.rank_ic for r in self.results) / len(self.results), 6)

    @property
    def ic_positive_ratio(self) -> float:
        if not self.results:
            return 0.0
        return round(sum(1 for r in self.results if r.ic > 0) / len(self.results), 6)

    @property
    def ic_std(self) -> float:
        if len(self.results) < 2:
            return 0.0
        mean = self.mean_ic
        variance = sum((r.ic - mean) ** 2 for r in self.results) / (len(self.results) - 1)
        return round(variance ** 0.5, 6)


class ICAnalyzer:

    def __init__(self, window_size: int = 20, min_window: int = 10):
        self.window_size = window_size
        self.min_window = min_window

    def analyze(self, dataset: BacktestDataset) -> list[RollingICReport]:
        horizons = {
            "5d": dataset.forward_returns_5d,
            "10d": dataset.forward_returns_10d,
            "20d": dataset.forward_returns_20d,
        }
        scores = dataset.scores
        timestamps = dataset.timestamps
        n = len(scores)

        if n < self.min_window:
            return [
                RollingICReport(horizon=h, window_size=self.window_size)
                for h in horizons
            ]

        reports = []
        for horizon_name, forward_returns in horizons.items():
            results = self._compute_rolling_ic(scores, forward_returns, timestamps, n)
            reports.append(
                RollingICReport(
                    horizon=horizon_name,
                    window_size=self.window_size,
                    results=results,
                )
            )
        return reports

    def _compute_rolling_ic(
        self,
        scores: list[float],
        forward_returns: list[float],
        timestamps: list,
        n: int,
    ) -> list[ICResult]:
        results = []
        step = max(1, self.window_size // 4)
        for start in range(0, n - self.min_window + 1, step):
            end = min(start + self.window_size, n)
            if end - start < self.min_window:
                continue

            window_scores = scores[start:end]
            window_returns = forward_returns[start:end]

            ic = information_coefficient(window_scores, window_returns)
            rank_ic = rank_information_coefficient(window_scores, window_returns)

            results.append(
                ICResult(
                    ic=ic,
                    rank_ic=rank_ic,
                    start_idx=start,
                    end_idx=end - 1,
                    start_time=timestamps[start],
                    end_time=timestamps[end - 1],
                    n_observations=end - start,
                )
            )
        return results
