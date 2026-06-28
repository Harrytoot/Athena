from app.decision_semantics.schema import (
    DecisionSemantic,
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ExecutionSemantic,
)

from app.domain.market.market_score import MarketScore
from app.decision_transparency.factor_attribution import FactorAttribution, FactorAttributionItem
from app.decision_transparency.scenario_simulator import ScenarioResult
from app.decision_transparency.risk_explainer import RiskExplanation
from app.decision_transparency.signal_explainer import SignalExplanation
from app.execution.execution_report import ExecutionReport

FACTOR_LABELS: dict[str, str] = {
    "trend": "趋势强度",
    "liquidity": "市场流动性",
    "breadth": "市场宽度",
    "volatility": "波动率",
    "sentiment": "市场情绪",
}

SCENARIO_VULNERABILITY_HIGH = 20.0
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_MODERATE = "MODERATE"
RISK_LEVEL_LOW = "LOW"


class SemanticMapper:

    def map_factors(self, score: MarketScore, attribution: FactorAttribution) -> list[FactorSemantic]:
        name_to_item: dict[str, FactorAttributionItem] = {
            item.factor_name: item for item in attribution.items
        }
        factors = [
            ("trend", score.trend, 0.30),
            ("liquidity", score.liquidity, 0.25),
            ("breadth", score.breadth, 0.20),
            ("volatility", score.volatility, 0.15),
            ("sentiment", score.sentiment, 0.10),
        ]
        result: list[FactorSemantic] = []
        for name, value, weight in factors:
            item = name_to_item.get(name)
            result.append(FactorSemantic(
                name=name,
                label=FACTOR_LABELS.get(name, name),
                value=round(value, 2),
                weight=weight,
                contribution=round(value * weight, 2),
                is_bullish=value >= 50.0,
                assessment=item.interpretation if item else "",
            ))
        return result

    def map_signal(self, explanation: SignalExplanation) -> SignalSemantic:
        strength = abs(explanation.total_score - 50.0) / 50.0
        strength = min(1.0, max(0.0, strength))
        return SignalSemantic(
            direction=explanation.direction,
            direction_label=explanation.direction_label,
            strength=round(strength, 4),
            base_confidence=explanation.confidence_score,
        )

    def map_risk(self, risk_explanation: RiskExplanation | None, scenario_results: list[ScenarioResult] | None = None) -> RiskSemantic:
        if risk_explanation is None:
            return self._default_risk()
        return self._build_risk_semantic(risk_explanation, scenario_results or [])

    def map_scenario(self, scenario_results: list[ScenarioResult] | None, signal_direction: str = "NEUTRAL") -> ScenarioSemantic:
        if not scenario_results:
            return ScenarioSemantic(
                stability_score=0.0,
                worst_case_score_change=0.0,
                state_change_count=0,
            )
        score_changes = [r.score_change for r in scenario_results]
        worst_change = min(score_changes)
        state_changes = sum(1 for r in scenario_results if r.state_changed)
        total = len(scenario_results)
        stability_score = 1.0 - (state_changes / total) - (abs(worst_change) / 200.0)
        stability_score = max(0.0, min(1.0, stability_score))
        entries: list[dict] = []
        for r in scenario_results:
            entries.append({
                "name": r.scenario.name,
                "original_score": r.original_score,
                "simulated_score": r.simulated_score,
                "score_change": r.score_change,
                "state_changed": r.state_changed,
                "impact": r.impact_assessment,
            })
        return ScenarioSemantic(
            stability_score=round(stability_score, 4),
            worst_case_score_change=round(worst_change, 2),
            state_change_count=state_changes,
            entries=entries,
        )

    def map_execution(self, execution_report: ExecutionReport | None) -> ExecutionSemantic:
        if execution_report is None:
            return self._default_execution()
        feasibility = execution_report.quality.overall_quality_score
        feasibility = max(0.0, min(1.0, feasibility))
        return ExecutionSemantic(
            feasibility=round(feasibility, 4),
            estimated_slippage_bps=execution_report.quality.avg_slippage_bps,
            estimated_fill_rate=round(execution_report.fill_rate, 4),
            quality_grade=execution_report.quality.quality_grade,
            warnings=list(execution_report.warnings),
        )

    def map_risk_from_signals(
        self,
        factor_items: list[FactorAttributionItem],
        scenario_results: list[ScenarioResult],
    ) -> RiskSemantic:
        bearish_count = sum(1 for i in factor_items if i.raw_value < 50)
        factor_risk = min(1.0, bearish_count / max(len(factor_items), 1))
        changes = [abs(r.score_change) for r in scenario_results] if scenario_results else [0.0]
        max_change = max(changes) if changes else 0.0
        scenario_vulnerability = min(1.0, max_change / 100.0)
        combined_risk = factor_risk * 0.6 + scenario_vulnerability * 0.4
        if combined_risk >= 0.6:
            level = RISK_LEVEL_HIGH
        elif combined_risk >= 0.3:
            level = RISK_LEVEL_MODERATE
        else:
            level = RISK_LEVEL_LOW

        warnings: list[str] = []
        if factor_risk >= 0.5:
            warnings.append(f"多项因子偏空 ({bearish_count}/{len(factor_items)})")
        if max_change >= 15:
            warnings.append(f"情景冲击显著 (最大变化: {max_change:.1f})")

        return RiskSemantic(
            overall_level=level,
            drawdown_risk=factor_risk,
            volatility_risk=scenario_vulnerability,
            correlation_risk=0.0,
            scenario_vulnerability=round(scenario_vulnerability, 4),
            warnings=warnings,
        )

    def _build_risk_semantic(
        self,
        risk: RiskExplanation,
        scenario_results: list[ScenarioResult],
    ) -> RiskSemantic:
        levels = {
            RISK_LEVEL_HIGH: 1.0,
            RISK_LEVEL_MODERATE: 0.5,
            RISK_LEVEL_LOW: 0.0,
        }
        changes = [abs(r.score_change) for r in scenario_results] if scenario_results else [0.0]
        max_change = max(changes) if changes else 0.0
        scenario_vulnerability = min(1.0, max_change / 100.0)
        return RiskSemantic(
            overall_level=risk.overall_risk_level,
            drawdown_risk=levels.get(risk.drawdown.risk_level, 0.5),
            volatility_risk=levels.get(risk.volatility.risk_level, 0.5),
            correlation_risk=levels.get(risk.correlation.risk_level, 0.5),
            scenario_vulnerability=round(scenario_vulnerability, 4),
            warnings=list(risk.warnings),
        )

    def _default_risk(self) -> RiskSemantic:
        return RiskSemantic(
            overall_level=RISK_LEVEL_LOW,
            drawdown_risk=0.0,
            volatility_risk=0.0,
            correlation_risk=0.0,
            scenario_vulnerability=0.0,
        )

    def _default_execution(self) -> ExecutionSemantic:
        return ExecutionSemantic(
            feasibility=0.5,
            estimated_slippage_bps=0.0,
            estimated_fill_rate=0.0,
            quality_grade="C",
        )
