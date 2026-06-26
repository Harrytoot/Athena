import pytest

from app.backtest_engine.dataset_builder import BacktestDataset, BacktestRow
from app.backtest_engine.evaluator import Evaluator, BacktestReport


def _row(score: float, fr5: float = 0.0, fr10: float = 0.0, fr20: float = 0.0) -> BacktestRow:
    return BacktestRow(
        timestamp=None,
        score=score,
        state="Bull" if score >= 60 else "Neutral" if score >= 40 else "Bear",
        trend=50.0,
        liquidity=50.0,
        breadth=50.0,
        volatility=50.0,
        sentiment=50.0,
        price=100.0,
        forward_return_5d=fr5,
        forward_return_10d=fr10,
        forward_return_20d=fr20,
    )


class TestEvaluator:

    def test_evaluate_returns_report(self):
        rows = [
            _row(80, 0.02),
            _row(70, 0.01),
            _row(50, 0.0),
            _row(30, -0.01),
            _row(20, -0.02),
        ]
        dataset = BacktestDataset(rows=rows)
        evaluator = Evaluator()
        report = evaluator.evaluate(dataset)
        assert isinstance(report, BacktestReport)

    def test_report_contains_all_metrics(self):
        rows = [
            _row(80, 0.02),
            _row(70, 0.01),
            _row(60, 0.005),
            _row(50, 0.0),
            _row(40, -0.005),
            _row(30, -0.01),
            _row(20, -0.02),
        ]
        dataset = BacktestDataset(rows=rows)
        evaluator = Evaluator()
        report = evaluator.evaluate(dataset)
        assert report.total_observations == 7
        assert report.period_5d.ic is not None
        assert report.period_5d.rank_ic is not None
        assert report.period_10d.sharpe is not None
        assert report.period_20d.win_rate is not None

    def test_report_tracks_signal_counts(self):
        rows = [
            _row(80, 0.01),   # long
            _row(60, 0.01),   # long
            _row(50, 0.0),    # neutral
            _row(40, -0.01),  # short
            _row(20, -0.01),  # short
        ]
        dataset = BacktestDataset(rows=rows)
        evaluator = Evaluator()
        report = evaluator.evaluate(dataset)
        assert report.long_count == 2
        assert report.short_count == 2
        assert report.neutral_count == 1
        assert report.signal_count == 4

    def test_empty_dataset_returns_empty_report(self):
        dataset = BacktestDataset(rows=[])
        evaluator = Evaluator()
        report = evaluator.evaluate(dataset)
        assert report.total_observations == 0

    def test_score_statistics(self):
        rows = [
            _row(30, 0.0),
            _row(50, 0.0),
            _row(70, 0.0),
        ]
        dataset = BacktestDataset(rows=rows)
        evaluator = Evaluator()
        report = evaluator.evaluate(dataset)
        assert report.score_min == 30.0
        assert report.score_max == 70.0
        assert report.score_mean == 50.0

    def test_ic_positive_when_scores_predict_returns(self):
        rows = [
            _row(80, 0.03),
            _row(75, 0.02),
            _row(60, 0.01),
            _row(40, -0.01),
            _row(30, -0.02),
            _row(20, -0.03),
        ]
        dataset = BacktestDataset(rows=rows)
        evaluator = Evaluator()
        report = evaluator.evaluate(dataset)
        assert report.period_5d.ic > 0
