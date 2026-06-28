import math
from typing import Optional

from app.application.dtos.decision_dtos import (
    ActionEnum,
    ConsensusItemDTO,
    ConsensusTypeEnum,
    ConsistencyReportDTO,
    ContradictionDTO,
    DecisionDTO,
    ExecutionSemanticDTO,
    FactorSemanticDTO,
    RiskItemDTO,
    RiskSemanticDTO,
    ScenarioEntryDTO,
    ScenarioSemanticDTO,
    SeverityEnum,
    SignalEnum,
    SignalSemanticDTO,
)
from app.application.services.market_score_service import MarketScoreService
from app.application.services.stock_service import StockService
from app.decision_semantics.confidence_model import ConfidenceModel
from app.decision_semantics.mapper import SemanticMapper
from app.decision_semantics.registry import SemanticRegistry, DEFAULT_SEMANTIC_VERSION
from app.decision_semantics.validator import SemanticValidator
from app.decision_transparency.factor_attribution import FactorAttributionEngine, FactorAttributionItem
from app.decision_transparency.scenario_simulator import ScenarioSimulator
from app.decision_transparency.signal_explainer import SignalExplainer, SignalExplanation
from app.domain.market.market_score import MarketScore

SIGNAL_STRONG_THRESHOLD = 75
BULL_COLOR = "#00B8D9"
BASE_COLOR = "#8B95A5"
BEAR_COLOR = "#FF5630"
DAYS_IN_MONTH = 20
MAX_DAILY_VOL = 0.03


class DecisionService:

    def __init__(
        self,
        market_score_service: MarketScoreService,
        stock_service: StockService,
    ):
        self._market_score_service = market_score_service
        self._stock_service = stock_service
        self._signal_explainer = SignalExplainer()
        self._factor_engine = FactorAttributionEngine()
        self._scenario_simulator = ScenarioSimulator()
        self._mapper = SemanticMapper()
        self._confidence_model = ConfidenceModel()
        self._validator = SemanticValidator()
        self._registry = SemanticRegistry()

    async def get_decision(self, symbol: str) -> Optional[DecisionDTO]:
        stock = await self._stock_service.get_stock_detail(symbol)
        if stock is None:
            return None

        score_data = await self._market_score_service.get_score()
        score = MarketScore(
            trend=score_data["trend"],
            liquidity=score_data["liquidity"],
            breadth=score_data["breadth"],
            volatility=score_data["volatility"],
            sentiment=score_data["sentiment"],
        )

        signal_explanation = self._signal_explainer.explain(score)
        attribution = self._factor_engine.attribute(score)
        scenario_results = self._scenario_simulator.simulate(
            trend=score.trend,
            liquidity=score.liquidity,
            breadth=score.breadth,
            volatility=score.volatility,
            sentiment=score.sentiment,
        )

        signal_semantic = self._mapper.map_signal(signal_explanation)
        factors = self._mapper.map_factors(score, attribution)
        risk_semantic = self._mapper.map_risk_from_signals(attribution.items, scenario_results)
        scenario_semantic = self._mapper.map_scenario(scenario_results, signal_semantic.direction)

        confidence = self._confidence_model.compute(
            signal=signal_semantic,
            factors=factors,
            scenario=scenario_semantic,
            risk=risk_semantic,
        )

        consistency = self._validator.validate(
            signal=signal_semantic,
            factors=factors,
            risk=risk_semantic,
            scenario=scenario_semantic,
        )

        return DecisionDTO(
            symbol=stock.symbol,
            name=stock.name,
            signal=self._map_signal(signal_explanation),
            signal_label=signal_explanation.direction_label,
            confidence=signal_explanation.confidence_score,
            consensus_items=self._build_consensus_items(attribution.items),
            risk_items=self._build_risk_items(attribution.items, scenario_results),
            scenarios=self._build_scenarios(score),
            action=self._map_action(signal_explanation),
            action_label=self._map_action_label(signal_explanation),
            explanation=signal_explanation.summary,
            factors=self._build_factor_semantic_dtos(factors),
            signal_semantic=self._build_signal_semantic_dto(signal_semantic),
            risk_semantic=self._build_risk_semantic_dto(risk_semantic),
            scenario_semantic=self._build_scenario_semantic_dto(scenario_semantic),
            execution_semantic=None,
            consistency=self._build_consistency_dto(consistency),
            confidence_score_normalized=confidence,
            semantic_version=DEFAULT_SEMANTIC_VERSION,
        )

    def _build_scenarios(self, score: MarketScore) -> list[ScenarioEntryDTO]:
        daily_vol = (100.0 - score.volatility) / 100.0 * MAX_DAILY_VOL
        monthly_vol = daily_vol * math.sqrt(DAYS_IN_MONTH)

        trend_direction = (score.total - 50.0) / 50.0
        base_return = round(trend_direction * monthly_vol * 1.5 * 100, 1)
        sigma_band = round(monthly_vol * 1.5 * 100, 1)

        bull_return = round(base_return + sigma_band, 1)
        bear_return = round(base_return - sigma_band, 1)

        return [
            ScenarioEntryDTO(label="🐂 Bull", return_pct=bull_return, color=BULL_COLOR),
            ScenarioEntryDTO(label="📊 Base", return_pct=base_return, color=BASE_COLOR),
            ScenarioEntryDTO(label="🐻 Bear", return_pct=bear_return, color=BEAR_COLOR),
        ]

    def _map_signal(self, explanation: SignalExplanation) -> SignalEnum:
        direction = explanation.direction
        confidence = explanation.confidence_score

        if direction == "LONG":
            return SignalEnum.STRONG_BUY if confidence >= SIGNAL_STRONG_THRESHOLD else SignalEnum.BUY
        if direction == "SHORT":
            return SignalEnum.STRONG_SELL if confidence >= SIGNAL_STRONG_THRESHOLD else SignalEnum.SELL
        return SignalEnum.NEUTRAL

    def _map_action(self, explanation: SignalExplanation) -> ActionEnum:
        signal = self._map_signal(explanation)
        action_map = {
            SignalEnum.STRONG_BUY: ActionEnum.APPROVE,
            SignalEnum.BUY: ActionEnum.APPROVE,
            SignalEnum.NEUTRAL: ActionEnum.HOLD,
            SignalEnum.SELL: ActionEnum.HOLD,
            SignalEnum.STRONG_SELL: ActionEnum.REJECT,
        }
        return action_map.get(signal, ActionEnum.HOLD)

    def _map_action_label(self, explanation: SignalExplanation) -> str:
        signal = self._map_signal(explanation)
        label_map = {
            SignalEnum.STRONG_BUY: "执行买入",
            SignalEnum.BUY: "小仓位介入",
            SignalEnum.NEUTRAL: "等待确认信号",
            SignalEnum.SELL: "减仓观望",
            SignalEnum.STRONG_SELL: "清仓离场",
        }
        return label_map.get(signal, "等待确认信号")

    def _build_consensus_items(
        self,
        items: list[FactorAttributionItem],
    ) -> list[ConsensusItemDTO]:
        positive = [i for i in items if i.is_positive]
        positive.sort(key=lambda i: i.contribution_percentage, reverse=True)
        top3 = positive[:3]

        result: list[ConsensusItemDTO] = []
        for item in top3:
            result.append(ConsensusItemDTO(
                text=f"{item.factor_label}: {item.interpretation}",
                type=ConsensusTypeEnum.BULLISH,
            ))
        return result

    def _build_risk_items(
        self,
        items: list[FactorAttributionItem],
        scenario_results,
    ) -> list[RiskItemDTO]:
        risk_items: list[RiskItemDTO] = []

        negative = [i for i in items if not i.is_positive]
        negative.sort(key=lambda i: abs(i.contribution_percentage), reverse=True)
        for item in negative[:2]:
            severity = (
                SeverityEnum.HIGH if abs(item.contribution_percentage) >= 10
                else SeverityEnum.MEDIUM if abs(item.contribution_percentage) >= 5
                else SeverityEnum.LOW
            )
            risk_items.append(RiskItemDTO(
                text=f"{item.factor_label}: {item.interpretation} (贡献 {item.weighted_contribution:+.1f})",
                severity=severity,
            ))

        high_impact_scenarios = [s for s in scenario_results if abs(s.score_change) >= 10]
        high_impact_scenarios.sort(key=lambda s: abs(s.score_change), reverse=True)
        for scenario in high_impact_scenarios[:3]:
            severity = (
                SeverityEnum.HIGH if abs(scenario.score_change) >= 20
                else SeverityEnum.MEDIUM
            )
            risk_items.append(RiskItemDTO(
                text=f"情景[{scenario.scenario.name}]: {scenario.impact_assessment}",
                severity=severity,
            ))

        return risk_items[:4]

    def _build_factor_semantic_dtos(self, factors) -> list[FactorSemanticDTO]:
        return [
            FactorSemanticDTO(
                name=f.name,
                label=f.label,
                value=f.value,
                weight=f.weight,
                contribution=f.contribution,
                is_bullish=f.is_bullish,
                assessment=f.assessment,
            )
            for f in factors
        ]

    def _build_signal_semantic_dto(self, signal) -> SignalSemanticDTO:
        return SignalSemanticDTO(
            direction=signal.direction,
            direction_label=signal.direction_label,
            strength=signal.strength,
            base_confidence=signal.base_confidence,
        )

    def _build_risk_semantic_dto(self, risk) -> RiskSemanticDTO:
        return RiskSemanticDTO(
            overall_level=risk.overall_level,
            drawdown_risk=risk.drawdown_risk,
            volatility_risk=risk.volatility_risk,
            correlation_risk=risk.correlation_risk,
            scenario_vulnerability=risk.scenario_vulnerability,
            warnings=risk.warnings,
        )

    def _build_scenario_semantic_dto(self, scenario) -> ScenarioSemanticDTO:
        return ScenarioSemanticDTO(
            stability_score=scenario.stability_score,
            worst_case_score_change=scenario.worst_case_score_change,
            state_change_count=scenario.state_change_count,
            entries=scenario.entries,
        )

    def _build_consistency_dto(self, consistency) -> ConsistencyReportDTO:
        return ConsistencyReportDTO(
            is_consistent=consistency.is_consistent,
            contradictions=[
                ContradictionDTO(
                    contradiction_type=c.contradiction_type,
                    severity=c.severity,
                    description=c.description,
                )
                for c in consistency.contradictions
            ],
            consistency_score=consistency.consistency_score,
        )
