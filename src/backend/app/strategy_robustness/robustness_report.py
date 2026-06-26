import math
from dataclasses import dataclass, field

from app.strategy.portfolio_builder import PortfolioHistory
from app.strategy.pnl_analyzer import PnLAnalyzer, StrategyPerformanceReport
from app.strategy.risk_manager import RiskResult

from app.strategy_robustness.transaction_cost import (
    CostEvent,
    TransactionCostConfig,
    TransactionCostSimulator,
)
from app.strategy_robustness.slippage_model import (
    SlippageConfig,
    SlippageEstimate,
    SlippageModel,
)
from app.strategy_robustness.market_impact import (
    ImpactConfig,
    ImpactEstimate,
    MarketImpactModel,
)
from app.strategy_robustness.stress_tester import (
    StressScenario,
    StressTestResult,
    StressTester,
)


@dataclass
class CostAdjustedMetrics:
    raw_sharpe: float
    cost_adjusted_sharpe: float
    total_transaction_costs: float
    cost_ratio: float
    total_slippage: float
    slippage_ratio: float
    total_market_impact: float
    impact_ratio: float
    total_friction: float
    friction_ratio: float

    @property
    def sharpe_erosion(self) -> float:
        return round(self.raw_sharpe - self.cost_adjusted_sharpe, 6)


@dataclass
class TurnoverImpact:
    avg_daily_turnover: float
    total_turnover: float
    turnover_count: int
    cost_per_turnover_pct: float
    slippage_sensitivity: dict[str, float]
    impact_sensitivity: dict[str, float]


@dataclass
class StabilityMetrics:
    perturbation_stability: float
    perturbation_mean_sharpe: float
    perturbation_sharpe_std: float
    stress_scenarios_passed: int
    stress_scenarios_total: int
    stress_resilience_score: float


@dataclass
class RobustnessReport:
    cost_metrics: CostAdjustedMetrics = field(default_factory=lambda: CostAdjustedMetrics(
        raw_sharpe=0.0,
        cost_adjusted_sharpe=0.0,
        total_transaction_costs=0.0,
        cost_ratio=0.0,
        total_slippage=0.0,
        slippage_ratio=0.0,
        total_market_impact=0.0,
        impact_ratio=0.0,
        total_friction=0.0,
        friction_ratio=0.0,
    ))
    turnover_impact: TurnoverImpact = field(default_factory=lambda: TurnoverImpact(
        avg_daily_turnover=0.0,
        total_turnover=0.0,
        turnover_count=0,
        cost_per_turnover_pct=0.0,
        slippage_sensitivity={},
        impact_sensitivity={},
    ))
    stability: StabilityMetrics = field(default_factory=lambda: StabilityMetrics(
        perturbation_stability=0.0,
        perturbation_mean_sharpe=0.0,
        perturbation_sharpe_std=0.0,
        stress_scenarios_passed=0,
        stress_scenarios_total=0,
        stress_resilience_score=0.0,
    ))
    stress_results: list[StressTestResult] = field(default_factory=list)
    overall_stability_score: float = 0.0
    overall_assessment: str = ""


class RobustnessReportGenerator:

    def __init__(
        self,
        cost_config: TransactionCostConfig | None = None,
        slippage_config: SlippageConfig | None = None,
        impact_config: ImpactConfig | None = None,
        risk_free_rate: float = 0.02,
    ):
        self.cost_simulator = TransactionCostSimulator(config=cost_config)
        self.slippage_model = SlippageModel(config=slippage_config)
        self.impact_model = MarketImpactModel(config=impact_config)
        self.stress_tester = StressTester(risk_free_rate=risk_free_rate)
        self.analyzer = PnLAnalyzer(risk_free_rate=risk_free_rate)
        self.risk_free_rate = risk_free_rate

    def generate(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
        perf_report: StrategyPerformanceReport | None = None,
    ) -> RobustnessReport:
        if perf_report is None:
            perf_report = self.analyzer.analyze(history)

        cost_events = self.cost_simulator.simulate(history, risk_result)
        slippage_estimates = self.slippage_model.estimate(history, risk_result)
        impact_estimates = self.impact_model.estimate(history, risk_result)

        total_costs = self.cost_simulator.compute_total_costs(cost_events)
        total_slippage = self.slippage_model.total_slippage_impact(slippage_estimates)
        total_impact = self.impact_model.total_impact(impact_estimates)

        cost_adjusted_sharpe = self.cost_simulator.compute_cost_adjusted_sharpe(
            history, cost_events, self.risk_free_rate
        )

        cost_metrics = CostAdjustedMetrics(
            raw_sharpe=perf_report.sharpe_ratio,
            cost_adjusted_sharpe=cost_adjusted_sharpe,
            total_transaction_costs=total_costs,
            cost_ratio=self.cost_simulator.cost_ratio(history, cost_events),
            total_slippage=total_slippage,
            slippage_ratio=round(total_slippage / abs(history.initial_nav), 8)
            if history.initial_nav != 0
            else 0.0,
            total_market_impact=total_impact,
            impact_ratio=self.impact_model.impact_ratio(history, impact_estimates),
            total_friction=round(total_costs + total_slippage + total_impact, 4),
            friction_ratio=round(
                (total_costs + total_slippage + total_impact) / abs(history.initial_nav), 8
            )
            if history.initial_nav != 0
            else 0.0,
        )

        turnover_impact = self._compute_turnover_impact(
            history, risk_result, cost_events, slippage_estimates, impact_estimates
        )

        stress_results = self.stress_tester.run(history, risk_result)
        perturbation = self.stress_tester.perturbation_stability(history)

        passed = sum(1 for r in stress_results if r.survived)
        total_stress = len(stress_results)

        stability = StabilityMetrics(
            perturbation_stability=perturbation["stability"],
            perturbation_mean_sharpe=perturbation["mean_sharpe"],
            perturbation_sharpe_std=perturbation["sharpe_std"],
            stress_scenarios_passed=passed,
            stress_scenarios_total=total_stress,
            stress_resilience_score=round(passed / total_stress, 4) if total_stress > 0 else 0.0,
        )

        overall_score = self._compute_overall_score(
            perf_report, cost_metrics, stability
        )

        assessment = self._assess_overall(perf_report, cost_metrics, stability, overall_score)

        return RobustnessReport(
            cost_metrics=cost_metrics,
            turnover_impact=turnover_impact,
            stability=stability,
            stress_results=stress_results,
            overall_stability_score=overall_score,
            overall_assessment=assessment,
        )

    def _compute_turnover_impact(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
        cost_events: list[CostEvent],
        slippage_estimates: list[SlippageEstimate],
        impact_estimates: list[ImpactEstimate],
    ) -> TurnoverImpact:
        positions = risk_result.positions
        n = len(positions)
        if n < 2:
            return TurnoverImpact(
                avg_daily_turnover=0.0,
                total_turnover=0.0,
                turnover_count=0,
                cost_per_turnover_pct=0.0,
                slippage_sensitivity={},
                impact_sensitivity={},
            )

        turnovers: list[float] = []
        for i in range(1, n):
            t = abs(positions[i].adjusted_position_pct - positions[i - 1].adjusted_position_pct)
            turnovers.append(t)

        total = sum(turnovers)
        avg = total / len(turnovers) if turnovers else 0.0

        total_cost_amount = sum(e.total_cost for e in cost_events)
        cost_per_turnover = 0.0
        if total > 1e-10 and history.initial_nav > 0:
            cost_per_turnover = total_cost_amount / (total * history.initial_nav)

        slippage_sens = self.slippage_model.sensitivity_analysis(history, risk_result)
        impact_sens = self.impact_model.sensitivity_analysis(history, risk_result)

        return TurnoverImpact(
            avg_daily_turnover=round(avg, 6),
            total_turnover=round(total, 6),
            turnover_count=len(turnovers),
            cost_per_turnover_pct=round(cost_per_turnover, 8),
            slippage_sensitivity=slippage_sens,
            impact_sensitivity=impact_sens,
        )

    def _compute_overall_score(
        self,
        perf_report: StrategyPerformanceReport,
        cost_metrics: CostAdjustedMetrics,
        stability: StabilityMetrics,
    ) -> float:
        scores: list[float] = []

        base_sharpe = perf_report.sharpe_ratio
        if base_sharpe != 0:
            cost_tolerance = max(0.0, min(1.0, cost_metrics.cost_adjusted_sharpe / base_sharpe))
        else:
            cost_tolerance = 0.5
        scores.append(cost_tolerance)

        friction_score = max(0.0, 1.0 - min(1.0, cost_metrics.friction_ratio * 100))
        scores.append(friction_score)

        scores.append(stability.perturbation_stability)

        scores.append(stability.stress_resilience_score)

        if cost_metrics.raw_sharpe > 0:
            positive_sharpe_bonus = 0.1
            scores.append(positive_sharpe_bonus)

        overall = sum(scores) / len(scores) if scores else 0.0
        return round(min(1.0, max(0.0, overall)), 4)

    def _assess_overall(
        self,
        perf_report: StrategyPerformanceReport,
        cost_metrics: CostAdjustedMetrics,
        stability: StabilityMetrics,
        overall_score: float,
    ) -> str:
        parts: list[str] = []

        if overall_score >= 0.8:
            parts.append("策略稳健性: 优秀")
        elif overall_score >= 0.6:
            parts.append("策略稳健性: 良好")
        elif overall_score >= 0.4:
            parts.append("策略稳健性: 一般")
        else:
            parts.append("策略稳健性: 较差")

        if cost_metrics.sharpe_erosion > 0.1:
            parts.append(f"成本侵蚀严重 (夏普衰减{cost_metrics.sharpe_erosion:.4f})")
        elif cost_metrics.sharpe_erosion > 0.05:
            parts.append(f"成本影响明显 (夏普衰减{cost_metrics.sharpe_erosion:.4f})")
        else:
            parts.append(f"成本影响可控 (夏普衰减{cost_metrics.sharpe_erosion:.4f})")

        if stability.perturbation_stability >= 0.8:
            parts.append("参数扰动稳定性: 高")
        elif stability.perturbation_stability >= 0.5:
            parts.append("参数扰动稳定性: 中")
        else:
            parts.append("参数扰动稳定性: 低")

        stress_label = (
            "高"
            if stability.stress_resilience_score >= 0.8
            else "中" if stability.stress_resilience_score >= 0.5
            else "低"
        )
        parts.append(
            f"压力测试通过率: {stability.stress_scenarios_passed}/{stability.stress_scenarios_total} ({stress_label})"
        )

        return " | ".join(parts)
