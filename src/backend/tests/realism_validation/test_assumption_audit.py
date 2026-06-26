from datetime import datetime, timezone

from app.execution.execution_report import ExecutionReport, ExecutionQuality
from app.portfolio.portfolio_engine import (
    PortfolioReport, PortfolioComposition, PortfolioMetrics,
)
from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.stress_tester import StressTestResult, StressScenario
from app.realism_validation.assumption_audit import AssumptionAuditor, AssumptionAuditReport


def _make_execution_report(
    fill_rate=0.85, avg_slippage=5.0, max_slippage=15.0,
    liquidity_score=0.7, total_cost=500.0, total_notional=500_000.0,
    partial_ratio=0.1,
):
    return ExecutionReport(
        generated_at=datetime.now(timezone.utc),
        total_orders=10,
        filled_orders=7,
        partially_filled=2,
        unfilled_orders=1,
        total_requested_notional=total_notional,
        total_executed_notional=total_notional * fill_rate,
        fill_rate=fill_rate,
        quality=ExecutionQuality(
            fill_rate=fill_rate,
            partial_fill_ratio=partial_ratio,
            avg_slippage_bps=avg_slippage,
            max_slippage_bps=max_slippage,
            total_slippage_cost=total_cost,
            avg_latency_ms=30.0,
            max_latency_ms=80.0,
            liquidity_score=liquidity_score,
            overall_quality_score=0.65,
        ),
        warnings=[],
        summary="",
    )


def _make_portfolio_report(active_strategies=3, div_ratio=1.5):
    return PortfolioReport(
        composition=PortfolioComposition(),
        metrics=PortfolioMetrics(
            expected_sharpe=1.2,
            expected_volatility=0.15,
            diversification_ratio=div_ratio,
            max_drawdown_estimate=-0.12,
            stability_score=0.65,
        ),
        assessment="",
    )


def _make_perf_report(
    total_return=0.15, annualized_return=0.12, sharpe=1.2,
    max_drawdown=-0.15, win_rate=0.55, daily_vol=0.01,
    calmar=0.8, total_days=252, drawdown_duration=20,
):
    return StrategyPerformanceReport(
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        max_drawdown_duration=drawdown_duration,
        win_rate=win_rate,
        avg_daily_return=0.0005,
        daily_volatility=daily_vol,
        calmar_ratio=calmar,
        total_days=total_days,
        avg_leverage=1.0,
        positive_days=int(total_days * win_rate),
        negative_days=int(total_days * (1 - win_rate)),
        drawdown_events=[],
    )


def _make_stress_result(scenario=StressScenario.FLASH_CRASH, survived=True, total_return=-0.05):
    return StressTestResult(
        scenario=scenario,
        description=f"{scenario.value} test",
        total_return=total_return,
        annualized_return=-0.10,
        sharpe_ratio=-0.5,
        max_drawdown=-0.12,
        win_rate=0.35,
        calmar_ratio=-0.8,
        total_days=252,
        return_delta_vs_baseline=0.0,
        sharpe_delta_vs_baseline=0.0,
        max_drawdown_delta_vs_baseline=0.0,
        survived=survived,
    )


class TestAssumptionAuditor:

    def test_normal_scenario_scores_high(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report()
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report()]
        stress = [_make_stress_result() for _ in range(5)]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        assert isinstance(report, AssumptionAuditReport)
        assert report.overall_realism >= 0.6
        assert len(report.assumptions) == 11
        assert report.assumptions[0].score > 0

    def test_unrealistic_fill_rate_detected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report(fill_rate=0.995)
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report()]
        stress = [_make_stress_result()]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        fill_assumption = report.assumptions[0]
        assert not fill_assumption.is_realistic
        assert "过高" in fill_assumption.details

    def test_unrealistic_sharpe_detected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report()
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report(sharpe=5.5)]
        stress = [_make_stress_result()]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        sharpe_assumptions = [a for a in report.assumptions if "夏普" in a.name]
        assert len(sharpe_assumptions) > 0
        assert not sharpe_assumptions[0].is_realistic

    def test_zero_slippage_with_fills_detected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report(avg_slippage=0.0, max_slippage=0.0, fill_rate=0.80)
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report()]
        stress = [_make_stress_result()]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        slippage_assumptions = [a for a in report.assumptions if "滑点" in a.name]
        assert len(slippage_assumptions) > 0
        assert not slippage_assumptions[0].is_realistic

    def test_all_stress_survived_detected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report()
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report()]
        stress = [_make_stress_result(survived=True) for _ in range(10)]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        stress_assumptions = [a for a in report.assumptions if "压力" in a.name]
        assert len(stress_assumptions) > 0
        assert not stress_assumptions[0].is_realistic

    def test_critical_issues_collected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report(fill_rate=0.0, avg_slippage=0.0, max_slippage=0.0)
        portfolio = PortfolioReport()
        perf = []
        stress = []

        report = auditor.audit(exec_report, portfolio, perf, stress)

        assert report.has_critical_issues
        assert report.unrealistic_count > 0

    def test_deterministic_with_seed(self):
        aud1 = AssumptionAuditor(seed=123)
        aud2 = AssumptionAuditor(seed=123)
        exec_report = _make_execution_report()
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report()]
        stress = [_make_stress_result() for _ in range(5)]

        r1 = aud1.audit(exec_report, portfolio, perf, stress)
        r2 = aud2.audit(exec_report, portfolio, perf, stress)

        assert r1.overall_realism == r2.overall_realism
        assert r1.unrealistic_count == r2.unrealistic_count

    def test_extreme_annual_return_detected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report()
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report(annualized_return=2.0)]
        stress = [_make_stress_result()]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        return_assumptions = [a for a in report.assumptions if "收益率" in a.name]
        assert len(return_assumptions) > 0
        assert not return_assumptions[0].is_realistic

    def test_drawdown_consistency_issues_detected(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report()
        portfolio = _make_portfolio_report()
        perf = [_make_perf_report(max_drawdown=-0.60, sharpe=2.5, win_rate=0.65)]
        stress = [_make_stress_result()]

        report = auditor.audit(exec_report, portfolio, perf, stress)

        dd_assumptions = [a for a in report.assumptions if "回撤" in a.name]
        assert len(dd_assumptions) > 0
        assert not dd_assumptions[0].is_realistic

    def test_empty_inputs_handled(self):
        auditor = AssumptionAuditor(seed=42)
        exec_report = _make_execution_report(fill_rate=0.0, avg_slippage=0.0, max_slippage=0.0)
        portfolio = PortfolioReport()
        perf: list = []
        stress: list = []

        report = auditor.audit(exec_report, portfolio, perf, stress)
        assert isinstance(report, AssumptionAuditReport)
        assert report.overall_realism < 0.5
