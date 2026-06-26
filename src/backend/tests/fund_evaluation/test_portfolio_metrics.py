import pytest

from app.fund_evaluation.portfolio_metrics import (
    DistributionStats,
    PortfolioMetricsAnalyzer,
    PortfolioStabilityMetrics,
    RollingSharpePoint,
)
from tests.fund_evaluation import _build_history, _make_strategy


class TestPortfolioMetricsAnalyzer:

    def test_empty_strategies(self):
        analyzer = PortfolioMetricsAnalyzer()
        result = analyzer.analyze([], [])
        assert isinstance(result, PortfolioStabilityMetrics)
        assert result.rolling_sharpes == []
        assert result.mean_rolling_sharpe == 0.0

    def test_single_strategy_with_history(self):
        history = _build_history(
            position_pcts=[1.0] * 120,
            prices=[100.0 + i * 0.2 + (i * 0.01 if i % 3 == 0 else -i * 0.005) for i in range(120)],
        )
        strategy = _make_strategy("s1", sharpe=1.0, history=history)
        analyzer = PortfolioMetricsAnalyzer(window_size=60)
        result = analyzer.analyze([strategy], [1.0])

        assert result.rolling_sharpes
        assert result.distribution is not None
        assert result.monthly_returns
        assert 0.0 <= result.positive_day_ratio <= 1.0

    def test_multiple_strategies(self):
        h1 = _build_history(
            position_pcts=[1.0] * 120,
            prices=[100.0 + i * 0.2 for i in range(120)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 120,
            prices=[100.0 + i * 0.1 for i in range(120)],
        )
        s1 = _make_strategy("momentum", sharpe=1.2, history=h1)
        s2 = _make_strategy("mean_rev", sharpe=0.8, history=h2)
        analyzer = PortfolioMetricsAnalyzer(window_size=60)
        result = analyzer.analyze([s1, s2], [0.6, 0.4])

        assert len(result.rolling_sharpes) > 0
        assert result.mean_rolling_sharpe != 0.0
        assert result.distribution is not None

    def test_no_history_fallback(self):
        s1 = _make_strategy("s1")
        s2 = _make_strategy("s2")
        analyzer = PortfolioMetricsAnalyzer()
        result = analyzer.analyze([s1, s2], [0.5, 0.5])

        assert isinstance(result, PortfolioStabilityMetrics)
        assert result.rolling_sharpes == []
        assert result.sharpe_stability == 0.0

    def test_sharpe_stability_range(self):
        history = _build_history(
            position_pcts=[0.5] * 150,
            prices=[100.0 + i * 0.15 for i in range(150)],
        )
        strategy = _make_strategy("s1", sharpe=1.0, history=history)
        analyzer = PortfolioMetricsAnalyzer(window_size=60)
        result = analyzer.analyze([strategy], [1.0])

        assert 0.0 <= result.sharpe_stability <= 1.0

    def test_distribution_stats_populated(self):
        history = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 + i * 0.3 for i in range(100)],
        )
        strategy = _make_strategy("s1", sharpe=1.0, history=history)
        analyzer = PortfolioMetricsAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        dist = result.distribution
        assert dist is not None
        assert isinstance(dist.mean, float)
        assert dist.std >= 0
        assert isinstance(dist.skewness, float)
        assert isinstance(dist.kurtosis, float)
        assert isinstance(dist.var_95, float)

    def test_monthly_returns(self):
        history = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.2 for i in range(100)],
        )
        strategy = _make_strategy("s1", sharpe=1.0, history=history)
        analyzer = PortfolioMetricsAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert len(result.monthly_returns) > 0
        assert 0.0 <= result.monthly_win_rate <= 1.0

    def test_short_history(self):
        history = _build_history(
            position_pcts=[1.0] * 30,
            prices=[100.0 + i * 0.5 for i in range(30)],
        )
        strategy = _make_strategy("s1", sharpe=1.0, history=history)
        analyzer = PortfolioMetricsAnalyzer(window_size=60)
        result = analyzer.analyze([strategy], [1.0])

        assert result.rolling_sharpes == []

    def test_negative_return_strategy(self):
        history = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 - i * 0.2 for i in range(100)],
        )
        strategy = _make_strategy("s1", sharpe=-0.5, history=history)
        analyzer = PortfolioMetricsAnalyzer(window_size=40)
        result = analyzer.analyze([strategy], [1.0])

        assert result.annualized_sharpe < 0

    def test_annualized_sharpe_computed(self):
        history = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.1 for i in range(100)],
        )
        strategy = _make_strategy("s1", sharpe=1.0, history=history)
        analyzer = PortfolioMetricsAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.annualized_sharpe != 0.0
