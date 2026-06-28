import pytest

from app.decision_transparency.decision_report_builder import DecisionReportBuilder, DecisionReport
from app.domain.market.market_score import MarketScore


class TestDecisionReportBuilder:

    def test_build_basic_report(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=75.0, liquidity=65.0, breadth=60.0, volatility=55.0, sentiment=50.0)

        report = builder.build(score)

        assert len(report.report_id) > 0
        assert report.signal_explanation.total_score == score.total
        assert len(report.factor_attribution.items) == 5
        assert len(report.scenario_results) > 0
        assert report.decision_trace is not None
        assert report.risk_explanation is None
        assert len(report.formatted_report) > 0

    def test_build_with_risk_data(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=70.0, liquidity=60.0, breadth=55.0, volatility=50.0, sentiment=45.0)
        daily_returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015, 0.01, -0.005, 0.0]
        drawdown_data = {
            "max_drawdown": -0.15,
            "avg_drawdown": -0.05,
            "drawdown_count": 3,
            "avg_duration_days": 10.0,
            "ulcer_index": 0.08,
        }
        correlation_data = {
            "positions_count": 5,
            "avg_pairwise_corr": 0.30,
        }

        report = builder.build(
            score,
            daily_returns=daily_returns,
            drawdown_data=drawdown_data,
            correlation_data=correlation_data,
        )

        assert report.risk_explanation is not None
        assert report.risk_explanation.drawdown.risk_level in ("HIGH", "MODERATE", "LOW")
        assert report.risk_explanation.volatility.risk_level in ("HIGH", "MODERATE", "LOW")
        assert report.risk_explanation.correlation.risk_level in ("HIGH", "MODERATE", "LOW")
        assert "风险评估" in report.formatted_report

    def test_build_with_user_action(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=60.0, liquidity=55.0, breadth=50.0, volatility=45.0, sentiment=40.0)

        report = builder.build(score, user_action="APPROVE", user_reason="信号符合预期")

        assert report.user_action == "APPROVE"
        assert "APPROVE" in report.formatted_report
        assert "信号符合预期" in report.formatted_report

    def test_build_without_scenarios(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=50.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)

        report = builder.build(score, include_scenarios=False)

        assert len(report.scenario_results) == 0

    def test_build_without_trace(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=50.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)

        report = builder.build(score, include_trace=False)

        assert report.decision_trace is None

    def test_report_has_all_sections(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=80.0, liquidity=75.0, breadth=70.0, volatility=65.0, sentiment=60.0)
        daily_returns = [0.01, 0.02, -0.01, 0.005, 0.015]
        drawdown_data = {
            "max_drawdown": -0.10,
            "avg_drawdown": -0.03,
            "drawdown_count": 2,
            "avg_duration_days": 5.0,
            "ulcer_index": 0.05,
        }
        correlation_data = {
            "positions_count": 8,
            "avg_pairwise_corr": 0.20,
        }

        report = builder.build(
            score,
            daily_returns=daily_returns,
            drawdown_data=drawdown_data,
            correlation_data=correlation_data,
        )

        sections = [
            "信号解释",
            "因子归因",
            "风险评估",
            "情景模拟",
            "决策追溯",
            "用户决策",
        ]
        for section in sections:
            assert section in report.formatted_report, f"Missing section: {section}"

    def test_formatted_report_is_structured(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=70.0, liquidity=65.0, breadth=60.0, volatility=55.0, sentiment=50.0)

        report = builder.build(score)

        assert report.formatted_report.startswith("=")
        assert "决策透明度报告" in report.formatted_report
        assert report.formatted_report.endswith("=")

    def test_strong_bull_overall_assessment(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=90.0, liquidity=85.0, breadth=80.0, volatility=75.0, sentiment=70.0)

        report = builder.build(score)

        assert len(report.overall_assessment) > 0
        assert "Bull" in report.overall_assessment or "看多" in report.overall_assessment

    def test_report_data_integrity(self):
        builder = DecisionReportBuilder()
        score = MarketScore(trend=65.0, liquidity=60.0, breadth=55.0, volatility=50.0, sentiment=45.0)
        daily_returns = [0.005, -0.008, 0.012, -0.003, 0.007]
        drawdown_data = {
            "max_drawdown": -0.12,
            "avg_drawdown": -0.04,
            "drawdown_count": 3,
            "avg_duration_days": 8.0,
            "ulcer_index": 0.06,
        }
        correlation_data = {
            "positions_count": 6,
            "avg_pairwise_corr": 0.35,
        }

        report = builder.build(
            score,
            daily_returns=daily_returns,
            drawdown_data=drawdown_data,
            correlation_data=correlation_data,
        )

        assert report.signal_explanation.total_score == score.total
        assert report.factor_attribution.total_score == score.total
        assert report.risk_explanation.drawdown.max_drawdown_pct == pytest.approx(-12.0)
        assert report.risk_explanation.correlation.avg_pairwise_correlation == pytest.approx(0.35)
