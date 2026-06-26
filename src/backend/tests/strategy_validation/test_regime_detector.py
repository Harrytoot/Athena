from datetime import datetime, timezone, timedelta

from app.backtest_engine.dataset_builder import BacktestDataset, BacktestRow
from app.strategy_validation.regime_detector import (
    RegimeDetector,
    RegimeReport,
    RegimeSegment,
    _map_regime,
)


def _row(
    ts: datetime,
    score: float,
    state: str,
) -> BacktestRow:
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
        forward_return_5d=0.0,
        forward_return_10d=0.0,
        forward_return_20d=0.0,
    )


class TestMapRegime:

    def test_bull_states(self):
        assert _map_regime("Strong Bull") == "Bull"
        assert _map_regime("Bull") == "Bull"

    def test_bear_states(self):
        assert _map_regime("Extreme Bear") == "Bear"
        assert _map_regime("Bear") == "Bear"

    def test_neutral_state(self):
        assert _map_regime("Neutral") == "Sideways"

    def test_unknown_state_defaults_to_sideways(self):
        assert _map_regime("Unknown") == "Sideways"


class TestRegimeDetector:

    def test_detect_contiguous_bull_segment(self):
        base = datetime.now(timezone.utc)
        rows = [_row(base + timedelta(days=i), 70.0, "Bull") for i in range(20)]
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=5)
        report = detector.detect(dataset)

        assert len(report.segments) == 1
        assert report.segments[0].regime == "Bull"
        assert report.segments[0].n_days == 20
        assert report.bull_ratio == 1.0
        assert report.bear_ratio == 0.0
        assert report.sideways_ratio == 0.0

    def test_detect_multiple_regime_changes(self):
        base = datetime.now(timezone.utc)
        states = (
            ["Bull"] * 10
            + ["Neutral"] * 8
            + ["Bear"] * 12
            + ["Bull"] * 15
        )
        rows = []
        for i, state in enumerate(states):
            score = 70.0 if state == "Bull" else 50.0 if state == "Neutral" else 30.0
            rows.append(_row(base + timedelta(days=i), score, state))
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=5)
        report = detector.detect(dataset)

        assert len(report.segments) == 4
        assert report.segments[0].regime == "Bull"
        assert report.segments[0].n_days == 10
        assert report.segments[1].regime == "Sideways"
        assert report.segments[1].n_days == 8
        assert report.segments[2].regime == "Bear"
        assert report.segments[2].n_days == 12
        assert report.segments[3].regime == "Bull"
        assert report.segments[3].n_days == 15

    def test_regime_ratios_sum_to_one(self):
        base = datetime.now(timezone.utc)
        states = ["Bull"] * 10 + ["Neutral"] * 5 + ["Bear"] * 10
        rows = []
        for i, state in enumerate(states):
            score = 70.0 if state == "Bull" else 50.0 if state == "Neutral" else 30.0
            rows.append(_row(base + timedelta(days=i), score, state))
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=1)
        report = detector.detect(dataset)

        total = report.bull_ratio + report.bear_ratio + report.sideways_ratio
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_empty_dataset(self):
        dataset = BacktestDataset(rows=[])
        detector = RegimeDetector()
        report = detector.detect(dataset)

        assert len(report.segments) == 0
        assert report.bull_ratio == 0.0
        assert report.bear_ratio == 0.0
        assert report.sideways_ratio == 0.0
        assert report.dominant_regime == "unknown"

    def test_min_segment_days_filters_short_segments(self):
        base = datetime.now(timezone.utc)
        states = (
            ["Bull"] * 15
            + ["Bear"] * 2
            + ["Bull"] * 10
        )
        rows = []
        for i, state in enumerate(states):
            score = 70.0 if state == "Bull" else 30.0
            rows.append(_row(base + timedelta(days=i), score, state))
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=5)
        report = detector.detect(dataset)

        assert len(report.segments) == 2
        assert all(s.n_days >= 5 for s in report.segments)
        assert report.bull_ratio == 1.0

    def test_segment_avg_score(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=0), 60.0, "Bull"),
            _row(base + timedelta(days=1), 70.0, "Bull"),
            _row(base + timedelta(days=2), 80.0, "Bull"),
        ]
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=1)
        report = detector.detect(dataset)

        assert report.segments[0].avg_score == 70.0

    def test_dominant_regime(self):
        base = datetime.now(timezone.utc)
        states = ["Bear"] * 30 + ["Bull"] * 10 + ["Neutral"] * 5
        rows = []
        for i, state in enumerate(states):
            score = 70.0 if state == "Bull" else 50.0 if state == "Neutral" else 30.0
            rows.append(_row(base + timedelta(days=i), score, state))
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=1)
        report = detector.detect(dataset)

        assert report.dominant_regime == "Bear"
        assert report.regime_count == 3

    def test_avg_segment_days(self):
        base = datetime.now(timezone.utc)
        states = ["Bull"] * 10 + ["Bear"] * 20
        rows = []
        for i, state in enumerate(states):
            score = 70.0 if state == "Bull" else 30.0
            rows.append(_row(base + timedelta(days=i), score, state))
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=1)
        report = detector.detect(dataset)

        assert report.avg_segment_days == 15.0

    def test_strong_bull_and_bull_merged_to_bull(self):
        base = datetime.now(timezone.utc)
        rows = [
            _row(base + timedelta(days=0), 85.0, "Strong Bull"),
            _row(base + timedelta(days=1), 75.0, "Bull"),
            _row(base + timedelta(days=2), 65.0, "Bull"),
            _row(base + timedelta(days=3), 55.0, "Neutral"),
        ]
        dataset = BacktestDataset(rows=rows)

        detector = RegimeDetector(min_segment_days=1)
        report = detector.detect(dataset)

        assert report.segments[0].regime == "Bull"
        assert report.segments[0].n_days == 3

import pytest
