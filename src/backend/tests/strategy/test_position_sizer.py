from datetime import datetime, timezone

import pytest

from app.strategy.position_sizer import DEFAULT_BASE_ALLOCATION, PositionSizer, StrategyPosition
from app.strategy.signal_mapper import SizedSignal


def _signal(score: float = 80.0, ts: datetime | None = None) -> SizedSignal:
    if ts is None:
        ts = datetime.now(timezone.utc)
    direction = 1 if score >= 60 else (-1 if score <= 40 else 0)
    weight = 0.5
    return SizedSignal(timestamp=ts, score=score, direction=direction, weight=weight)


class TestPositionSizer:

    def test_size_long_signal(self):
        sizer = PositionSizer()
        signal = SizedSignal(
            timestamp=datetime.now(timezone.utc),
            score=80.0,
            direction=1,
            weight=0.5,
        )
        pos = sizer.size(signal, nav=100000.0)
        assert pos.direction == 1
        assert pos.position_pct == 0.5
        assert pos.notional == 50000.0

    def test_size_short_signal(self):
        sizer = PositionSizer()
        signal = SizedSignal(
            timestamp=datetime.now(timezone.utc),
            score=20.0,
            direction=-1,
            weight=0.8,
        )
        pos = sizer.size(signal, nav=100000.0)
        assert pos.direction == -1
        assert pos.position_pct == -0.8
        assert pos.notional == -80000.0

    def test_size_neutral_signal(self):
        sizer = PositionSizer()
        signal = SizedSignal(
            timestamp=datetime.now(timezone.utc),
            score=50.0,
            direction=0,
            weight=0.0,
        )
        pos = sizer.size(signal, nav=100000.0)
        assert pos.direction == 0
        assert pos.position_pct == 0.0
        assert pos.notional == 0.0

    def test_default_nav(self):
        sizer = PositionSizer()
        signal = _signal(score=80.0)
        signal.weight = 1.0
        pos = sizer.size(signal)
        assert pos.notional == 1.0
        assert pos.position_pct == 1.0

    def test_custom_base_allocation(self):
        sizer = PositionSizer(base_allocation=0.5)
        signal = _signal(score=80.0)
        signal.weight = 1.0
        pos = sizer.size(signal, nav=100000.0)
        assert pos.position_pct == 0.5
        assert pos.notional == 50000.0

    def test_size_all_with_nav_series(self):
        sizer = PositionSizer()
        ts = datetime.now(timezone.utc)
        signals = [
            SizedSignal(timestamp=ts, score=80.0, direction=1, weight=1.0),
            SizedSignal(timestamp=ts, score=20.0, direction=-1, weight=0.5),
        ]
        nav_series = [100000.0, 95000.0]
        positions = sizer.size_all(signals, nav_series)
        assert len(positions) == 2
        assert positions[0].notional == 100000.0
        assert positions[1].notional == -47500.0

    def test_size_all_no_nav_series(self):
        sizer = PositionSizer()
        ts = datetime.now(timezone.utc)
        signals = [
            SizedSignal(timestamp=ts, score=80.0, direction=1, weight=0.5),
            SizedSignal(timestamp=ts, score=50.0, direction=0, weight=0.0),
        ]
        positions = sizer.size_all(signals)
        assert len(positions) == 2
        assert positions[0].position_pct == 0.5
        assert positions[1].position_pct == 0.0

    def test_size_all_mismatched_lengths(self):
        sizer = PositionSizer()
        ts = datetime.now(timezone.utc)
        signals = [
            SizedSignal(timestamp=ts, score=80.0, direction=1, weight=0.5),
        ]
        nav_series = [100000.0, 90000.0]
        positions = sizer.size_all(signals, nav_series)
        assert len(positions) == 1
        assert positions[0].position_pct == 0.5

    def test_strategy_position_dataclass_fields(self):
        ts = datetime.now(timezone.utc)
        pos = StrategyPosition(
            timestamp=ts,
            direction=1,
            signal_weight=0.5,
            position_pct=0.5,
            notional=50000.0,
        )
        assert pos.timestamp == ts
        assert pos.direction == 1
        assert pos.signal_weight == 0.5
        assert pos.position_pct == 0.5
        assert pos.notional == 50000.0
