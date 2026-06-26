from dataclasses import dataclass, field

from app.backtest_engine.dataset_builder import BacktestDataset
from app.backtest_engine.metrics import information_coefficient, rank_information_coefficient


@dataclass
class DecayPoint:
    horizon: int
    horizon_label: str
    ic: float
    rank_ic: float
    mean_abs_return: float


@dataclass
class DecayReport:
    points: list[DecayPoint] = field(default_factory=list)

    @property
    def optimal_horizon(self) -> str:
        if not self.points:
            return "unknown"
        return max(self.points, key=lambda p: abs(p.ic)).horizon_label

    @property
    def max_ic(self) -> float:
        if not self.points:
            return 0.0
        return max(p.ic for p in self.points)


class SignalDecayAnalyzer:

    def analyze(self, dataset: BacktestDataset) -> DecayReport:
        if not dataset.rows:
            return DecayReport()

        scores = dataset.scores
        horizons = [
            (5, "5d", dataset.forward_returns_5d),
            (10, "10d", dataset.forward_returns_10d),
            (20, "20d", dataset.forward_returns_20d),
        ]

        points = []
        for horizon, label, returns in horizons:
            ic = information_coefficient(scores, returns)
            rank_ic = rank_information_coefficient(scores, returns)
            mean_abs_r = (
                sum(abs(r) for r in returns) / len(returns) if returns else 0.0
            )
            points.append(
                DecayPoint(
                    horizon=horizon,
                    horizon_label=label,
                    ic=ic,
                    rank_ic=rank_ic,
                    mean_abs_return=round(mean_abs_r, 6),
                )
            )

        return DecayReport(points=points)
