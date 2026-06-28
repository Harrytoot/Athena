from dataclasses import dataclass

from app.decision_semantics.schema import (
    DecisionSemantic,
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ExecutionSemantic,
    ConsistencyReport,
    ContradictionEntry,
)


@dataclass
class ReductionInput:
    symbol: str
    name: str
    signal: SignalSemantic | None = None
    factors: list[FactorSemantic] | None = None
    risk: RiskSemantic | None = None
    scenario: ScenarioSemantic | None = None
    execution: ExecutionSemantic | None = None
    consistency: ConsistencyReport | None = None
    confidence_score: float | None = None
    action: str = "HOLD"
    action_label: str = ""
    summary: str = ""
    semantic_version: str = "1.0.0"


class SemanticReducer:

    def reduce(self, inputs: list[ReductionInput]) -> DecisionSemantic:
        if not inputs:
            return self._empty_semantic()

        primary = inputs[0]

        merged_factors = primary.factors or []
        merged_risk = primary.risk
        merged_scenario = primary.scenario
        merged_execution = primary.execution
        merged_consistency = primary.consistency

        for inp in inputs[1:]:
            if inp.factors:
                merged_factors = self._merge_factors(merged_factors, inp.factors)
            if inp.risk and not merged_risk:
                merged_risk = inp.risk
            if inp.scenario and not merged_scenario:
                merged_scenario = inp.scenario
            if inp.execution and not merged_execution:
                merged_execution = inp.execution
            if inp.consistency:
                merged_consistency = self._merge_consistency(
                    merged_consistency, inp.consistency
                )

        confidence = primary.confidence_score or 0.5

        return DecisionSemantic(
            symbol=primary.symbol,
            name=primary.name,
            signal=primary.signal or SignalSemantic(
                direction="NEUTRAL",
                direction_label="中性",
                strength=0.0,
                base_confidence=50.0,
            ),
            factors=merged_factors,
            risk=merged_risk,
            scenario=merged_scenario,
            execution=merged_execution,
            confidence_score=confidence,
            consistency=merged_consistency,
            action=primary.action,
            action_label=primary.action_label,
            summary=primary.summary,
            semantic_version=primary.semantic_version,
        )

    def _merge_factors(
        self,
        base: list[FactorSemantic],
        incoming: list[FactorSemantic],
    ) -> list[FactorSemantic]:
        existing_names = {f.name for f in base}
        for factor in incoming:
            if factor.name not in existing_names:
                base.append(factor)
                existing_names.add(factor.name)
        return base

    def _merge_consistency(
        self,
        base: ConsistencyReport | None,
        incoming: ConsistencyReport,
    ) -> ConsistencyReport:
        if base is None:
            return incoming
        merged_contradictions = list(base.contradictions)
        for c in incoming.contradictions:
            if c.contradiction_type not in {mc.contradiction_type for mc in merged_contradictions}:
                merged_contradictions.append(c)
        combined_score = min(base.consistency_score, incoming.consistency_score)
        return ConsistencyReport(
            is_consistent=len(merged_contradictions) == 0,
            contradictions=merged_contradictions,
            consistency_score=combined_score,
        )

    def _empty_semantic(self) -> DecisionSemantic:
        return DecisionSemantic(
            symbol="",
            name="",
            signal=SignalSemantic(
                direction="NEUTRAL",
                direction_label="中性",
                strength=0.0,
                base_confidence=50.0,
            ),
            confidence_score=0.5,
            action="HOLD",
            action_label="等待确认信号",
        )
