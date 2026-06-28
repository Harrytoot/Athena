from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class FactorSemantic:
    name: str
    label: str
    value: float
    weight: float
    contribution: float
    is_bullish: bool
    assessment: str


@dataclass
class SignalSemantic:
    direction: str
    direction_label: str
    strength: float
    base_confidence: float


@dataclass
class RiskSemantic:
    overall_level: str
    drawdown_risk: float
    volatility_risk: float
    correlation_risk: float
    scenario_vulnerability: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class ScenarioSemantic:
    stability_score: float
    worst_case_score_change: float
    state_change_count: int
    entries: list[dict] = field(default_factory=list)


@dataclass
class ExecutionSemantic:
    feasibility: float
    estimated_slippage_bps: float
    estimated_fill_rate: float
    quality_grade: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class ContradictionEntry:
    contradiction_type: str
    severity: str
    description: str


@dataclass
class ConsistencyReport:
    is_consistent: bool
    contradictions: list[ContradictionEntry] = field(default_factory=list)
    consistency_score: float = 1.0


@dataclass
class DecisionSemantic:
    symbol: str
    name: str
    signal: SignalSemantic
    factors: list[FactorSemantic] = field(default_factory=list)
    risk: RiskSemantic | None = None
    scenario: ScenarioSemantic | None = None
    execution: ExecutionSemantic | None = None
    confidence_score: float = 0.5
    consistency: ConsistencyReport | None = None
    action: str = "HOLD"
    action_label: str = ""
    summary: str = ""
    semantic_version: str = "1.0.0"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
