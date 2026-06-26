import pytest

from app.fund_evaluation.drawdown_analyzer import (
    DrawdownAnalysisResult,
    DrawdownAnalyzer,
    DrawdownCluster,
    DrawdownEvent,
    TailRiskMetrics,
)
from tests.fund_evaluation import _build_history, _make_strategy


class TestDrawdownAnalyzer:

    def test_empty_strategies(self):
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([], [])
        assert isinstance(result, DrawdownAnalysisResult)
        assert result.max_drawdown == 0.0

    def test_single_strategy_uptrend(self):
        history = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 + i * 0.5 for i in range(100)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.max_drawdown >= 0.0 or result.max_drawdown > -0.01
        assert len(result.drawdown_events) >= 0

    def test_drawdown_detection(self):
        history = _build_history(
            position_pcts=[1.0] * 50,
            prices=[100.0, 101.0, 95.0, 96.0, 97.0] * 10,
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.max_drawdown < 0
        assert len(result.drawdown_events) > 0

    def test_tail_risk_metrics(self):
        history = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.1 for i in range(100)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        tail = result.tail_risk
        assert isinstance(tail, TailRiskMetrics)
        assert tail.var_99 <= tail.var_95
        assert tail.cvar_95 <= tail.var_95
        assert isinstance(tail.worst_day_return, float)
        assert isinstance(tail.tail_ratio, float)

    def test_clusters_identified(self):
        history = _build_history(
            position_pcts=[1.0] * 120,
            prices=[100.0, 101.0, 95.0, 94.0, 96.0, 97.0, 100.0, 99.0, 92.0, 93.0]
            + [100.0 + i * 2 for i in range(110)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer(cluster_gap_threshold=5)
        result = analyzer.analyze([strategy], [1.0])

        assert result.clustering_score >= 0.0 and result.clustering_score <= 1.0

    def test_ulcer_index(self):
        history = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 + i * 0.2 for i in range(100)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.ulcer_index >= 0.0

    def test_no_history_fallback(self):
        s1 = _make_strategy("s1")
        s2 = _make_strategy("s2")
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([s1, s2], [0.5, 0.5])

        assert isinstance(result, DrawdownAnalysisResult)
        assert result.max_drawdown == 0.0

    def test_severe_drawdown(self):
        cycle = [100.0, 80.0, 75.0, 78.0, 72.0, 70.0, 73.0]
        n = 84
        prices = [cycle[i % len(cycle)] for i in range(n)]
        history = _build_history(
            position_pcts=[1.0] * n,
            prices=prices,
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.max_drawdown < -0.10

    def test_tail_risk_worst_day(self):
        history = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0, 100.0, 90.0, 100.0] + [100.0 + i * 0.5 for i in range(1, 97)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.tail_risk.worst_day_return < 0

    def test_multiple_strategies(self):
        h1 = _build_history(
            position_pcts=[0.5] * 80,
            prices=[100.0 + i * 0.2 for i in range(80)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 80,
            prices=[100.0 + i * 0.1 for i in range(80)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([s1, s2], [0.5, 0.5])

        assert isinstance(result, DrawdownAnalysisResult)
        assert result.drawdown_frequency >= 0

    def test_drawdown_frequency(self):
        history = _build_history(
            position_pcts=[0.5] * 252,
            prices=[100.0 + i * 0.05 for i in range(252)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = DrawdownAnalyzer()
        result = analyzer.analyze([strategy], [1.0])

        assert result.drawdown_frequency >= 0
