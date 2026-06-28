import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

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


class DeltaFieldChangeType(Enum):
    CHANGED = "changed"
    ADDED = "added"
    REMOVED = "removed"


@dataclass
class DeltaFieldChange:
    field_path: str
    change_type: DeltaFieldChangeType
    old_value: object | None = None
    new_value: object | None = None


@dataclass
class SemanticDelta:
    from_snapshot_id: str
    to_snapshot_id: str
    symbol: str
    changes: list[DeltaFieldChange] = field(default_factory=list)
    delta_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    delta_id: str = ""

    def __post_init__(self):
        if not self.delta_id:
            self.delta_id = self._compute_id()

    def _compute_id(self) -> str:
        payload = {
            "symbol": self.symbol,
            "from_snapshot_id": self.from_snapshot_id,
            "to_snapshot_id": self.to_snapshot_id,
            "changes": [
                {
                    "field_path": c.field_path,
                    "change_type": c.change_type.value,
                    "new_value": str(c.new_value),
                }
                for c in self.changes
            ],
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def is_empty(self) -> bool:
        return len(self.changes) == 0

    def changed_field_paths(self) -> list[str]:
        return [
            c.field_path
            for c in self.changes
            if c.change_type == DeltaFieldChangeType.CHANGED
        ]

    def added_field_paths(self) -> list[str]:
        return [
            c.field_path
            for c in self.changes
            if c.change_type == DeltaFieldChangeType.ADDED
        ]

    def removed_field_paths(self) -> list[str]:
        return [
            c.field_path
            for c in self.changes
            if c.change_type == DeltaFieldChangeType.REMOVED
        ]


_FLOAT_TOLERANCE = 1e-6


class SemanticDeltaEngine:

    def compute_delta(
        self, older: DecisionSemantic, newer: DecisionSemantic
    ) -> SemanticDelta:
        changes: list[DeltaFieldChange] = []

        older_flat = self._flatten(older)
        newer_flat = self._flatten(newer)

        all_keys = set(older_flat.keys()) | set(newer_flat.keys())

        for key in sorted(all_keys):
            old_val = older_flat.get(key)
            new_val = newer_flat.get(key)

            if key not in older_flat:
                changes.append(DeltaFieldChange(
                    field_path=key,
                    change_type=DeltaFieldChangeType.ADDED,
                    old_value=None,
                    new_value=new_val,
                ))
            elif key not in newer_flat:
                changes.append(DeltaFieldChange(
                    field_path=key,
                    change_type=DeltaFieldChangeType.REMOVED,
                    old_value=old_val,
                    new_value=None,
                ))
            elif not self._values_equal(old_val, new_val):
                changes.append(DeltaFieldChange(
                    field_path=key,
                    change_type=DeltaFieldChangeType.CHANGED,
                    old_value=old_val,
                    new_value=new_val,
                ))

        return SemanticDelta(
            from_snapshot_id="",
            to_snapshot_id="",
            symbol=older.symbol,
            changes=changes,
        )

    def apply_delta(
        self, semantic: DecisionSemantic, delta: SemanticDelta
    ) -> DecisionSemantic:
        result = deepcopy(semantic)

        flat = self._flatten(result)

        for change in delta.changes:
            if change.change_type == DeltaFieldChangeType.CHANGED:
                if change.field_path in flat:
                    flat[change.field_path] = change.new_value
            elif change.change_type == DeltaFieldChangeType.ADDED:
                flat[change.field_path] = change.new_value
            elif change.change_type == DeltaFieldChangeType.REMOVED:
                flat.pop(change.field_path, None)

        rebuilt = self._unflatten(flat, result.semantic_version)
        return rebuilt

    def is_delta_applicable(
        self, semantic: DecisionSemantic, delta: SemanticDelta
    ) -> bool:
        if delta.symbol and delta.symbol != semantic.symbol:
            return False

        flat = self._flatten(semantic)

        for change in delta.changes:
            if change.change_type == DeltaFieldChangeType.CHANGED:
                if change.field_path not in flat:
                    return False
            elif change.change_type == DeltaFieldChangeType.REMOVED:
                if change.field_path not in flat:
                    continue

        return True

    def merge_deltas(self, deltas: list[SemanticDelta]) -> SemanticDelta:
        if not deltas:
            raise ValueError("Cannot merge empty delta list")

        all_changes: dict[str, DeltaFieldChange] = {}
        symbol = deltas[0].symbol
        from_id = deltas[0].from_snapshot_id
        to_id = deltas[-1].to_snapshot_id

        for delta in deltas:
            for change in delta.changes:
                all_changes[change.field_path] = change

        return SemanticDelta(
            from_snapshot_id=from_id,
            to_snapshot_id=to_id,
            symbol=symbol,
            changes=list(all_changes.values()),
        )

    def _flatten(self, semantic: DecisionSemantic) -> dict:
        result = {}

        result["symbol"] = semantic.symbol
        result["name"] = semantic.name
        result["semantic_version"] = semantic.semantic_version
        result["generated_at"] = semantic.generated_at
        result["confidence_score"] = semantic.confidence_score
        result["action"] = semantic.action
        result["action_label"] = semantic.action_label
        result["summary"] = semantic.summary

        result["signal.direction"] = semantic.signal.direction
        result["signal.direction_label"] = semantic.signal.direction_label
        result["signal.strength"] = semantic.signal.strength
        result["signal.base_confidence"] = semantic.signal.base_confidence

        for i, f in enumerate(semantic.factors):
            result[f"factors.{i}.name"] = f.name
            result[f"factors.{i}.label"] = f.label
            result[f"factors.{i}.value"] = f.value
            result[f"factors.{i}.weight"] = f.weight
            result[f"factors.{i}.contribution"] = f.contribution
            result[f"factors.{i}.is_bullish"] = f.is_bullish
            result[f"factors.{i}.assessment"] = f.assessment

        if semantic.risk:
            result["risk.overall_level"] = semantic.risk.overall_level
            result["risk.drawdown_risk"] = semantic.risk.drawdown_risk
            result["risk.volatility_risk"] = semantic.risk.volatility_risk
            result["risk.correlation_risk"] = semantic.risk.correlation_risk
            result["risk.scenario_vulnerability"] = semantic.risk.scenario_vulnerability
            for i, w in enumerate(semantic.risk.warnings):
                result[f"risk.warnings.{i}"] = w
        else:
            result["risk"] = None

        if semantic.scenario:
            result["scenario.stability_score"] = semantic.scenario.stability_score
            result["scenario.worst_case_score_change"] = semantic.scenario.worst_case_score_change
            result["scenario.state_change_count"] = semantic.scenario.state_change_count
            for i, entry in enumerate(semantic.scenario.entries):
                result[f"scenario.entries.{i}"] = json.dumps(entry, sort_keys=True)
        else:
            result["scenario"] = None

        if semantic.execution:
            result["execution.feasibility"] = semantic.execution.feasibility
            result["execution.estimated_slippage_bps"] = semantic.execution.estimated_slippage_bps
            result["execution.estimated_fill_rate"] = semantic.execution.estimated_fill_rate
            result["execution.quality_grade"] = semantic.execution.quality_grade
            for i, w in enumerate(semantic.execution.warnings):
                result[f"execution.warnings.{i}"] = w
        else:
            result["execution"] = None

        if semantic.consistency:
            result["consistency.is_consistent"] = semantic.consistency.is_consistent
            result["consistency.consistency_score"] = semantic.consistency.consistency_score
            for i, c in enumerate(semantic.consistency.contradictions):
                result[f"consistency.contradictions.{i}"] = json.dumps({
                    "contradiction_type": c.contradiction_type,
                    "severity": c.severity,
                    "description": c.description,
                }, sort_keys=True)
        else:
            result["consistency"] = None

        result["generated_at_timestamp"] = semantic.generated_at

        return result

    def _unflatten(self, flat: dict, semantic_version: str) -> DecisionSemantic:
        signal = SignalSemantic(
            direction=flat.get("signal.direction", "NEUTRAL"),
            direction_label=flat.get("signal.direction_label", ""),
            strength=float(flat.get("signal.strength", 0.0)),
            base_confidence=float(flat.get("signal.base_confidence", 0.0)),
        )

        factor_names = set()
        for key in flat:
            if key.startswith("factors.") and ".name" in key:
                idx = key.split(".")[1]
                factor_names.add(idx)

        factors = []
        for idx in sorted(factor_names, key=int):
            factors.append(FactorSemantic(
                name=flat.get(f"factors.{idx}.name", ""),
                label=flat.get(f"factors.{idx}.label", ""),
                value=float(flat.get(f"factors.{idx}.value", 0.0)),
                weight=float(flat.get(f"factors.{idx}.weight", 0.0)),
                contribution=float(flat.get(f"factors.{idx}.contribution", 0.0)),
                is_bullish=flat.get(f"factors.{idx}.is_bullish", False) in (True, "True"),
                assessment=flat.get(f"factors.{idx}.assessment", ""),
            ))

        risk = None
        if flat.get("risk") is not None or "risk.overall_level" in flat:
            warnings = []
            i = 0
            while f"risk.warnings.{i}" in flat:
                warnings.append(flat[f"risk.warnings.{i}"])
                i += 1
            risk = RiskSemantic(
                overall_level=flat.get("risk.overall_level", "MODERATE"),
                drawdown_risk=float(flat.get("risk.drawdown_risk", 0.0)),
                volatility_risk=float(flat.get("risk.volatility_risk", 0.0)),
                correlation_risk=float(flat.get("risk.correlation_risk", 0.0)),
                scenario_vulnerability=float(flat.get("risk.scenario_vulnerability", 0.0)),
                warnings=warnings,
            )

        scenario = None
        if flat.get("scenario") is not None or "scenario.stability_score" in flat:
            entries = []
            i = 0
            while f"scenario.entries.{i}" in flat:
                entries.append(json.loads(flat[f"scenario.entries.{i}"]))
                i += 1
            scenario = ScenarioSemantic(
                stability_score=float(flat.get("scenario.stability_score", 0.0)),
                worst_case_score_change=float(flat.get("scenario.worst_case_score_change", 0.0)),
                state_change_count=int(flat.get("scenario.state_change_count", 0)),
                entries=entries,
            )

        execution = None
        if flat.get("execution") is not None or "execution.feasibility" in flat:
            exec_warnings = []
            i = 0
            while f"execution.warnings.{i}" in flat:
                exec_warnings.append(flat[f"execution.warnings.{i}"])
                i += 1
            execution = ExecutionSemantic(
                feasibility=float(flat.get("execution.feasibility", 0.0)),
                estimated_slippage_bps=float(flat.get("execution.estimated_slippage_bps", 0.0)),
                estimated_fill_rate=float(flat.get("execution.estimated_fill_rate", 0.0)),
                quality_grade=flat.get("execution.quality_grade", "C"),
                warnings=exec_warnings,
            )

        consistency = None
        if flat.get("consistency") is not None or "consistency.is_consistent" in flat:
            contradictions = []
            i = 0
            while f"consistency.contradictions.{i}" in flat:
                cd = json.loads(flat[f"consistency.contradictions.{i}"])
                contradictions.append(ContradictionEntry(
                    contradiction_type=cd["contradiction_type"],
                    severity=cd["severity"],
                    description=cd["description"],
                ))
                i += 1
            consistency = ConsistencyReport(
                is_consistent=flat.get("consistency.is_consistent", True) in (True, "True"),
                contradictions=contradictions,
                consistency_score=float(flat.get("consistency.consistency_score", 1.0)),
            )

        generated_at = flat.get("generated_at_timestamp", flat.get("generated_at", ""))

        return DecisionSemantic(
            symbol=flat.get("symbol", ""),
            name=flat.get("name", ""),
            signal=signal,
            factors=factors,
            risk=risk,
            scenario=scenario,
            execution=execution,
            confidence_score=float(flat.get("confidence_score", 0.5)),
            consistency=consistency,
            action=flat.get("action", "HOLD"),
            action_label=flat.get("action_label", ""),
            summary=flat.get("summary", ""),
            semantic_version=semantic_version,
            generated_at=generated_at,
        )

    def _values_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if isinstance(a, float) and isinstance(b, float):
            return abs(a - b) < _FLOAT_TOLERANCE
        if isinstance(a, bool) and isinstance(b, bool):
            return a == b
        if isinstance(a, bool) or isinstance(b, bool):
            return False
        return a == b
