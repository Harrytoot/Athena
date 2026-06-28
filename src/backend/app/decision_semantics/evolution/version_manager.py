from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


SCHEMA_V1_0 = "1.0.0"
SCHEMA_V1_1 = "1.1.0"
SCHEMA_V2_0 = "2.0.0"

ALL_SUPPORTED_VERSIONS = [SCHEMA_V1_0, SCHEMA_V1_1, SCHEMA_V2_0]
FROZEN_VERSIONS = {SCHEMA_V1_0}


class EvolutionKind(Enum):
    ADDITIVE = "additive"
    DEPRECATION = "deprecation"
    RENAME = "rename"
    RESTRUCTURE = "restructure"


@dataclass
class EvolutionRule:
    target_version: str
    kind: EvolutionKind
    field_name: str
    description: str
    transform: Callable[[dict], dict] = field(default=lambda x: x)


@dataclass
class VersionUpgradePath:
    from_version: str
    to_version: str
    rules: list[EvolutionRule] = field(default_factory=list)

    @property
    def is_additive(self) -> bool:
        return all(r.kind == EvolutionKind.ADDITIVE for r in self.rules)

    @property
    def is_breaking(self) -> bool:
        return any(
            r.kind in (EvolutionKind.DEPRECATION, EvolutionKind.RENAME, EvolutionKind.RESTRUCTURE)
            for r in self.rules
        )


@dataclass
class VersionDowngradePath:
    from_version: str
    to_version: str
    rules: list[EvolutionRule] = field(default_factory=list)


class EvolutionVersionManager:
    _upgrade_paths: dict[tuple[str, str], VersionUpgradePath] = {}
    _downgrade_paths: dict[tuple[str, str], VersionDowngradePath] = {}
    _compatibility_matrix: dict[str, set[str]] = {}

    def __init__(self):
        self._register_upgrade_paths()
        self._register_downgrade_paths()
        self._build_compatibility_matrix()

    def get_upgrade_path(self, from_ver: str, to_ver: str) -> VersionUpgradePath | None:
        return self._upgrade_paths.get((from_ver, to_ver))

    def get_downgrade_path(self, from_ver: str, to_ver: str) -> VersionDowngradePath | None:
        return self._downgrade_paths.get((from_ver, to_ver))

    def is_upgrade_possible(self, from_ver: str, to_ver: str) -> bool:
        return (from_ver, to_ver) in self._upgrade_paths

    def is_downgrade_possible(self, from_ver: str, to_ver: str) -> bool:
        return (from_ver, to_ver) in self._downgrade_paths

    def is_backward_compatible(self, from_ver: str, to_ver: str) -> bool:
        path = self.get_downgrade_path(from_ver, to_ver)
        if path is None:
            return False
        return all(
            r.kind == EvolutionKind.ADDITIVE
            for r in path.rules
        )

    def compatible_versions(self, version: str) -> set[str]:
        return self._compatibility_matrix.get(version, set())

    def all_versions(self) -> list[str]:
        return list(ALL_SUPPORTED_VERSIONS)

    def frozen_versions(self) -> set[str]:
        return set(FROZEN_VERSIONS)

    def is_frozen(self, version: str) -> bool:
        return version in FROZEN_VERSIONS

    def _register_upgrade_paths(self):
        self._upgrade_paths[(SCHEMA_V1_0, SCHEMA_V1_1)] = VersionUpgradePath(
            from_version=SCHEMA_V1_0,
            to_version=SCHEMA_V1_1,
            rules=[
                EvolutionRule(
                    target_version=SCHEMA_V1_1,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="strategy_id",
                    description="Add strategy_id field for tracking strategy provenance",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_1,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="source_pipeline",
                    description="Add source_pipeline field for tracking pipeline version",
                ),
            ],
        )

        self._upgrade_paths[(SCHEMA_V1_1, SCHEMA_V2_0)] = VersionUpgradePath(
            from_version=SCHEMA_V1_1,
            to_version=SCHEMA_V2_0,
            rules=[
                EvolutionRule(
                    target_version=SCHEMA_V2_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="decision_id",
                    description="Add decision_id unique identifier for audit trail",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V2_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="tags",
                    description="Add tags field for categorical filtering",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V2_0,
                    kind=EvolutionKind.RENAME,
                    field_name="narrative",
                    description="Rename summary to narrative for richer descriptions",
                ),
            ],
        )

        self._upgrade_paths[(SCHEMA_V1_0, SCHEMA_V2_0)] = VersionUpgradePath(
            from_version=SCHEMA_V1_0,
            to_version=SCHEMA_V2_0,
            rules=(
                self._upgrade_paths[(SCHEMA_V1_0, SCHEMA_V1_1)].rules
                + self._upgrade_paths[(SCHEMA_V1_1, SCHEMA_V2_0)].rules
            ),
        )

    def _register_downgrade_paths(self):
        self._downgrade_paths[(SCHEMA_V1_1, SCHEMA_V1_0)] = VersionDowngradePath(
            from_version=SCHEMA_V1_1,
            to_version=SCHEMA_V1_0,
            rules=[
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="strategy_id",
                    description="Drop strategy_id field",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="source_pipeline",
                    description="Drop source_pipeline field",
                ),
            ],
        )

        self._downgrade_paths[(SCHEMA_V2_0, SCHEMA_V1_1)] = VersionDowngradePath(
            from_version=SCHEMA_V2_0,
            to_version=SCHEMA_V1_1,
            rules=[
                EvolutionRule(
                    target_version=SCHEMA_V1_1,
                    kind=EvolutionKind.RENAME,
                    field_name="summary",
                    description="Map narrative back to summary",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_1,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="decision_id",
                    description="Drop decision_id field",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_1,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="tags",
                    description="Drop tags field",
                ),
            ],
        )

        self._downgrade_paths[(SCHEMA_V2_0, SCHEMA_V1_0)] = VersionDowngradePath(
            from_version=SCHEMA_V2_0,
            to_version=SCHEMA_V1_0,
            rules=[
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.RENAME,
                    field_name="summary",
                    description="Map narrative back to summary",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="strategy_id",
                    description="Drop strategy_id field",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="source_pipeline",
                    description="Drop source_pipeline field",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="decision_id",
                    description="Drop decision_id field",
                ),
                EvolutionRule(
                    target_version=SCHEMA_V1_0,
                    kind=EvolutionKind.ADDITIVE,
                    field_name="tags",
                    description="Drop tags field",
                ),
            ],
        )

    def _build_compatibility_matrix(self):
        for v in ALL_SUPPORTED_VERSIONS:
            self._compatibility_matrix[v] = set()
            self._compatibility_matrix[v].add(v)

        for (from_v, to_v), path in self._downgrade_paths.items():
            self._compatibility_matrix[to_v].add(from_v)
            for entry in self._downgrade_paths.values():
                if entry.from_version == from_v and entry.to_version == to_v:
                    continue
            self._compatibility_matrix[v].update(
                self._compatibility_matrix.get(from_v, set())
            )
            for cv in list(self._compatibility_matrix[from_v]):
                self._compatibility_matrix[cv].add(from_v)

        for v in ALL_SUPPORTED_VERSIONS:
            for other in ALL_SUPPORTED_VERSIONS:
                if v != other and self.is_downgrade_possible(other, v):
                    self._compatibility_matrix[v].add(other)
