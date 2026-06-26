import pytest

from app.fund_evaluation.strategy_correlation import (
    CorrelationMatrix,
    StrategyCorrelationAnalyzer,
    StrategyCorrelationResult,
)
from tests.fund_evaluation import _build_history, _make_strategy


class TestStrategyCorrelationAnalyzer:

    def test_empty_strategies(self):
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([])
        assert isinstance(result, StrategyCorrelationResult)
        assert result.correlation_matrix.strategy_ids == []

    def test_single_strategy(self):
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([_make_strategy("s1")])
        assert result.diversification_ratio == 0.0

    def test_two_strategies_with_history(self):
        h1 = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 + i * 0.2 for i in range(100)],
        )
        h2 = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 + i * 0.25 for i in range(100)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        assert len(result.correlation_matrix.strategy_ids) == 2
        assert result.correlation_matrix.pearson[0][0] == 1.0
        assert result.correlation_matrix.pearson[1][1] == 1.0
        assert -1.0 <= result.correlation_matrix.pearson[0][1] <= 1.0

    def test_correlation_range(self):
        h1 = _build_history(
            position_pcts=[1.0] * 50,
            prices=[100.0 + i * 0.5 for i in range(50)],
        )
        h2 = _build_history(
            position_pcts=[-1.0] * 50,
            prices=[100.0 + i * 0.5 for i in range(50)],
        )
        s1 = _make_strategy("long", history=h1)
        s2 = _make_strategy("short", history=h2)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        corr = result.correlation_matrix.pearson[0][1]
        assert -1.0 <= corr <= 1.0

    def test_three_strategies(self):
        h1 = _build_history(
            position_pcts=[0.8] * 80,
            prices=[100.0 + i * 0.3 for i in range(80)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 80,
            prices=[100.0 + i * 0.15 for i in range(80)],
        )
        h3 = _build_history(
            position_pcts=[1.0] * 80,
            prices=[100.0 + i * (-0.1 if i % 3 == 0 else 0.2) for i in range(80)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        s3 = _make_strategy("s3", history=h3)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2, s3])

        assert len(result.correlation_matrix.strategy_ids) == 3
        assert len(result.correlation_matrix.pearson) == 3
        assert len(result.correlation_matrix.spearman) == 3
        assert -1.0 <= result.avg_pairwise_corr <= 1.0

    def test_diversification_ratio(self):
        h1 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.1 for i in range(100)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * (-0.05 if i % 2 == 0 else 0.15) for i in range(100)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        assert result.diversification_ratio >= 1.0

    def test_effective_n(self):
        h1 = _build_history(
            position_pcts=[1.0] * 60,
            prices=[100.0 + i * 0.2 for i in range(60)],
        )
        h2 = _build_history(
            position_pcts=[1.0] * 60,
            prices=[100.0 + i * 0.15 for i in range(60)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        assert result.effective_n > 0

    def test_no_history_fallback(self):
        s1 = _make_strategy("s1")
        s2 = _make_strategy("s2")
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        assert isinstance(result, StrategyCorrelationResult)
        assert result.correlation_matrix.strategy_ids == ["s1", "s2"]

    def test_correlation_matrix_properties(self):
        h1 = _build_history(
            position_pcts=[0.5] * 50,
            prices=[100.0 + i * 0.2 for i in range(50)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 50,
            prices=[100.0 + i * 0.1 for i in range(50)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        matrix = result.correlation_matrix
        assert matrix.get_pearson("s1", "s2") == matrix.pearson[0][1]
        assert matrix.get_pearson("s1", "unknown") == 0.0
        assert isinstance(matrix.avg_pearson, float)
        assert matrix.n_observations > 0

    def test_symmetric_correlation(self):
        h1 = _build_history(
            position_pcts=[1.0] * 60,
            prices=[100.0 + i * 0.3 for i in range(60)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 60,
            prices=[100.0 + i * 0.1 for i in range(60)],
        )
        s1 = _make_strategy("a", history=h1)
        s2 = _make_strategy("b", history=h2)
        analyzer = StrategyCorrelationAnalyzer()
        result = analyzer.analyze([s1, s2])

        matrix = result.correlation_matrix
        assert matrix.pearson[0][1] == matrix.pearson[1][0]
        assert matrix.spearman[0][1] == matrix.spearman[1][0]
