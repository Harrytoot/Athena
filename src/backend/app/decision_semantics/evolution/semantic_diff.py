import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from app.decision_semantics.schema import DecisionSemantic


class DiffType(Enum):
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_CHANGED = "field_changed"
    FIELD_UNCHANGED = "field_unchanged"
    VERSION_CHANGE = "version_change"


@dataclass
class FieldChange:
    field_path: str
    diff_type: DiffType
    old_value: object | None = None
    new_value: object | None = None
    description: str = ""


@dataclass
class SemanticDiffReport:
    from_version: str
    to_version: str
    symbol: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    changes: list[FieldChange] = field(default_factory=list)
    diff_id: str = ""
    is_structural_only: bool = False
    summary: str = ""

    def __post_init__(self):
        if not self.diff_id:
            self.diff_id = self._compute_diff_id()

    def _compute_diff_id(self) -> str:
        payload = {
            "symbol": self.symbol,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "changes": [
                {
                    "field_path": c.field_path,
                    "diff_type": c.diff_type.value,
                    "description": c.description,
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
    def added_fields(self) -> list[str]:
        return [
            c.field_path
            for c in self.changes
            if c.diff_type == DiffType.FIELD_ADDED
        ]

    @property
    def removed_fields(self) -> list[str]:
        return [
            c.field_path
            for c in self.changes
            if c.diff_type == DiffType.FIELD_REMOVED
        ]

    @property
    def changed_fields(self) -> list[str]:
        return [
            c.field_path
            for c in self.changes
            if c.diff_type == DiffType.FIELD_CHANGED
        ]

    @property
    def has_breaking_changes(self) -> bool:
        return any(
            c.diff_type == DiffType.FIELD_REMOVED
            and not c.field_path.startswith("ext_")
            for c in self.changes
        )


_STRUCTURAL_FIELDS = {
    "semantic_version",
    "decision_id",
    "strategy_id",
    "source_pipeline",
    "tags",
    "narrative",
}


class SemanticDiff:

    _FLOAT_TOLERANCE = 1e-6

    def diff(
        self,
        older: DecisionSemantic,
        newer: DecisionSemantic,
    ) -> SemanticDiffReport:
        older_dict = self._to_flattened(older)
        newer_dict = self._to_flattened(newer)

        changes: list[FieldChange] = []

        older_ext = getattr(older, "strategy_id", None)
        newer_ext = getattr(newer, "strategy_id", None)
        if older_ext is None and newer_ext is not None:
            changes.append(FieldChange(
                field_path="strategy_id",
                diff_type=DiffType.FIELD_ADDED,
                old_value=None,
                new_value=newer_ext,
                description="strategy_id added as evolution field",
            ))
        elif older_ext is not None and newer_ext is None:
            changes.append(FieldChange(
                field_path="strategy_id",
                diff_type=DiffType.FIELD_REMOVED,
                old_value=older_ext,
                new_value=None,
                description="strategy_id removed",
            ))
        elif older_ext != newer_ext:
            changes.append(FieldChange(
                field_path="strategy_id",
                diff_type=DiffType.FIELD_CHANGED,
                old_value=older_ext,
                new_value=newer_ext,
                description="strategy_id value changed",
            ))

        older_sp = getattr(older, "source_pipeline", None)
        newer_sp = getattr(newer, "source_pipeline", None)
        if older_sp is None and newer_sp is not None:
            changes.append(FieldChange(
                field_path="source_pipeline",
                diff_type=DiffType.FIELD_ADDED,
                old_value=None,
                new_value=newer_sp,
                description="source_pipeline added as evolution field",
            ))
        elif older_sp is not None and newer_sp is None:
            changes.append(FieldChange(
                field_path="source_pipeline",
                diff_type=DiffType.FIELD_REMOVED,
                old_value=older_sp,
                new_value=None,
                description="source_pipeline removed",
            ))
        elif older_sp != newer_sp:
            changes.append(FieldChange(
                field_path="source_pipeline",
                diff_type=DiffType.FIELD_CHANGED,
                old_value=older_sp,
                new_value=newer_sp,
                description="source_pipeline value changed",
            ))

        older_did = getattr(older, "decision_id", None)
        newer_did = getattr(newer, "decision_id", None)
        if older_did is None and newer_did is not None:
            changes.append(FieldChange(
                field_path="decision_id",
                diff_type=DiffType.FIELD_ADDED,
                old_value=None,
                new_value=newer_did,
                description="decision_id added as evolution field",
            ))
        elif older_did is not None and newer_did is None:
            changes.append(FieldChange(
                field_path="decision_id",
                diff_type=DiffType.FIELD_REMOVED,
                old_value=older_did,
                new_value=None,
                description="decision_id removed",
            ))
        elif older_did != newer_did:
            changes.append(FieldChange(
                field_path="decision_id",
                diff_type=DiffType.FIELD_CHANGED,
                old_value=older_did,
                new_value=newer_did,
                description="decision_id value changed",
            ))

        older_tags = getattr(older, "tags", [])
        newer_tags = getattr(newer, "tags", [])
        if older_tags != newer_tags:
            if older_tags is None or len(older_tags) == 0:
                changes.append(FieldChange(
                    field_path="tags",
                    diff_type=DiffType.FIELD_ADDED,
                    old_value=older_tags,
                    new_value=newer_tags,
                    description="tags added as evolution field",
                ))
            elif newer_tags is None or len(newer_tags) == 0:
                changes.append(FieldChange(
                    field_path="tags",
                    diff_type=DiffType.FIELD_REMOVED,
                    old_value=older_tags,
                    new_value=newer_tags,
                    description="tags removed",
                ))
            else:
                changes.append(FieldChange(
                    field_path="tags",
                    diff_type=DiffType.FIELD_CHANGED,
                    old_value=older_tags,
                    new_value=newer_tags,
                    description="tags value changed",
                ))

        older_narrative = getattr(older, "narrative", None)
        newer_narrative = getattr(newer, "narrative", None)
        if older_narrative is not None or newer_narrative is not None:
            if older_narrative is None and newer_narrative is not None:
                changes.append(FieldChange(
                    field_path="narrative",
                    diff_type=DiffType.FIELD_ADDED,
                    old_value=None,
                    new_value=newer_narrative,
                    description="narrative field added (v2.0 migration)",
                ))
            elif older_narrative is not None and newer_narrative is None:
                changes.append(FieldChange(
                    field_path="narrative",
                    diff_type=DiffType.FIELD_REMOVED,
                    old_value=older_narrative,
                    new_value=None,
                    description="narrative field removed",
                ))
            elif older_narrative != newer_narrative:
                changes.append(FieldChange(
                    field_path="narrative",
                    diff_type=DiffType.FIELD_CHANGED,
                    old_value=older_narrative,
                    new_value=newer_narrative,
                    description="narrative value changed",
                ))

        if older.summary != newer.summary:
            summary_changed = False
            for c in changes:
                if c.field_path == "narrative" and c.diff_type == DiffType.FIELD_CHANGED:
                    summary_changed = True
                    break
            if not summary_changed:
                changes.append(FieldChange(
                    field_path="summary",
                    diff_type=DiffType.FIELD_CHANGED,
                    old_value=older.summary,
                    new_value=newer.summary,
                    description="summary value changed",
                ))

        common_keys = set(older_dict.keys()) & set(newer_dict.keys())
        for key in sorted(common_keys):
            old_val = older_dict[key]
            new_val = newer_dict[key]
            if not self._values_equal(old_val, new_val):
                changes.append(FieldChange(
                    field_path=key,
                    diff_type=DiffType.FIELD_CHANGED,
                    old_value=old_val,
                    new_value=new_val,
                    description=f"{key} changed: {old_val} → {new_val}",
                ))

        only_in_older = set(older_dict.keys()) - set(newer_dict.keys())
        for key in sorted(only_in_older):
            changes.append(FieldChange(
                field_path=key,
                diff_type=DiffType.FIELD_REMOVED,
                old_value=older_dict[key],
                new_value=None,
                description=f"{key} removed",
            ))

        only_in_newer = set(newer_dict.keys()) - set(older_dict.keys())
        for key in sorted(only_in_newer):
            changes.append(FieldChange(
                field_path=key,
                diff_type=DiffType.FIELD_ADDED,
                old_value=None,
                new_value=newer_dict[key],
                description=f"{key} added",
            ))

        is_structural = all(
            c.field_path in _STRUCTURAL_FIELDS or c.field_path == "narrative"
            for c in changes
        ) and len(changes) > 0

        return SemanticDiffReport(
            from_version=older.semantic_version,
            to_version=newer.semantic_version,
            symbol=older.symbol,
            changes=changes,
            is_structural_only=is_structural,
            summary=self._build_summary(changes, is_structural),
        )

    def _to_flattened(self, semantic: DecisionSemantic) -> dict:
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
            result["risk.warnings_count"] = len(semantic.risk.warnings)
        else:
            result["risk"] = None

        if semantic.scenario:
            result["scenario.stability_score"] = semantic.scenario.stability_score
            result["scenario.worst_case_score_change"] = semantic.scenario.worst_case_score_change
            result["scenario.state_change_count"] = semantic.scenario.state_change_count
        else:
            result["scenario"] = None

        if semantic.execution:
            result["execution.feasibility"] = semantic.execution.feasibility
            result["execution.quality_grade"] = semantic.execution.quality_grade
        else:
            result["execution"] = None

        if semantic.consistency:
            result["consistency.is_consistent"] = semantic.consistency.is_consistent
            result["consistency.consistency_score"] = semantic.consistency.consistency_score
        else:
            result["consistency"] = None

        return result

    def _values_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if isinstance(a, float) and isinstance(b, float):
            return abs(a - b) < self._FLOAT_TOLERANCE
        if isinstance(a, list) and isinstance(b, list):
            return a == b
        return a == b

    def _build_summary(
        self, changes: list[FieldChange], is_structural: bool
    ) -> str:
        if not changes:
            return "No differences detected"

        added = 0
        removed = 0
        changed = 0

        for c in changes:
            if c.diff_type == DiffType.FIELD_ADDED:
                added += 1
            elif c.diff_type == DiffType.FIELD_REMOVED:
                removed += 1
            elif c.diff_type == DiffType.FIELD_CHANGED:
                changed += 1

        parts = []
        if added:
            parts.append(f"{added} field(s) added")
        if removed:
            parts.append(f"{removed} field(s) removed")
        if changed:
            parts.append(f"{changed} field(s) changed")

        base = ", ".join(parts) if parts else "No changes"
        if is_structural:
            base += " (structural only)"
        return base
