import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.schema import (
    DecisionSemantic,
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ExecutionSemantic,
    ConsistencyReport,
)
from app.decision_semantics.evolution.version_manager import (
    EvolutionVersionManager,
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
    EvolutionKind,
)


@dataclass
class DecisionSemanticV1_1:
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
    semantic_version: str = SCHEMA_V1_1
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    strategy_id: str = ""
    source_pipeline: str = ""


@dataclass
class DecisionSemanticV2_0:
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
    semantic_version: str = SCHEMA_V2_0
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision_id: str = ""
    tags: list[str] = field(default_factory=list)
    narrative: str = ""


@dataclass
class UpgradeResult:
    original: DecisionSemantic
    result: DecisionSemantic
    from_version: str
    to_version: str
    applied_rules: list[str]


@dataclass
class DowngradeResult:
    original: DecisionSemantic
    result: DecisionSemantic
    from_version: str
    to_version: str
    dropped_fields: list[str]
    mapped_fields: list[str]


class SchemaEvolver:

    def __init__(self):
        self._version_manager = EvolutionVersionManager()

    def upgrade(self, semantic: DecisionSemantic, target_version: str) -> UpgradeResult:
        from_ver = semantic.semantic_version
        if from_ver == target_version:
            return UpgradeResult(
                original=semantic,
                result=semantic,
                from_version=from_ver,
                to_version=target_version,
                applied_rules=[],
            )

        path = self._version_manager.get_upgrade_path(from_ver, target_version)
        if path is None:
            raise ValueError(
                f"No upgrade path from {from_ver} to {target_version}"
            )

        applied: list[str] = []

        serializable = self._to_serializable(semantic)

        for rule in path.rules:
            if rule.kind == EvolutionKind.RENAME:
                target = rule.field_name
                if target == "narrative":
                    serializable["narrative"] = serializable.pop("summary", "")
                elif target == "summary":
                    serializable["summary"] = serializable.pop("narrative", "")
            serializable = rule.transform(serializable)
            applied.append(rule.description)

        if target_version == SCHEMA_V1_1:
            result = self._from_serializable_v1_1(serializable)
        elif target_version == SCHEMA_V1_0:
            result = self._from_serializable_v1_0(serializable)
        else:
            result = self._from_serializable_v2_0(serializable)

        result.semantic_version = target_version

        return UpgradeResult(
            original=semantic,
            result=result,
            from_version=from_ver,
            to_version=target_version,
            applied_rules=applied,
        )

    def upgrade_to_target(
        self,
        semantic: DecisionSemantic,
        target_version: str,
    ) -> DecisionSemantic:
        return self.upgrade(semantic, target_version).result

    def downgrade(
        self,
        semantic: DecisionSemantic,
        target_version: str,
    ) -> DowngradeResult:
        from_ver = semantic.semantic_version
        if from_ver == target_version:
            return DowngradeResult(
                original=semantic,
                result=semantic,
                from_version=from_ver,
                to_version=target_version,
                dropped_fields=[],
                mapped_fields=[],
            )

        path = self._version_manager.get_downgrade_path(from_ver, target_version)
        if path is None:
            raise ValueError(
                f"No downgrade path from {from_ver} to {target_version}"
            )

        dropped: list[str] = []
        mapped: list[str] = []

        serializable = self._to_serializable(semantic)

        for rule in path.rules:
            if rule.kind == EvolutionKind.ADDITIVE:
                serializable.pop(rule.field_name, None)
                dropped.append(rule.field_name)
            elif rule.kind == EvolutionKind.RENAME:
                if rule.field_name == "summary":
                    serializable["summary"] = serializable.pop("narrative", "")
                    mapped.append("narrative → summary")
                elif rule.field_name == "narrative":
                    serializable["narrative"] = serializable.pop("summary", "")
                    mapped.append("summary → narrative")

        if target_version == SCHEMA_V1_1:
            result = self._from_serializable_v1_1(serializable)
        else:
            result = self._from_serializable_v1_0(serializable)

        result.semantic_version = target_version

        return DowngradeResult(
            original=semantic,
            result=result,
            from_version=from_ver,
            to_version=target_version,
            dropped_fields=dropped,
            mapped_fields=mapped,
        )

    def downgrade_to_target(
        self,
        semantic: DecisionSemantic,
        target_version: str,
    ) -> DecisionSemantic:
        return self.downgrade(semantic, target_version).result

    def to_v1_1(
        self,
        v1_0: DecisionSemantic,
        strategy_id: str = "",
        source_pipeline: str = "",
    ) -> DecisionSemantic:
        serializable = self._to_serializable(v1_0)
        serializable["strategy_id"] = strategy_id
        serializable["source_pipeline"] = source_pipeline
        serializable["semantic_version"] = SCHEMA_V1_1
        return self._from_serializable_v1_1(serializable)

    def to_v2_0(
        self,
        source: DecisionSemantic,
        decision_id: str = "",
        tags: list[str] | None = None,
        narrative: str = "",
    ) -> DecisionSemantic:
        serializable = self._to_serializable(source)
        serializable["decision_id"] = decision_id or self._generate_decision_id(
            serializable
        )
        serializable["tags"] = tags or []
        serializable["narrative"] = narrative or serializable.get("summary", "")
        serializable.pop("summary", None)
        serializable["semantic_version"] = SCHEMA_V2_0
        return self._from_serializable_v2_0(serializable)

    def _to_serializable(self, semantic: DecisionSemantic) -> dict:
        result = {
            "symbol": semantic.symbol,
            "name": semantic.name,
            "signal": {
                "direction": semantic.signal.direction,
                "direction_label": semantic.signal.direction_label,
                "strength": semantic.signal.strength,
                "base_confidence": semantic.signal.base_confidence,
            },
            "factors": [
                {
                    "name": f.name,
                    "label": f.label,
                    "value": f.value,
                    "weight": f.weight,
                    "contribution": f.contribution,
                    "is_bullish": f.is_bullish,
                    "assessment": f.assessment,
                }
                for f in semantic.factors
            ],
            "risk": (
                {
                    "overall_level": semantic.risk.overall_level,
                    "drawdown_risk": semantic.risk.drawdown_risk,
                    "volatility_risk": semantic.risk.volatility_risk,
                    "correlation_risk": semantic.risk.correlation_risk,
                    "scenario_vulnerability": semantic.risk.scenario_vulnerability,
                    "warnings": list(semantic.risk.warnings),
                }
                if semantic.risk
                else None
            ),
            "scenario": (
                {
                    "stability_score": semantic.scenario.stability_score,
                    "worst_case_score_change": semantic.scenario.worst_case_score_change,
                    "state_change_count": semantic.scenario.state_change_count,
                    "entries": list(semantic.scenario.entries),
                }
                if semantic.scenario
                else None
            ),
            "execution": (
                {
                    "feasibility": semantic.execution.feasibility,
                    "estimated_slippage_bps": semantic.execution.estimated_slippage_bps,
                    "estimated_fill_rate": semantic.execution.estimated_fill_rate,
                    "quality_grade": semantic.execution.quality_grade,
                    "warnings": list(semantic.execution.warnings),
                }
                if semantic.execution
                else None
            ),
            "confidence_score": semantic.confidence_score,
            "consistency": (
                {
                    "is_consistent": semantic.consistency.is_consistent,
                    "contradictions": [
                        {
                            "contradiction_type": c.contradiction_type,
                            "severity": c.severity,
                            "description": c.description,
                        }
                        for c in semantic.consistency.contradictions
                    ],
                    "consistency_score": semantic.consistency.consistency_score,
                }
                if semantic.consistency
                else None
            ),
            "action": semantic.action,
            "action_label": semantic.action_label,
            "summary": semantic.summary,
            "semantic_version": semantic.semantic_version,
            "generated_at": semantic.generated_at,
            "strategy_id": getattr(semantic, "strategy_id", ""),
            "source_pipeline": getattr(semantic, "source_pipeline", ""),
            "decision_id": getattr(semantic, "decision_id", ""),
            "tags": getattr(semantic, "tags", []),
            "narrative": getattr(semantic, "narrative", ""),
        }
        return result

    def _from_serializable_v1_0(self, data: dict) -> DecisionSemantic:
        return DecisionSemantic(
            symbol=data["symbol"],
            name=data["name"],
            signal=self._build_signal(data["signal"]),
            factors=[self._build_factor(f) for f in data.get("factors", [])],
            risk=self._build_risk(data["risk"]) if data.get("risk") else None,
            scenario=self._build_scenario(data["scenario"]) if data.get("scenario") else None,
            execution=self._build_execution(data["execution"]) if data.get("execution") else None,
            confidence_score=data.get("confidence_score", 0.5),
            consistency=self._build_consistency(data["consistency"]) if data.get("consistency") else None,
            action=data.get("action", "HOLD"),
            action_label=data.get("action_label", ""),
            summary=data.get("summary", ""),
            semantic_version=data.get("semantic_version", SCHEMA_V1_0),
            generated_at=data.get("generated_at", ""),
        )

    def _from_serializable_v1_1(self, data: dict) -> DecisionSemantic:
        result = self._from_serializable_v1_0(data)
        result.strategy_id = data.get("strategy_id", "")
        result.source_pipeline = data.get("source_pipeline", "")
        result.semantic_version = SCHEMA_V1_1
        return result

    def _from_serializable_v2_0(self, data: dict) -> DecisionSemantic:
        result = DecisionSemantic(
            symbol=data["symbol"],
            name=data["name"],
            signal=self._build_signal(data["signal"]),
            factors=[self._build_factor(f) for f in data.get("factors", [])],
            risk=self._build_risk(data["risk"]) if data.get("risk") else None,
            scenario=self._build_scenario(data["scenario"]) if data.get("scenario") else None,
            execution=self._build_execution(data["execution"]) if data.get("execution") else None,
            confidence_score=data.get("confidence_score", 0.5),
            consistency=self._build_consistency(data["consistency"]) if data.get("consistency") else None,
            action=data.get("action", "HOLD"),
            action_label=data.get("action_label", ""),
            summary=data.get("summary", data.get("narrative", "")),
            semantic_version=data.get("semantic_version", SCHEMA_V2_0),
            generated_at=data.get("generated_at", ""),
        )
        decision_id = data.get("decision_id", "")
        result.decision_id = decision_id or self._generate_decision_id(data)
        result.tags = data.get("tags", [])
        result.narrative = data.get("narrative") or data.get("summary", "")
        result.strategy_id = data.get("strategy_id", "")
        result.source_pipeline = data.get("source_pipeline", "")
        return result

    def _build_signal(self, data: dict) -> SignalSemantic:
        return SignalSemantic(
            direction=data["direction"],
            direction_label=data["direction_label"],
            strength=data["strength"],
            base_confidence=data["base_confidence"],
        )

    def _build_factor(self, data: dict) -> FactorSemantic:
        return FactorSemantic(
            name=data["name"],
            label=data["label"],
            value=data["value"],
            weight=data["weight"],
            contribution=data["contribution"],
            is_bullish=data["is_bullish"],
            assessment=data["assessment"],
        )

    def _build_risk(self, data: dict) -> RiskSemantic:
        return RiskSemantic(
            overall_level=data["overall_level"],
            drawdown_risk=data["drawdown_risk"],
            volatility_risk=data["volatility_risk"],
            correlation_risk=data["correlation_risk"],
            scenario_vulnerability=data["scenario_vulnerability"],
            warnings=list(data.get("warnings", [])),
        )

    def _build_scenario(self, data: dict) -> ScenarioSemantic:
        return ScenarioSemantic(
            stability_score=data["stability_score"],
            worst_case_score_change=data["worst_case_score_change"],
            state_change_count=data["state_change_count"],
            entries=list(data.get("entries", [])),
        )

    def _build_execution(self, data: dict) -> ExecutionSemantic:
        return ExecutionSemantic(
            feasibility=data["feasibility"],
            estimated_slippage_bps=data["estimated_slippage_bps"],
            estimated_fill_rate=data["estimated_fill_rate"],
            quality_grade=data["quality_grade"],
            warnings=list(data.get("warnings", [])),
        )

    def _build_consistency(self, data: dict) -> ConsistencyReport:
        from app.decision_semantics.schema import ContradictionEntry

        return ConsistencyReport(
            is_consistent=data["is_consistent"],
            contradictions=[
                ContradictionEntry(
                    contradiction_type=c["contradiction_type"],
                    severity=c["severity"],
                    description=c["description"],
                )
                for c in data.get("contradictions", [])
            ],
            consistency_score=data.get("consistency_score", 1.0),
        )

    def _generate_decision_id(self, data: dict) -> str:
        payload = {
            "symbol": data.get("symbol", ""),
            "generated_at": data.get("generated_at", ""),
            "action": data.get("action", ""),
            "confidence_score": data.get("confidence_score", 0.0),
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        hash_hex = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"d_{hash_hex[:16]}"
