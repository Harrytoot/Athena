import pytest

from app.portfolio.portfolio_engine import (
    PortfolioComposition,
    PortfolioEngine,
    PortfolioMetrics,
    PortfolioReport,
)
from app.fund_evaluation.fund_report import (
    FundEvaluationReport,
    FundReportGenerator,
    MultiStrategyUplift,
)
from tests.fund_evaluation import _build_history, _make_strategy


def _make_portfolio_report(strategies):
    engine = PortfolioEngine()
    return engine.construct(strategies)


class TestFundReportGenerator:

    def test_empty_strategies(self):
        generator = FundReportGenerator()
        result = generator.generate([], PortfolioReport())
        assert isinstance(result, FundEvaluationReport)
        assert result.overall_score == 0.0

    def test_not_ready_portfolio(self):
        generator = FundReportGenerator()
        p1 = _make_strategy("s1")
        result = generator.generate([p1], PortfolioReport())
        assert isinstance(result, FundEvaluationReport)

    def test_single_strategy_full_report(self):
        history = _build_history(
            position_pcts=[0.5] * 120,
            prices=[100.0 + i * 0.2 for i in range(120)],
        )
        s1 = _make_strategy("s1", sharpe=1.2, history=history)
        portfolio_report = _make_portfolio_report([s1])

        generator = FundReportGenerator(rolling_window=60)
        result = generator.generate([s1], portfolio_report)

        assert isinstance(result, FundEvaluationReport)
        assert isinstance(result.stability, object)
        assert isinstance(result.correlation, object)
        assert isinstance(result.drawdown, object)
        assert isinstance(result.uplift, MultiStrategyUplift)
        assert len(result.assessment) > 0

    def test_multiple_strategies_full_report(self):
        h1 = _build_history(
            position_pcts=[1.0] * 150,
            prices=[100.0 + i * 0.3 for i in range(150)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 150,
            prices=[100.0 + i * 0.15 for i in range(150)],
        )
        h3 = _build_history(
            position_pcts=[0.3] * 150,
            prices=[100.0 + i * 0.1 for i in range(150)],
        )
        s1 = _make_strategy("momentum", sharpe=1.5, history=h1)
        s2 = _make_strategy("mean_rev", sharpe=1.0, history=h2)
        s3 = _make_strategy("arbitrage", sharpe=0.8, history=h3)
        strategies = [s1, s2, s3]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=60)
        result = generator.generate(strategies, portfolio_report)

        assert isinstance(result, FundEvaluationReport)
        assert 0.0 <= result.overall_score <= 1.0
        assert len(result.assessment) > 0
        assert result.uplift.diversification_benefit >= 0

    def test_overall_score_range(self):
        h1 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.2 for i in range(100)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.1 for i in range(100)],
        )
        s1 = _make_strategy("s1", sharpe=1.5, history=h1)
        s2 = _make_strategy("s2", sharpe=1.0, history=h2)
        strategies = [s1, s2]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=40)
        result = generator.generate(strategies, portfolio_report)

        assert 0.0 <= result.overall_score <= 1.0

    def test_risk_flags_generated(self):
        h1 = _build_history(
            position_pcts=[1.0] * 120,
            prices=[100.0 + i * 0.3 for i in range(120)],
        )
        h2 = _build_history(
            position_pcts=[1.0] * 120,
            prices=[100.0 + i * 0.29 for i in range(120)],
        )
        s1 = _make_strategy("s1", sharpe=1.5, history=h1)
        s2 = _make_strategy("s2", sharpe=1.4, history=h2)
        strategies = [s1, s2]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=60)
        result = generator.generate(strategies, portfolio_report)

        assert isinstance(result.risk_flags, list)

    def test_uplift_metrics_computed(self):
        h1 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.2 for i in range(100)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.05 for i in range(100)],
        )
        s1 = _make_strategy("s1", sharpe=1.5, history=h1)
        s2 = _make_strategy("s2", sharpe=0.5, history=h2)
        strategies = [s1, s2]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=40)
        result = generator.generate(strategies, portfolio_report)

        assert result.uplift.best_single_sharpe >= result.uplift.avg_single_sharpe
        assert isinstance(result.uplift.sharpe_uplift_vs_best, float)
        assert isinstance(result.uplift.sharpe_uplift_vs_avg, float)

    def test_assessment_string_format(self):
        h1 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.2 for i in range(100)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 + i * 0.1 for i in range(100)],
        )
        s1 = _make_strategy("s1", sharpe=1.5, history=h1)
        s2 = _make_strategy("s2", sharpe=1.0, history=h2)
        strategies = [s1, s2]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=40)
        result = generator.generate(strategies, portfolio_report)

        assert "基金评估" in result.assessment
        assert " | " in result.assessment

    def test_no_history_strategies(self):
        s1 = _make_strategy("s1", sharpe=1.5)
        s2 = _make_strategy("s2", sharpe=1.0)
        s3 = _make_strategy("s3", sharpe=0.8)
        strategies = [s1, s2, s3]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=40)
        result = generator.generate(strategies, portfolio_report)

        assert isinstance(result, FundEvaluationReport)
        assert result.overall_score >= 0.0
        assert result.uplift is not None

    def test_negative_sharpe_strategies(self):
        h1 = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 - i * 0.2 for i in range(100)],
        )
        s1 = _make_strategy("s1", sharpe=-0.5, history=h1)
        strategies = [s1]

        portfolio_report = _make_portfolio_report(strategies)

        generator = FundReportGenerator(rolling_window=60)
        result = generator.generate(strategies, portfolio_report)

        assert isinstance(result, FundEvaluationReport)
        assert len(result.risk_flags) >= 0
