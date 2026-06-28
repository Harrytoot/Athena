from pydantic import BaseModel, Field

from app.application.dtos.decision_dtos import (
    ConsistencyReportDTO,
    ExecutionSemanticDTO,
    FactorSemanticDTO,
    RiskSemanticDTO,
    ScenarioSemanticDTO,
    SignalSemanticDTO,
)
from app.decision_semantics.schema import (
    ConsistencyReport,
    ContradictionEntry,
    DecisionSemantic,
    ExecutionSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    SignalSemantic,
)


class ContradictionResponse(BaseModel):
    contradiction_type: str = Field(alias="contradictionType")
    severity: str
    description: str

    model_config = {"populate_by_name": True}


class ConsistencyResponse(BaseModel):
    is_consistent: bool = Field(alias="isConsistent")
    contradictions: list[ContradictionResponse] = Field(default_factory=list)
    consistency_score: float = Field(alias="consistencyScore")

    model_config = {"populate_by_name": True}


class DecisionSemanticResponse(BaseModel):
    symbol: str
    name: str
    signal: SignalSemanticDTO
    factors: list[FactorSemanticDTO] = Field(default_factory=list)
    risk: RiskSemanticDTO | None = None
    scenario: ScenarioSemanticDTO | None = None
    execution: ExecutionSemanticDTO | None = None
    confidence_score: float = Field(alias="confidenceScore")
    consistency: ConsistencyResponse | None = None
    action: str = "HOLD"
    action_label: str = Field(alias="actionLabel")
    summary: str = ""
    semantic_version: str = Field(default="1.0.0", alias="semanticVersion")
    generated_at: str = Field(alias="generatedAt")

    model_config = {"populate_by_name": True}


class ExplainResponse(BaseModel):
    symbol: str
    name: str
    action: str
    action_label: str = Field(alias="actionLabel")
    summary: str
    direction: str
    direction_label: str = Field(alias="directionLabel")
    confidence_score: float = Field(alias="confidenceScore")
    semantic_version: str = Field(default="1.0.0", alias="semanticVersion")
    generated_at: str = Field(alias="generatedAt")
    factors: list[FactorSemanticDTO] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list, alias="riskWarnings")
    scenario_summary: str = Field(default="", alias="scenarioSummary")

    model_config = {"populate_by_name": True}


class BatchRequest(BaseModel):
    symbols: list[str]


class BatchResponse(BaseModel):
    results: list[DecisionSemanticResponse]


class ErrorResponse(BaseModel):
    detail: str


class SemanticSerializer:

    def serialize(self, semantic: DecisionSemantic) -> DecisionSemanticResponse:
        return DecisionSemanticResponse(
            symbol=semantic.symbol,
            name=semantic.name,
            signal=self._serialize_signal(semantic.signal),
            factors=self._serialize_factors(semantic.factors),
            risk=self._serialize_risk(semantic.risk),
            scenario=self._serialize_scenario(semantic.scenario),
            execution=self._serialize_execution(semantic.execution),
            confidence_score=semantic.confidence_score,
            consistency=self._serialize_consistency(semantic.consistency),
            action=semantic.action,
            action_label=semantic.action_label,
            summary=semantic.summary,
            semantic_version=semantic.semantic_version,
            generated_at=semantic.generated_at,
        )

    def serialize_explain(self, semantic: DecisionSemantic) -> ExplainResponse:
        scenario_summary = ""
        if semantic.scenario and semantic.scenario.entries:
            total = len(semantic.scenario.entries)
            changes = sum(1 for e in semantic.scenario.entries if e.get("state_changed"))
            scenario_summary = f"stability={semantic.scenario.stability_score:.2f}, worst_change={semantic.scenario.worst_case_score_change:+.1f}, state_changes={changes}/{total}"

        return ExplainResponse(
            symbol=semantic.symbol,
            name=semantic.name,
            action=semantic.action,
            action_label=semantic.action_label,
            summary=semantic.summary,
            direction=semantic.signal.direction,
            direction_label=semantic.signal.direction_label,
            confidence_score=semantic.confidence_score,
            semantic_version=semantic.semantic_version,
            generated_at=semantic.generated_at,
            factors=self._serialize_factors(semantic.factors),
            risk_warnings=semantic.risk.warnings if semantic.risk else [],
            scenario_summary=scenario_summary,
        )

    def _serialize_signal(self, signal: SignalSemantic) -> SignalSemanticDTO:
        return SignalSemanticDTO(
            direction=signal.direction,
            direction_label=signal.direction_label,
            strength=signal.strength,
            base_confidence=signal.base_confidence,
        )

    def _serialize_factors(self, factors: list[FactorSemantic]) -> list[FactorSemanticDTO]:
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

    def _serialize_risk(self, risk: RiskSemantic | None) -> RiskSemanticDTO | None:
        if risk is None:
            return None
        return RiskSemanticDTO(
            overall_level=risk.overall_level,
            drawdown_risk=risk.drawdown_risk,
            volatility_risk=risk.volatility_risk,
            correlation_risk=risk.correlation_risk,
            scenario_vulnerability=risk.scenario_vulnerability,
            warnings=risk.warnings,
        )

    def _serialize_scenario(self, scenario: ScenarioSemantic | None) -> ScenarioSemanticDTO | None:
        if scenario is None:
            return None
        return ScenarioSemanticDTO(
            stability_score=scenario.stability_score,
            worst_case_score_change=scenario.worst_case_score_change,
            state_change_count=scenario.state_change_count,
            entries=scenario.entries,
        )

    def _serialize_execution(self, execution: ExecutionSemantic | None) -> ExecutionSemanticDTO | None:
        if execution is None:
            return None
        return ExecutionSemanticDTO(
            feasibility=execution.feasibility,
            estimated_slippage_bps=execution.estimated_slippage_bps,
            estimated_fill_rate=execution.estimated_fill_rate,
            quality_grade=execution.quality_grade,
            warnings=execution.warnings,
        )

    def _serialize_consistency(self, consistency: ConsistencyReport | None) -> ConsistencyResponse | None:
        if consistency is None:
            return None
        return ConsistencyResponse(
            is_consistent=consistency.is_consistent,
            contradictions=[
                ContradictionResponse(
                    contradiction_type=c.contradiction_type,
                    severity=c.severity,
                    description=c.description,
                )
                for c in consistency.contradictions
            ],
            consistency_score=consistency.consistency_score,
        )
