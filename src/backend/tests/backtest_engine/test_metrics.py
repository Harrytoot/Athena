import math
import pytest

from app.backtest_engine.metrics import (
    information_coefficient,
    pearson_correlation,
    rank_information_coefficient,
    sharpe_ratio,
    spearman_rank_correlation,
    win_rate,
)


class TestPearsonCorrelation:

    def test_perfect_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        assert pearson_correlation(x, y) == pytest.approx(1.0, abs=1e-6)

    def test_perfect_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        assert pearson_correlation(x, y) == pytest.approx(-1.0, abs=1e-6)

    def test_no_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [3, 3, 3, 3, 3]
        assert pearson_correlation(x, y) == 0.0

    def test_returns_zero_for_too_few(self):
        assert pearson_correlation([1], [2]) == 0.0

    def test_returns_zero_for_mismatched_length(self):
        assert pearson_correlation([1, 2], [1]) == 0.0


class TestSpearmanRankCorrelation:

    def test_perfect_monotonic(self):
        x = [10, 20, 30, 40, 50]
        y = [100, 200, 300, 400, 500]
        assert spearman_rank_correlation(x, y) == pytest.approx(1.0, abs=1e-6)

    def test_negative_monotonic(self):
        x = [10, 20, 30, 40, 50]
        y = [500, 400, 300, 200, 100]
        assert spearman_rank_correlation(x, y) == pytest.approx(-1.0, abs=1e-6)


class TestInformationCoefficient:

    def test_ic_positive_with_correlated_data(self):
        scores = [30, 40, 50, 60, 70, 80]
        returns = [-0.02, -0.01, 0.0, 0.01, 0.02, 0.03]
        ic = information_coefficient(scores, returns)
        assert ic > 0


class TestRankInformationCoefficient:

    def test_rank_ic_positive(self):
        scores = [30, 40, 50, 60, 70, 80]
        returns = [-0.02, -0.01, 0.0, 0.01, 0.02, 0.03]
        rank_ic = rank_information_coefficient(scores, returns)
        assert rank_ic > 0


class TestSharpeRatio:

    def test_positive_returns(self):
        returns = [0.01, 0.012, 0.008, 0.015, 0.009, 0.011, 0.013, 0.007, 0.014, 0.01]
        shr = sharpe_ratio(returns)
        assert shr > 0

    def test_negative_returns(self):
        returns = [-0.01, -0.012, -0.008, -0.015, -0.009, -0.011, -0.013, -0.007, -0.014, -0.01]
        shr = sharpe_ratio(returns)
        assert shr < 0

    def test_zero_returns(self):
        returns = [0.0] * 20
        assert sharpe_ratio(returns) == 0.0

    def test_returns_zero_for_few_samples(self):
        assert sharpe_ratio([0.01]) == 0.0


class TestWinRate:

    def test_all_wins(self):
        signals = [1, 1, 1]
        returns = [0.01, 0.02, 0.03]
        assert win_rate(signals, returns) == pytest.approx(1.0, abs=1e-6)

    def test_all_losses(self):
        signals = [1, 1, 1]
        returns = [-0.01, -0.02, -0.03]
        assert win_rate(signals, returns) == 0.0

    def test_mixed(self):
        signals = [1, -1, 1, -1]
        returns = [0.01, -0.02, -0.01, 0.02]
        assert win_rate(signals, returns) == pytest.approx(0.5, abs=1e-6)

    def test_short_win(self):
        signals = [-1]
        returns = [-0.01]
        assert win_rate(signals, returns) == 1.0

    def test_no_signals(self):
        signals = [0, 0, 0]
        returns = [0.01, 0.02, 0.03]
        assert win_rate(signals, returns) == 0.0

    def test_mismatched_length(self):
        assert win_rate([1], [0.01, 0.02]) == 0.0
