from datetime import datetime, timezone, timedelta

import pytest

from app.backtest_engine.dataset_builder import BacktestDataset, BacktestRow
from app.strategy_validation.signal_decay import DecayPoint, DecayReport, SignalDecayAnalyzer


def _row(
    ts: datetime,
    score: float,
    forward_return_5d: float = 0.0,
    forward_return_10d: float = 0.0,
    forward_return_20d: float = 0.0,
) -> BacktestRow:
    return BacktestRow(
        timestamp=ts,
        score=score,
        state="Bull" if score >= 60 else "Neutral" if score >= 40 else "Bear",
        trend=50.0,
        liquidity=50.0,
        breadth=50.0,
        volatility=50.0,
        sentiment=50.0,
        price=100.0,
        forward_return_5d=forward_return_5d,
        forward_return_10d=forward_return_10d,
        forward_return_20d=forward_return_20d,
    )


class TestSignalDecayAnalyzer:

    def test_analyze_returns_three_horizon_points(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i, 0.01, 0.02, 0.03)
            for i in range(30)
        ]
        dataset = BacktestDataset(rows=rows)

        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        assert len(report.points) == 3
        horizons = {p.horizon for p in report.points}
        assert horizons == {5, 10, 20}

    def test_decay_point_has_all_fields(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i, 0.01, 0.02, 0.03)
            for i in range(20)
        ]
        dataset = BacktestDataset(rows=rows)

        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        for point in report.points:
            assert isinstance(point.horizon, int)
            assert isinstance(point.horizon_label, str)
            assert isinstance(point.ic, float)
            assert isinstance(point.rank_ic, float)
            assert isinstance(point.mean_abs_return, float)
            assert point.mean_abs_return >= 0.0

    def test_empty_dataset(self):
        dataset = BacktestDataset(rows=[])
        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        assert len(report.points) == 0
        assert report.optimal_horizon == "unknown"
        assert report.max_ic == 0.0

    def test_optimal_horizon_matches_highest_abs_ic(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(30):
            ts = base + timedelta(days=i)
            score = 50.0 + i
            rows.append(_row(ts, score, 0.01, 0.05, 0.02))
        dataset = BacktestDataset(rows=rows)

        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        highest = max(report.points, key=lambda p: abs(p.ic))
        assert report.optimal_horizon == highest.horizon_label

    def test_max_ic(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i, 0.01, 0.02, 0.03)
            for i in range(20)
        ]
        dataset = BacktestDataset(rows=rows)

        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        assert report.max_ic == max(p.ic for p in report.points)

    def test_signal_decay_with_correlated_scores(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(20):
            ts = base + timedelta(days=i)
            score = 60.0 + i * 2.0
            rows.append(_row(ts, score, 0.02, 0.015, 0.01))
        dataset = BacktestDataset(rows=rows)

        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        for point in report.points:
            assert -1.0 <= point.ic <= 1.0
            assert -1.0 <= point.rank_ic <= 1.0

    def test_small_dataset_still_works(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i * 10, 0.01, 0.02, 0.03)
            for i in range(5)
        ]
        dataset = BacktestDataset(rows=rows)

        analyzer = SignalDecayAnalyzer()
        report = analyzer.analyze(dataset)

        assert len(report.points) == 3
