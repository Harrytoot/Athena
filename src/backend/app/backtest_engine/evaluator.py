from dataclasses import dataclass, field

from app.backtest_engine.dataset_builder import BacktestDataset
from app.backtest_engine.metrics import (
    information_coefficient,
    rank_information_coefficient,
    sharpe_ratio,
    win_rate,
)
from app.backtest_engine.signal_generator import generate_series


@dataclass
class PeriodMetrics:
    ic: float = 0.0
    rank_ic: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    mean_return: float = 0.0
    n_observations: int = 0


@dataclass
class BacktestReport:
    total_observations: int = 0
    signal_count: int = 0
    long_count: int = 0
    short_count: int = 0
    neutral_count: int = 0
    period_5d: PeriodMetrics = field(default_factory=PeriodMetrics)
    period_10d: PeriodMetrics = field(default_factory=PeriodMetrics)
    period_20d: PeriodMetrics = field(default_factory=PeriodMetrics)
    score_min: float = 0.0
    score_max: float = 0.0
    score_mean: float = 0.0


class Evaluator:

    def evaluate(self, dataset: BacktestDataset) -> BacktestReport:
        if not dataset.rows:
            return BacktestReport()

        scores = dataset.scores
        signals = dataset.signals

        report = BacktestReport(
            total_observations=len(dataset.rows),
            signal_count=sum(1 for s in signals if s != 0),
            long_count=sum(1 for s in signals if s > 0),
            short_count=sum(1 for s in signals if s < 0),
            neutral_count=sum(1 for s in signals if s == 0),
            score_min=round(min(scores), 2),
            score_max=round(max(scores), 2),
            score_mean=round(sum(scores) / len(scores), 2),
        )

        report.period_5d = self._eval_period(scores, signals, dataset.forward_returns_5d)
        report.period_10d = self._eval_period(scores, signals, dataset.forward_returns_10d)
        report.period_20d = self._eval_period(scores, signals, dataset.forward_returns_20d)

        return report

    def _eval_period(
        self, scores: list[float], signals: list[int], forward_returns: list[float]
    ) -> PeriodMetrics:
        if len(scores) < 3 or len(scores) != len(forward_returns):
            return PeriodMetrics()

        ic = information_coefficient(scores, forward_returns)
        rank_ic = rank_information_coefficient(scores, forward_returns)
        wr = win_rate(signals, forward_returns)

        strategy_returns = []
        for s, r in zip(signals, forward_returns):
            if s != 0:
                strategy_returns.append(s * r)

        shr = sharpe_ratio(strategy_returns) if strategy_returns else 0.0
        mean_r = round(sum(forward_returns) / len(forward_returns), 6) if forward_returns else 0.0

        return PeriodMetrics(
            ic=ic,
            rank_ic=rank_ic,
            sharpe=shr,
            win_rate=wr,
            mean_return=mean_r,
            n_observations=len(scores),
        )
