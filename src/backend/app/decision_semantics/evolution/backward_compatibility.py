from dataclasses import dataclass, field

from app.decision_semantics.schema import DecisionSemantic
from app.decision_semantics.evolution.version_manager import (
    EvolutionVersionManager,
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
)
from app.decision_semantics.evolution.schema_evolver import SchemaEvolver


@dataclass
class DowngradeMapping:
    original_version: str
    target_version: str
    field_mappings: dict[str, str] = field(default_factory=dict)
    dropped_fields: list[str] = field(default_factory=list)
    default_values: dict[str, object] = field(default_factory=dict)


_DEFAULT_DOWNGRADE_MAPPINGS: dict[tuple[str, str], DowngradeMapping] = {
    (SCHEMA_V1_1, SCHEMA_V1_0): DowngradeMapping(
        original_version=SCHEMA_V1_1,
        target_version=SCHEMA_V1_0,
        dropped_fields=["strategy_id", "source_pipeline"],
    ),
    (SCHEMA_V2_0, SCHEMA_V1_1): DowngradeMapping(
        original_version=SCHEMA_V2_0,
        target_version=SCHEMA_V1_1,
        field_mappings={"narrative": "summary"},
        dropped_fields=["decision_id", "tags"],
        default_values={"strategy_id": "", "source_pipeline": ""},
    ),
    (SCHEMA_V2_0, SCHEMA_V1_0): DowngradeMapping(
        original_version=SCHEMA_V2_0,
        target_version=SCHEMA_V1_0,
        field_mappings={"narrative": "summary"},
        dropped_fields=["decision_id", "tags", "strategy_id", "source_pipeline"],
    ),
}


class BackwardCompatibility:

    def __init__(self):
        self._version_manager = EvolutionVersionManager()
        self._evolver = SchemaEvolver()
        self._mappings: dict[tuple[str, str], DowngradeMapping] = dict(
            _DEFAULT_DOWNGRADE_MAPPINGS
        )

    def can_serve(
        self,
        semantic: DecisionSemantic,
        consumer_version: str,
    ) -> bool:
        if semantic.semantic_version == consumer_version:
            return True
        return self._version_manager.is_downgrade_possible(
            semantic.semantic_version, consumer_version
        )

    def serve_to_consumer(
        self,
        semantic: DecisionSemantic,
        consumer_version: str,
    ) -> DecisionSemantic:
        if semantic.semantic_version == consumer_version:
            return semantic
        result = self._evolver.downgrade(semantic, consumer_version)
        return result.result

    def validate_no_breaking_changes(
        self,
        old_semantic: DecisionSemantic,
        new_semantic: DecisionSemantic,
    ) -> list[str]:
        issues: list[str] = []

        old_keys = self._core_field_keys(old_semantic)
        new_keys = self._core_field_keys(new_semantic)

        for key in old_keys:
            if key not in new_keys:
                issues.append(
                    f"BREAKING: Core field '{key}' missing in new version"
                )

        for key in old_keys:
            old_val = getattr(old_semantic, key, None)
            new_val = getattr(new_semantic, key, None)
            if type(old_val) is not type(new_val) and old_val is not None:
                issues.append(
                    f"BREAKING: Core field '{key}' type changed from "
                    f"{type(old_val).__name__} to {type(new_val).__name__}"
                )

        return issues

    def get_mapping(self, from_ver: str, to_ver: str) -> DowngradeMapping | None:
        return self._mappings.get((from_ver, to_ver))

    def register_mapping(self, from_ver: str, to_ver: str, mapping: DowngradeMapping) -> None:
        self._mappings[(from_ver, to_ver)] = mapping

    def _core_field_keys(self, semantic: DecisionSemantic) -> list[str]:
        return [
            "symbol",
            "name",
            "signal",
            "factors",
            "risk",
            "scenario",
            "execution",
            "confidence_score",
            "consistency",
            "action",
            "action_label",
            "summary",
            "semantic_version",
            "generated_at",
        ]


def is_backward_compatible(
    newer: DecisionSemantic,
    older_version: str,
) -> bool:
    compat = BackwardCompatibility()
    return compat.can_serve(newer, older_version)
