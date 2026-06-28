from enum import Enum

from pydantic import BaseModel, Field


class SignalEnum(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class ConsensusTypeEnum(str, Enum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class SeverityEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionEnum(str, Enum):
    APPROVE = "APPROVE"
    HOLD = "HOLD"
    REJECT = "REJECT"


class ConsensusItemDTO(BaseModel):
    text: str
    type: ConsensusTypeEnum


class RiskItemDTO(BaseModel):
    text: str
    severity: SeverityEnum


class ScenarioEntryDTO(BaseModel):
    label: str
    return_pct: float = Field(alias="returnPct")
    color: str

    model_config = {"populate_by_name": True}


class FactorSemanticDTO(BaseModel):
    name: str
    label: str
    value: float
    weight: float
    contribution: float
    is_bullish: bool = Field(alias="isBullish")
    assessment: str

    model_config = {"populate_by_name": True}


class SignalSemanticDTO(BaseModel):
    direction: str
    direction_label: str = Field(alias="directionLabel")
    strength: float
    base_confidence: float = Field(alias="baseConfidence")

    model_config = {"populate_by_name": True}


class RiskSemanticDTO(BaseModel):
    overall_level: str = Field(alias="overallLevel")
    drawdown_risk: float = Field(alias="drawdownRisk")
    volatility_risk: float = Field(alias="volatilityRisk")
    correlation_risk: float = Field(alias="correlationRisk")
    scenario_vulnerability: float = Field(alias="scenarioVulnerability")
    warnings: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ScenarioSemanticDTO(BaseModel):
    stability_score: float = Field(alias="stabilityScore")
    worst_case_score_change: float = Field(alias="worstCaseScoreChange")
    state_change_count: int = Field(alias="stateChangeCount")
    entries: list[dict] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ExecutionSemanticDTO(BaseModel):
    feasibility: float
    estimated_slippage_bps: float = Field(alias="estimatedSlippageBps")
    estimated_fill_rate: float = Field(alias="estimatedFillRate")
    quality_grade: str = Field(alias="qualityGrade")
    warnings: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ContradictionDTO(BaseModel):
    contradiction_type: str = Field(alias="contradictionType")
    severity: str
    description: str

    model_config = {"populate_by_name": True}


class ConsistencyReportDTO(BaseModel):
    is_consistent: bool = Field(alias="isConsistent")
    contradictions: list[ContradictionDTO] = Field(default_factory=list)
    consistency_score: float = Field(alias="consistencyScore")

    model_config = {"populate_by_name": True}


class DecisionDTO(BaseModel):
    symbol: str
    name: str
    signal: SignalEnum
    signal_label: str = Field(alias="signalLabel")
    confidence: float
    consensus_items: list[ConsensusItemDTO] = Field(default_factory=list, alias="consensusItems")
    risk_items: list[RiskItemDTO] = Field(default_factory=list, alias="riskItems")
    scenarios: list[ScenarioEntryDTO] = Field(default_factory=list)
    action: ActionEnum
    action_label: str = Field(alias="actionLabel")
    explanation: str = ""
    factors: list[FactorSemanticDTO] = Field(default_factory=list)
    signal_semantic: SignalSemanticDTO | None = Field(default=None, alias="signalSemantic")
    risk_semantic: RiskSemanticDTO | None = Field(default=None, alias="riskSemantic")
    scenario_semantic: ScenarioSemanticDTO | None = Field(default=None, alias="scenarioSemantic")
    execution_semantic: ExecutionSemanticDTO | None = Field(default=None, alias="executionSemantic")
    consistency: ConsistencyReportDTO | None = Field(default=None)
    confidence_score_normalized: float | None = Field(default=None, alias="confidenceScoreNormalized")
    semantic_version: str = Field(default="1.0.0", alias="semanticVersion")

    model_config = {"populate_by_name": True}
