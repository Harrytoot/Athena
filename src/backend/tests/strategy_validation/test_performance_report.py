from datetime import datetime, timezone, timedelta

import pytest

from app.backtest_engine.dataset_builder import BacktestDataset, BacktestRow
from app.strategy_validation.performance_report import (
    PerformanceReportGenerator,
    RegimePerformance,
    StrategyValidationReport,
)


def _row(
    ts: datetime,
    score: float,
    state: str = None,
    forward_return_5d: float = 0.0,
    forward_return_10d: float = 0.0,
    forward_return_20d: float = 0.0,
) -> BacktestRow:
    if state is None:
        state = "Bull" if score >= 60 else "Neutral" if score >= 40 else "Bear"
    return BacktestRow(
        timestamp=ts,
        score=score,
        state=state,
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


class TestPerformanceReportGenerator:

    def test_generate_returns_complete_report(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(60):
            ts = base + timedelta(days=i)
            score = 50.0 + i
            rows.append(_row(ts, score, forward_return_5d=0.01, forward_return_10d=0.02, forward_return_20d=0.03))
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator(ic_window_size=20)
        report = generator.generate(dataset)

        assert isinstance(report, StrategyValidationReport)
        assert len(report.ic_rolling) == 3
        assert len(report.decay.points) == 3
        assert isinstance(report.stability_score, float)
        assert isinstance(report.overall_assessment, str)
        assert len(report.overall_assessment) > 0

    def test_empty_dataset_produces_default_report(self):
        dataset = BacktestDataset(rows=[])
        generator = PerformanceReportGenerator()
        report = generator.generate(dataset)

        assert report.stability_score == 0.0
        assert len(report.ic_rolling) == 3
        for r in report.ic_rolling:
            assert len(r.results) == 0
        assert len(report.decay.points) == 0
        assert len(report.regime.segments) == 0
        assert len(report.regime_performance) == 0

    def test_stability_score_in_range(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(80):
            ts = base + timedelta(days=i)
            score = 50.0 + i
            rows.append(_row(ts, score, forward_return_5d=0.01, forward_return_10d=0.02, forward_return_20d=0.03))
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator(ic_window_size=20)
        report = generator.generate(dataset)

        assert 0.0 <= report.stability_score <= 1.0

    def test_multiple_regimes_produces_segmented_performance(self):
        base = datetime.now(timezone.utc)
        states = ["Bull"] * 20 + ["Bear"] * 20 + ["Bull"] * 20
        rows = []
        for i, state in enumerate(states):
            score = 70.0 if state == "Bull" else 30.0
            ret = 0.02 if state == "Bull" else -0.02
            rows.append(_row(
                base + timedelta(days=i),
                score,
                state=state,
                forward_return_5d=ret,
                forward_return_10d=ret,
                forward_return_20d=ret,
            ))
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator(ic_window_size=20, regime_min_segment=5)
        report = generator.generate(dataset)

        assert len(report.regime_performance) >= 1
        for rp in report.regime_performance:
            assert rp.regime in ("Bull", "Bear", "Sideways")
            assert rp.n_observations > 0

    def test_regime_performance_fields(self):
        base = datetime.now(timezone.utc)
        rows = []
        for i in range(30):
            score = 70.0 if i < 15 else 30.0
            state = "Bull" if i < 15 else "Bear"
            rows.append(_row(
                base + timedelta(days=i),
                score,
                state=state,
                forward_return_5d=0.01,
                forward_return_10d=0.02,
                forward_return_20d=0.03,
            ))
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator(regime_min_segment=1)
        report = generator.generate(dataset)

        for rp in report.regime_performance:
            assert isinstance(rp.ic_5d, float)
            assert isinstance(rp.ic_10d, float)
            assert isinstance(rp.ic_20d, float)
            assert isinstance(rp.rank_ic_5d, float)
            assert isinstance(rp.rank_ic_10d, float)
            assert isinstance(rp.rank_ic_20d, float)

    def test_assessment_contains_key_info(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i, forward_return_5d=0.01, forward_return_10d=0.02, forward_return_20d=0.03)
            for i in range(50)
        ]
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator()
        report = generator.generate(dataset)

        assert "IC" in report.overall_assessment or "stability" in report.overall_assessment.lower()
        assert "horizon" in report.overall_assessment.lower()

    def test_small_dataset_stability_zero(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 50.0 + i, forward_return_5d=0.01, forward_return_10d=0.02, forward_return_20d=0.03)
            for i in range(15)
        ]
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator(ic_window_size=20)
        report = generator.generate(dataset)

        assert report.stability_score == 0.0

    def test_single_regime_all_data(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=i), 70.0, state="Bull", forward_return_5d=0.01, forward_return_10d=0.02, forward_return_20d=0.03)
            for i in range(50)
        ]
        dataset = BacktestDataset(rows=rows)

        generator = PerformanceReportGenerator()
        report = generator.generate(dataset)

        assert len(report.regime_performance) == 1
        assert report.regime_performance[0].regime == "Bull"
        assert report.regime_performance[0].n_observations == 50
