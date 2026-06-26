from datetime import datetime, timezone, timedelta

import pytest

from app.backtest_engine.dataset_builder import BacktestDataset, BacktestRow
from app.strategy_validation.ic_analyzer import ICAnalyzer, ICResult, RollingICReport


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


class TestICAnalyzer:

    def test_analyze_returns_reports_for_all_horizons(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(40):
            ts = base + timedelta(days=i)
            score = 30.0 + i * 1.5
            rows.append(_row(ts, score, 0.01, 0.02, 0.03))
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        assert len(reports) == 3
        horizons = {r.horizon for r in reports}
        assert horizons == {"5d", "10d", "20d"}

    def test_mean_ic_computed(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(50):
            ts = base + timedelta(days=i)
            score = 50.0 + i * 1.0
            rows.append(_row(ts, score, 0.01, 0.02, 0.03))
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        for report in reports:
            assert len(report.results) > 0
            assert isinstance(report.mean_ic, float)
            assert isinstance(report.mean_rank_ic, float)

    def test_ic_positive_ratio_in_range(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(50):
            ts = base + timedelta(days=i)
            score = 50.0 + i * 1.0
            rows.append(_row(ts, score, 0.01, 0.02, 0.03))
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        for report in reports:
            assert 0.0 <= report.ic_positive_ratio <= 1.0

    def test_empty_dataset_produces_empty_reports(self):
        dataset = BacktestDataset(rows=[])
        analyzer = ICAnalyzer(window_size=20)
        reports = analyzer.analyze(dataset)

        assert len(reports) == 3
        for report in reports:
            assert len(report.results) == 0
            assert report.mean_ic == 0.0
            assert report.mean_rank_ic == 0.0
            assert report.ic_positive_ratio == 0.0

    def test_small_dataset_below_min_window(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i, 0.01, 0.02, 0.03)
            for i in range(5)
        ]
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        for report in reports:
            assert len(report.results) == 0

    def test_rolling_windows_have_correct_size(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(60):
            ts = base + timedelta(days=i)
            score = 50.0 + i
            rows.append(_row(ts, score, 0.01, 0.02, 0.03))
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        for report in reports:
            for result in report.results:
                assert result.n_observations <= 20
                assert result.n_observations >= 10

    def test_ic_result_contains_all_fields(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(40):
            ts = base + timedelta(days=i)
            score = 50.0 + i
            rows.append(_row(ts, score, 0.01, 0.02, 0.03))
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        for report in reports:
            for result in report.results:
                assert isinstance(result.ic, float)
                assert isinstance(result.rank_ic, float)
                assert isinstance(result.start_time, datetime)
                assert isinstance(result.end_time, datetime)
                assert result.start_idx < result.end_idx

    def test_ic_std_computed(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(50):
            ts = base + timedelta(days=i)
            score = 50.0 + i
            rows.append(_row(ts, score, 0.01, 0.02, 0.03))
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=20, min_window=10)
        reports = analyzer.analyze(dataset)

        for report in reports:
            assert report.ic_std >= 0.0

    def test_single_window_produces_zero_std(self):
        base = datetime.now(timezone.utc)
        rows = [_row(base + timedelta(days=i), 50.0 + i, 0.01, 0.02, 0.03) for i in range(25)]
        dataset = BacktestDataset(rows=rows)

        analyzer = ICAnalyzer(window_size=50, min_window=20)
        reports = analyzer.analyze(dataset)

        for report in reports:
            assert report.ic_std == 0.0
