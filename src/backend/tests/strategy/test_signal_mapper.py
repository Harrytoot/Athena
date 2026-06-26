from datetime import datetime, timezone

import pytest

from app.strategy.signal_mapper import LONG_THRESHOLD, SHORT_THRESHOLD, SignalMapper, SizedSignal


class TestSignalMapper:

    def test_strong_long_signal_max_weight(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        signal = mapper.map_score(100.0, ts)
        assert signal.direction == 1
        assert signal.weight == 1.0
        assert signal.score == 100.0

    def test_threshold_long_signal_zero_weight(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        signal = mapper.map_score(60.0, ts)
        assert signal.direction == 1
        assert signal.weight == 0.0

    def test_strong_short_signal_max_weight(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        signal = mapper.map_score(0.0, ts)
        assert signal.direction == -1
        assert signal.weight == 1.0

    def test_threshold_short_signal_zero_weight(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        signal = mapper.map_score(40.0, ts)
        assert signal.direction == -1
        assert signal.weight == 0.0

    def test_neutral_signal(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        signal = mapper.map_score(50.0, ts)
        assert signal.direction == 0
        assert signal.weight == 0.0

    def test_long_signal_weight_increases_with_score(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        s80 = mapper.map_score(80.0, ts)
        s90 = mapper.map_score(90.0, ts)
        assert s80.weight > 0
        assert s90.weight > s80.weight

    def test_short_signal_weight_increases_as_score_decreases(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        s20 = mapper.map_score(20.0, ts)
        s10 = mapper.map_score(10.0, ts)
        assert s20.weight > 0
        assert s10.weight > s20.weight

    def test_weight_never_exceeds_one(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        for score in [0.0, 10.0, 30.0, 50.0, 70.0, 90.0, 100.0]:
            signal = mapper.map_score(score, ts)
            assert 0.0 <= signal.weight <= 1.0

    def test_map_batch(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        scores = [80.0, 50.0, 20.0]
        timestamps = [ts, ts, ts]
        signals = mapper.map_batch(scores, timestamps)
        assert len(signals) == 3
        assert signals[0].direction == 1
        assert signals[1].direction == 0
        assert signals[2].direction == -1

    def test_custom_thresholds(self):
        mapper = SignalMapper(long_threshold=70.0, short_threshold=30.0)
        ts = datetime.now(timezone.utc)
        assert mapper.map_score(80.0, ts).direction == 1
        assert mapper.map_score(65.0, ts).direction == 0
        assert mapper.map_score(20.0, ts).direction == -1

    def test_boundary_scores(self):
        mapper = SignalMapper()
        ts = datetime.now(timezone.utc)
        assert mapper.map_score(LONG_THRESHOLD - 0.01, ts).direction == 0
        assert mapper.map_score(SHORT_THRESHOLD + 0.01, ts).direction == 0

    def test_sized_signal_dataclass_fields(self):
        ts = datetime.now(timezone.utc)
        signal = SizedSignal(timestamp=ts, score=75.0, direction=1, weight=0.5)
        assert signal.timestamp == ts
        assert signal.score == 75.0
        assert signal.direction == 1
        assert signal.weight == 0.5
