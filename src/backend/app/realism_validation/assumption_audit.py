import math
from dataclasses import dataclass, field

from app.execution.execution_report import ExecutionReport
from app.portfolio.portfolio_engine import PortfolioReport
from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.stress_tester import StressTestResult

MAX_REALISTIC_FILL_RATE = 0.98
MAX_REALISTIC_SHARPE = 4.0
MAX_REALISTIC_ANNUAL_RETURN = 1.5
MIN_REALISTIC_ANNUAL_RETURN = -0.5
MAX_REALISTIC_VOLATILITY = 0.80
MIN_REALISTIC_VOLATILITY = 0.02
MAX_REALISTIC_SLIPPAGE_BPS = 200.0
MAX_REALISTIC_WIN_RATE = 0.70
MIN_REALISTIC_WIN_RATE = 0.30
UNREALISTIC_CORRELATION_HIGH = 0.95
UNREALISTIC_CORRELATION_LOW = -0.80
MAX_DRAWDOWN_VIOLATION = -0.80
MAX_SLIPPAGE_NO_STRESS = 30.0


@dataclass
class AssumptionResult:
    name: str
    description: str
    is_realistic: bool
    score: float
    details: str


@dataclass
class AssumptionAuditReport:
    assumptions: list[AssumptionResult] = field(default_factory=list)
    unrealistic_count: int = 0
    overall_realism: float = 0.0
    critical_issues: list[str] = field(default_factory=list)
    assessment: str = ""

    @property
    def has_critical_issues(self) -> bool:
        return len(self.critical_issues) > 0


class AssumptionAuditor:

    def __init__(self, seed: int | None = None):
        self.seed = seed

    def audit(
        self,
        execution_report: ExecutionReport,
        portfolio_report: PortfolioReport,
        perf_reports: list[StrategyPerformanceReport],
        stress_results: list[StressTestResult],
    ) -> AssumptionAuditReport:
        assumptions: list[AssumptionResult] = []
        critical_issues: list[str] = []

        a = self._check_fill_rate(execution_report)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_slippage_plausibility(execution_report)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_liquidity_availability(execution_report)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_return_plausibility(perf_reports)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_sharpe_plausibility(perf_reports)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_volatility_plausibility(perf_reports)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_win_rate_plausibility(perf_reports)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_drawdown_consistency(perf_reports)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_portfolio_diversification(portfolio_report)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_stress_survival(stress_results)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        a = self._check_cost_realism(execution_report)
        assumptions.append(a)
        if not a.is_realistic and a.score < 0.4:
            critical_issues.append(a.name)

        unrealistic_count = sum(1 for a in assumptions if not a.is_realistic)
        scores = [a.score for a in assumptions]
        overall = round(sum(scores) / len(scores), 4) if scores else 0.0

        assessment = self._assess(overall, unrealistic_count, critical_issues)

        return AssumptionAuditReport(
            assumptions=assumptions,
            unrealistic_count=unrealistic_count,
            overall_realism=overall,
            critical_issues=critical_issues,
            assessment=assessment,
        )

    def _check_fill_rate(self, report: ExecutionReport) -> AssumptionResult:
        fr = report.fill_rate
        if fr <= 0:
            return AssumptionResult(
                name="订单成交率",
                description="检查订单成交率是否在合理范围",
                is_realistic=False,
                score=0.0,
                details=f"成交率为0，数据异常",
            )
        if fr > MAX_REALISTIC_FILL_RATE:
            return AssumptionResult(
                name="订单成交率",
                description="检查订单成交率是否在合理范围",
                is_realistic=False,
                score=0.3,
                details=f"成交率 {fr:.2%} 过高(>98%)，实际市场不可能每笔订单都完全成交",
            )
        if fr >= 0.95:
            return AssumptionResult(
                name="订单成交率",
                description="检查订单成交率是否在合理范围",
                is_realistic=True,
                score=0.85,
                details=f"成交率 {fr:.2%} 较高但在大型流动性标的下可接受",
            )
        if fr >= 0.70:
            return AssumptionResult(
                name="订单成交率",
                description="检查订单成交率是否在合理范围",
                is_realistic=True,
                score=1.0,
                details=f"成交率 {fr:.2%} 在现实交易范围内",
            )
        if fr >= 0.40:
            return AssumptionResult(
                name="订单成交率",
                description="检查订单成交率是否在合理范围",
                is_realistic=True,
                score=0.7,
                details=f"成交率 {fr:.2%} 偏低但未失实",
            )
        return AssumptionResult(
            name="订单成交率",
            description="检查订单成交率是否在合理范围",
            is_realistic=False,
            score=0.3,
            details=f"成交率 {fr:.2%} 过低，可能低估了流动性",
        )

    def _check_slippage_plausibility(self, report: ExecutionReport) -> AssumptionResult:
        avg_slip = report.quality.avg_slippage_bps
        max_slip = report.quality.max_slippage_bps
        if max_slip > MAX_REALISTIC_SLIPPAGE_BPS:
            return AssumptionResult(
                name="滑点真实性",
                description="检查滑点是否在正常市场范围内",
                is_realistic=False,
                score=0.2,
                details=f"最大滑点 {max_slip:.1f}bps 超出200bps，仅在极端行情出现",
            )
        if max_slip > MAX_SLIPPAGE_NO_STRESS:
            return AssumptionResult(
                name="滑点真实性",
                description="检查滑点是否在正常市场范围内",
                is_realistic=True,
                score=0.65,
                details=f"平均滑点 {avg_slip:.1f}bps, 最大 {max_slip:.1f}bps，处于较高但可接受范围",
            )
        if avg_slip == 0 and report.fill_rate > 0:
            return AssumptionResult(
                name="滑点真实性",
                description="检查滑点是否在正常市场范围内",
                is_realistic=False,
                score=0.4,
                details=f"有成交但滑点为0，真实市场中不可能零滑点执行",
            )
        return AssumptionResult(
            name="滑点真实性",
            description="检查滑点是否在正常市场范围内",
            is_realistic=True,
            score=1.0,
            details=f"平均滑点 {avg_slip:.1f}bps, 最大 {max_slip:.1f}bps，在合理范围内",
        )

    def _check_liquidity_availability(self, report: ExecutionReport) -> AssumptionResult:
        liq_score = report.quality.liquidity_score
        if liq_score >= 0.8:
            return AssumptionResult(
                name="流动性假设",
                description="检查流动性评分是否反映真实市场深度",
                is_realistic=True,
                score=0.9,
                details=f"流动性评分 {liq_score:.2f}，较高但大盘股可接受",
            )
        if liq_score >= 0.5:
            return AssumptionResult(
                name="流动性假设",
                description="检查流动性评分是否反映真实市场深度",
                is_realistic=True,
                score=1.0,
                details=f"流动性评分 {liq_score:.2f}，在正常范围内",
            )
        if liq_score >= 0.3:
            return AssumptionResult(
                name="流动性假设",
                description="检查流动性评分是否反映真实市场深度",
                is_realistic=True,
                score=0.7,
                details=f"流动性评分 {liq_score:.2f} 偏低，符合中低流动性标的特征",
            )
        return AssumptionResult(
            name="流动性假设",
            description="检查流动性评分是否反映真实市场深度",
            is_realistic=False,
            score=0.4,
            details=f"流动性评分 {liq_score:.2f} 过低，可能高估了流动性风险",
        )

    def _check_return_plausibility(
        self, perf_reports: list[StrategyPerformanceReport]
    ) -> AssumptionResult:
        if not perf_reports:
            return AssumptionResult(
                name="收益率合理性",
                description="检查年化收益率是否在现实范围内",
                is_realistic=False,
                score=0.0,
                details="无策略业绩数据",
            )
        annual_returns = [p.annualized_return for p in perf_reports]
        avg_return = sum(annual_returns) / len(annual_returns)
        max_ret = max(annual_returns)
        min_ret = min(annual_returns)

        violations: list[str] = []
        for p in perf_reports:
            if p.annualized_return > MAX_REALISTIC_ANNUAL_RETURN:
                violations.append(f"{p.annualized_return:.1%}")
        if max_ret > MAX_REALISTIC_ANNUAL_RETURN:
            return AssumptionResult(
                name="收益率合理性",
                description="检查年化收益率是否在现实范围内",
                is_realistic=False,
                score=0.2,
                details=f"存在年化收益>{MAX_REALISTIC_ANNUAL_RETURN:.0%}的策略: {', '.join(violations[:3])}。实际交易中维持如此高收益几无可能",
            )
        if min_ret < MIN_REALISTIC_ANNUAL_RETURN and len(perf_reports) == 1:
            return AssumptionResult(
                name="收益率合理性",
                description="检查年化收益率是否在现实范围内",
                is_realistic=True,
                score=0.8,
                details=f"年化收益 {min_ret:.1%} 极低，但单一策略可能表现不佳",
            )
        return AssumptionResult(
            name="收益率合理性",
            description="检查年化收益率是否在现实范围内",
            is_realistic=True,
            score=round(max(0.0, min(1.0, 1.0 - abs(avg_return) / MAX_REALISTIC_ANNUAL_RETURN)), 4),
            details=f"平均年化收益 {avg_return:.1%}，在合理范围内",
        )

    def _check_sharpe_plausibility(
        self, perf_reports: list[StrategyPerformanceReport]
    ) -> AssumptionResult:
        if not perf_reports:
            return AssumptionResult(
                name="夏普比率合理性",
                description="检查夏普比率是否在现实范围内",
                is_realistic=False,
                score=0.0,
                details="无策略业绩数据",
            )
        sharpes = [p.sharpe_ratio for p in perf_reports]
        max_sharpe = max(sharpes)
        avg_sharpe = sum(sharpes) / len(sharpes)

        if max_sharpe > MAX_REALISTIC_SHARPE:
            return AssumptionResult(
                name="夏普比率合理性",
                description="检查夏普比率是否在现实范围内",
                is_realistic=False,
                score=0.15,
                details=f"存在夏普比率 {max_sharpe:.2f} > {MAX_REALISTIC_SHARPE}，真实市场中几乎不可能持续，可能存在回测过拟合",
            )
        if max_sharpe > 3.0:
            return AssumptionResult(
                name="夏普比率合理性",
                description="检查夏普比率是否在现实范围内",
                is_realistic=False,
                score=0.4,
                details=f"最大夏普 {max_sharpe:.2f} 处于极端高位，建议检查数据挖掘偏差",
            )
        if max_sharpe > 2.5:
            return AssumptionResult(
                name="夏普比率合理性",
                description="检查夏普比率是否在现实范围内",
                is_realistic=True,
                score=0.7,
                details=f"最大夏普 {max_sharpe:.2f} 偏高但个别策略可能实现",
            )
        return AssumptionResult(
            name="夏普比率合理性",
            description="检查夏普比率是否在现实范围内",
            is_realistic=True,
            score=round(max(0.0, min(1.0, 1.0 - avg_sharpe / MAX_REALISTIC_SHARPE)), 4),
            details=f"平均夏普 {avg_sharpe:.2f}，在合理范围内",
        )

    def _check_volatility_plausibility(
        self, perf_reports: list[StrategyPerformanceReport]
    ) -> AssumptionResult:
        if not perf_reports:
            return AssumptionResult(
                name="波动率合理性",
                description="检查日波动率是否在现实范围内",
                is_realistic=False,
                score=0.0,
                details="无策略业绩数据",
            )
        vols = [p.daily_volatility for p in perf_reports]
        avg_vol = sum(vols) / len(vols)
        annual_vol = avg_vol * math.sqrt(252.0)

        if annual_vol > MAX_REALISTIC_VOLATILITY:
            return AssumptionResult(
                name="波动率合理性",
                description="检查日波动率是否在现实范围内",
                is_realistic=False,
                score=0.2,
                details=f"年化波动率 {annual_vol:.1%} > {MAX_REALISTIC_VOLATILITY:.0%}，极端异常",
            )
        if annual_vol < MIN_REALISTIC_VOLATILITY and avg_vol > 0:
            return AssumptionResult(
                name="波动率合理性",
                description="检查日波动率是否在现实范围内",
                is_realistic=False,
                score=0.4,
                details=f"年化波动率 {annual_vol:.1%} 极低，真实市场中不存在几乎无波动的策略",
            )
        return AssumptionResult(
            name="波动率合理性",
            description="检查日波动率是否在现实范围内",
            is_realistic=True,
            score=round(max(0.0, 1.0 - abs(annual_vol - 0.25) / 0.50), 4),
            details=f"年化波动率 {annual_vol:.1%}，在合理范围内",
        )

    def _check_win_rate_plausibility(
        self, perf_reports: list[StrategyPerformanceReport]
    ) -> AssumptionResult:
        if not perf_reports:
            return AssumptionResult(
                name="胜率合理性",
                description="检查胜率是否在现实范围内",
                is_realistic=False,
                score=0.0,
                details="无策略业绩数据",
            )
        win_rates = [p.win_rate for p in perf_reports]
        avg_wr = sum(win_rates) / len(win_rates)
        max_wr = max(win_rates)

        if max_wr > MAX_REALISTIC_WIN_RATE:
            return AssumptionResult(
                name="胜率合理性",
                description="检查胜率是否在现实范围内",
                is_realistic=False,
                score=0.3,
                details=f"存在胜率 {max_wr:.1%} > {MAX_REALISTIC_WIN_RATE:.0%}，高胜率通常伴随低盈亏比，需核实",
            )
        if avg_wr < MIN_REALISTIC_WIN_RATE:
            return AssumptionResult(
                name="胜率合理性",
                description="检查胜率是否在现实范围内",
                is_realistic=True,
                score=0.7,
                details=f"平均胜率 {avg_wr:.1%} 偏低，部分趋势跟踪策略属正常范围",
            )
        return AssumptionResult(
            name="胜率合理性",
            description="检查胜率是否在现实范围内",
            is_realistic=True,
            score=round(max(0.0, min(1.0, 1.0 - abs(avg_wr - 0.55) / 0.30)), 4),
            details=f"平均胜率 {avg_wr:.1%}，在合理范围内",
        )

    def _check_drawdown_consistency(
        self, perf_reports: list[StrategyPerformanceReport]
    ) -> AssumptionResult:
        if not perf_reports:
            return AssumptionResult(
                name="回撤一致性",
                description="检查最大回撤与其他指标是否一致",
                is_realistic=False,
                score=0.0,
                details="无策略业绩数据",
            )
        issues: list[str] = []
        for p in perf_reports:
            if p.max_drawdown < MAX_DRAWDOWN_VIOLATION:
                issues.append(f"回撤 {p.max_drawdown:.1%} 极端，策略可能应为失败状态")
            if p.max_drawdown > 0 and p.sharpe_ratio > 2.0:
                issues.append(f"夏普 {p.sharpe_ratio:.2f} 与回撤 {p.max_drawdown:.1%} 不符，可能低估尾部风险")
            if p.max_drawdown < -0.50 and p.win_rate > 0.60:
                issues.append(f"高胜率 {p.win_rate:.1%} 但深回撤 {p.max_drawdown:.1%}，盈亏比可能极不对称")

        if issues:
            return AssumptionResult(
                name="回撤一致性",
                description="检查最大回撤与其他指标是否一致",
                is_realistic=False,
                score=round(max(0.1, 1.0 - len(issues) * 0.2), 4),
                details="; ".join(issues[:3]),
            )
        return AssumptionResult(
            name="回撤一致性",
            description="检查最大回撤与其他指标是否一致",
            is_realistic=True,
            score=1.0,
            details="回撤与其他业绩指标一致",
        )

    def _check_portfolio_diversification(
        self, portfolio_report: PortfolioReport
    ) -> AssumptionResult:
        metrics = portfolio_report.metrics
        comp = portfolio_report.composition
        div_ratio = metrics.diversification_ratio

        if comp.active_strategies <= 1:
            return AssumptionResult(
                name="组合分散度",
                description="检查组合是否充分分散",
                is_realistic=False,
                score=0.3,
                details="仅1个策略，未体现组合分散特征",
            )
        if div_ratio >= 5.0:
            return AssumptionResult(
                name="组合分散度",
                description="检查组合是否充分分散",
                is_realistic=False,
                score=0.4,
                details=f"分散化比率 {div_ratio:.1f} 异常高，可能高估了策略间独立性",
            )
        if div_ratio < 1.0:
            return AssumptionResult(
                name="组合分散度",
                description="检查组合是否充分分散",
                is_realistic=False,
                score=0.5,
                details=f"分散化比率 {div_ratio:.2f} < 1，策略高度相关，分散化无效",
            )
        return AssumptionResult(
            name="组合分散度",
            description="检查组合是否充分分散",
            is_realistic=True,
            score=round(min(1.0, div_ratio / 2.0), 4),
            details=f"分散化比率 {div_ratio:.2f}，{comp.active_strategies}个策略",
        )

    def _check_stress_survival(
        self, stress_results: list[StressTestResult]
    ) -> AssumptionResult:
        if not stress_results:
            return AssumptionResult(
                name="压力生存能力",
                description="检查策略在压力场景下是否合理存活",
                is_realistic=False,
                score=0.0,
                details="无压力测试数据",
            )
        total = len(stress_results)
        survived = sum(1 for r in stress_results if r.survived)
        survival_rate = survived / total if total > 0 else 0.0

        if survival_rate == 1.0:
            return AssumptionResult(
                name="压力生存能力",
                description="检查策略在压力场景下是否合理存活",
                is_realistic=False,
                score=0.3,
                details="所有压力场景100%存活，真实市场中极端压力下应有场景失败，模型可能过于乐观",
            )
        if survival_rate >= 0.8:
            return AssumptionResult(
                name="压力生存能力",
                description="检查策略在压力场景下是否合理存活",
                is_realistic=True,
                score=0.85,
                details=f"{survived}/{total} ({survival_rate:.0%}) 场景存活，策略具备一定韧性",
            )
        if survival_rate >= 0.5:
            return AssumptionResult(
                name="压力生存能力",
                description="检查策略在压力场景下是否合理存活",
                is_realistic=True,
                score=1.0,
                details=f"{survived}/{total} ({survival_rate:.0%}) 场景存活，符合真实策略在压力下的表现",
            )
        return AssumptionResult(
            name="压力生存能力",
            description="检查策略在压力场景下是否合理存活",
            is_realistic=True,
            score=0.7,
            details=f"{survived}/{total} ({survival_rate:.0%}) 场景存活，压力下多数失败属正常",
        )

    def _check_cost_realism(self, report: ExecutionReport) -> AssumptionResult:
        total_cost = report.quality.total_slippage_cost
        total_notional = report.total_executed_notional
        if total_notional <= 0:
            return AssumptionResult(
                name="成本真实性",
                description="检查交易成本占名义本金的比重",
                is_realistic=True,
                score=0.5,
                details="无成交数据",
            )
        cost_ratio = total_cost / total_notional

        if cost_ratio > 0.05:
            return AssumptionResult(
                name="成本真实性",
                description="检查交易成本占名义本金的比重",
                is_realistic=False,
                score=0.3,
                details=f"成本占比 {cost_ratio:.2%} > 5%，成本模型可能过于悲观",
            )
        if cost_ratio < 0.0001 and total_notional > 0 and total_cost > 0:
            return AssumptionResult(
                name="成本真实性",
                description="检查交易成本占名义本金的比重",
                is_realistic=False,
                score=0.5,
                details=f"成本占比 {cost_ratio:.4%} 极低，可能低估了真实交易成本",
            )
        return AssumptionResult(
            name="成本真实性",
            description="检查交易成本占名义本金的比重",
            is_realistic=True,
            score=round(max(0.0, 1.0 - cost_ratio / 0.03), 4),
            details=f"成本占比 {cost_ratio:.2%}，在合理范围内",
        )

    def _assess(
        self, overall: float, unrealistic_count: int, critical: list[str]
    ) -> str:
        parts: list[str] = []
        if overall >= 0.8:
            parts.append("仿真真实度: 高")
        elif overall >= 0.6:
            parts.append("仿真真实度: 中")
        elif overall >= 0.4:
            parts.append("仿真真实度: 偏低")
        else:
            parts.append("仿真真实度: 低")

        parts.append(f"不实假设: {unrealistic_count}项")
        if critical:
            parts.append(f"严重问题: {len(critical)}项")

        return " | ".join(parts)
