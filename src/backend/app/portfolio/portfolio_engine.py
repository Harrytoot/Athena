import math
from dataclasses import dataclass, field

from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy.portfolio_builder import PortfolioHistory
from app.strategy_robustness.robustness_report import RobustnessReport
from app.strategy_validation.performance_report import StrategyValidationReport

from app.portfolio.weight_optimizer import WeightResult, WeightOptimizer
from app.portfolio.risk_budgeting import RiskBudgetResult, RiskBudgeting, RiskConstraint
from app.portfolio.allocator import AllocationResult, CapitalAllocation, CapitalAllocator
from app.portfolio.rebalancer import RebalanceResult, Rebalancer

TRADING_DAYS = 252.0


@dataclass
class StrategyInput:
    strategy_id: str
    performance: StrategyPerformanceReport
    robustness: RobustnessReport
    validation: StrategyValidationReport | None = None
    history: PortfolioHistory | None = None


@dataclass
class PortfolioComposition:
    allocations: list[CapitalAllocation] = field(default_factory=list)
    weight_result: WeightResult = field(default_factory=WeightResult)
    risk_budget_result: RiskBudgetResult = field(default_factory=RiskBudgetResult)

    @property
    def total_weight(self) -> float:
        return sum(a.weight for a in self.allocations)

    @property
    def active_strategies(self) -> int:
        return len([a for a in self.allocations if a.weight > 0])


@dataclass
class PortfolioMetrics:
    expected_return: float = 0.0
    expected_volatility: float = 0.0
    expected_sharpe: float = 0.0
    portfolio_beta: float = 1.0
    diversification_ratio: float = 0.0
    risk_concentration: float = 0.0
    max_drawdown_estimate: float = 0.0
    calmar_estimate: float = 0.0
    stability_score: float = 0.0


@dataclass
class PortfolioReport:
    composition: PortfolioComposition = field(default_factory=PortfolioComposition)
    metrics: PortfolioMetrics = field(default_factory=PortfolioMetrics)
    rebalance: RebalanceResult | None = None
    assessment: str = ""
    risk_flags: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return len(self.composition.allocations) > 0 and self.composition.total_weight > 0


class PortfolioEngine:

    def __init__(
        self,
        total_capital: float = 1_000_000.0,
        max_strategy_weight: float = 0.50,
        min_strategy_weight: float = 0.05,
        risk_aversion: float = 1.0,
        risk_constraint: RiskConstraint | None = None,
        cash_reserve_pct: float = 0.0,
        drift_threshold: float = 0.05,
    ):
        self.total_capital = total_capital
        self.weight_optimizer = WeightOptimizer(
            max_weight=max_strategy_weight,
            min_weight=min_strategy_weight,
            risk_aversion=risk_aversion,
        )
        self.risk_budgeting = RiskBudgeting(constraint=risk_constraint)
        self.allocator = CapitalAllocator(
            total_capital=total_capital,
            cash_reserve_pct=cash_reserve_pct,
        )
        self.rebalancer = Rebalancer(drift_threshold=drift_threshold)

    def construct(
        self,
        strategies: list[StrategyInput],
        regime_multipliers: dict[str, float] | None = None,
        correlation_matrix: dict[str, dict[str, float]] | None = None,
    ) -> PortfolioReport:
        if not strategies:
            return PortfolioReport()

        perf_data = [
            (s.strategy_id, s.performance, s.robustness)
            for s in strategies
        ]

        volatility_map = {s.strategy_id: s.performance.daily_volatility for s in strategies}

        weight_result = self.weight_optimizer.optimize(perf_data, regime_multipliers)

        risk_budget_result = self.risk_budgeting.compute_risk_budgets(
            weight_result, volatility_map, correlation_matrix
        )

        allocation_result = self.allocator.allocate(weight_result, risk_budget_result)

        composition = PortfolioComposition(
            allocations=allocation_result.allocations,
            weight_result=weight_result,
            risk_budget_result=risk_budget_result,
        )

        metrics = self._compute_metrics(composition, strategies, correlation_matrix)

        risk_flags = self._check_risk_flags(composition, metrics)

        assessment = self._assess_portfolio(composition, metrics)

        return PortfolioReport(
            composition=composition,
            metrics=metrics,
            assessment=assessment,
            risk_flags=risk_flags,
        )

    def rebalance(
        self,
        current_allocations: list[CapitalAllocation],
        strategies: list[StrategyInput],
        regime_multipliers: dict[str, float] | None = None,
        correlation_matrix: dict[str, dict[str, float]] | None = None,
    ) -> PortfolioReport:
        report = self.construct(strategies, regime_multipliers, correlation_matrix)

        rebalance_result = self.rebalancer.check(
            current_allocations, report.composition.weight_result
        )

        report.rebalance = rebalance_result

        if rebalance_result.triggered:
            report.assessment = f"Rebalance triggered: {rebalance_result.trigger_reason} | {report.assessment}"

        return report

    def _compute_metrics(
        self,
        composition: PortfolioComposition,
        strategies: list[StrategyInput],
        correlation_matrix: dict[str, dict[str, float]] | None = None,
    ) -> PortfolioMetrics:
        if not strategies:
            return PortfolioMetrics()

        norm_weights = composition.weight_result.normalized_weights
        ids = [s.strategy_id for s in strategies]
        n = len(ids)

        if correlation_matrix is None:
            correlation_matrix = {
                id_i: {id_j: 1.0 if i == j else 0.3 for j, id_j in enumerate(ids)}
                for i, id_i in enumerate(ids)
            }

        returns = [s.performance.annualized_return for s in strategies]
        volatilities = [s.performance.daily_volatility * math.sqrt(TRADING_DAYS) for s in strategies]

        expected_return = sum(norm_weights[i] * returns[i] for i in range(n))

        portfolio_var = 0.0
        for i in range(n):
            for j in range(n):
                rho = correlation_matrix.get(ids[i], {}).get(ids[j], 0.3 if i != j else 1.0)
                portfolio_var += norm_weights[i] * norm_weights[j] * volatilities[i] * volatilities[j] * rho
        expected_vol = math.sqrt(max(0.0, portfolio_var))

        expected_sharpe = expected_return / expected_vol if expected_vol > 0 else 0.0

        weighted_vol = sum(norm_weights[i] * volatilities[i] for i in range(n))
        diversification_ratio = weighted_vol / expected_vol if expected_vol > 0 else 1.0

        max_dd_components = [s.performance.max_drawdown for s in strategies]
        weights_only = [a.weight for a in composition.allocations]
        max_dd_estimate = sum(w * abs(dd) for w, dd in zip(weights_only, max_dd_components) if dd < 0)
        max_dd_estimate = -max_dd_estimate

        calmar_estimate = expected_return / abs(max_dd_estimate) if max_dd_estimate != 0 else 0.0

        stability_scores = [s.robustness.overall_stability_score for s in strategies]
        stability_score = sum(norm_weights[i] * stability_scores[i] for i in range(n))

        risk_conc = composition.risk_budget_result.risk_concentration
        if risk_conc == 0 and composition.risk_budget_result.budgets:
            ratios = [b.risk_ratio for b in composition.risk_budget_result.budgets]
            risk_conc = sum(r ** 2 for r in ratios)

        return PortfolioMetrics(
            expected_return=round(expected_return, 6),
            expected_volatility=round(expected_vol, 6),
            expected_sharpe=round(expected_sharpe, 6),
            diversification_ratio=round(diversification_ratio, 6),
            risk_concentration=round(risk_conc, 6),
            max_drawdown_estimate=round(max_dd_estimate, 6),
            calmar_estimate=round(calmar_estimate, 6),
            stability_score=round(stability_score, 6),
        )

    def _check_risk_flags(
        self,
        composition: PortfolioComposition,
        metrics: PortfolioMetrics,
    ) -> list[str]:
        flags: list[str] = []

        if metrics.expected_volatility > 0.30:
            flags.append("High portfolio volatility (>30%)")

        if metrics.expected_sharpe < 0.0:
            flags.append("Negative expected Sharpe ratio")

        if metrics.risk_concentration > 0.5:
            flags.append("High risk concentration")

        if metrics.max_drawdown_estimate < -0.20:
            flags.append("Estimated max drawdown exceeds 20%")

        if composition.active_strategies < 2:
            flags.append("Insufficient strategy diversification")

        if composition.weight_result.total_weight < 0.9:
            flags.append("Total weight below 90% — unallocated capital")

        for sw in composition.weight_result.weights:
            if sw.capped:
                flags.append(f"{sw.strategy_id} capped: {sw.cap_reason}")

        return flags

    def _assess_portfolio(
        self,
        composition: PortfolioComposition,
        metrics: PortfolioMetrics,
    ) -> str:
        parts: list[str] = []

        if metrics.expected_sharpe >= 1.5:
            parts.append("组合质量: 优秀")
        elif metrics.expected_sharpe >= 1.0:
            parts.append("组合质量: 良好")
        elif metrics.expected_sharpe >= 0.5:
            parts.append("组合质量: 一般")
        else:
            parts.append("组合质量: 较低")

        if metrics.diversification_ratio >= 1.5:
            parts.append("分散化: 高")
        elif metrics.diversification_ratio >= 1.2:
            parts.append("分散化: 中")
        else:
            parts.append("分散化: 低")

        if composition.active_strategies >= 5:
            parts.append(f"策略数: {composition.active_strategies} (充足)")
        elif composition.active_strategies >= 3:
            parts.append(f"策略数: {composition.active_strategies} (适中)")
        else:
            parts.append(f"策略数: {composition.active_strategies} (偏少)")

        if metrics.stability_score >= 0.7:
            parts.append("稳定性: 高")
        elif metrics.stability_score >= 0.4:
            parts.append("稳定性: 中")
        else:
            parts.append("稳定性: 低")

        return " | ".join(parts)
