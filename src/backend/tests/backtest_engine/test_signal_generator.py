from app.backtest_engine.signal_generator import generate_signal, generate_series


class TestGenerateSignal:

    def test_long_above_threshold(self):
        assert generate_signal(80) == 1
        assert generate_signal(60) == 1

    def test_short_below_threshold(self):
        assert generate_signal(20) == -1
        assert generate_signal(40) == -1

    def test_neutral_mid_range(self):
        assert generate_signal(50) == 0
        assert generate_signal(45) == 0
        assert generate_signal(55) == 0

    def test_edge_cases(self):
        assert generate_signal(100) == 1
        assert generate_signal(0) == -1


class TestGenerateSeries:

    def test_series_length_matches(self):
        scores = [80, 50, 30]
        signals = generate_series(scores)
        assert len(signals) == 3
        assert signals == [1, 0, -1]

    def test_empty_series(self):
        assert generate_series([]) == []
