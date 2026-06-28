from dataclasses import dataclass


@dataclass
class SemanticVersion:
    major: int
    minor: int
    patch: int

    def to_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))

    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        return self.major == other.major and self.minor == other.minor


SEMVER_1_0_0 = SemanticVersion(major=1, minor=0, patch=0)
SEMVER_1_1_0 = SemanticVersion(major=1, minor=1, patch=0)
SEMVER_2_0_0 = SemanticVersion(major=2, minor=0, patch=0)

CURRENT_VERSION = SEMVER_1_0_0
SUPPORTED_VERSIONS = [SEMVER_1_0_0, SEMVER_1_1_0, SEMVER_2_0_0]
FROZEN_VERSIONS = {SEMVER_1_0_0}

DEFAULT_SEMANTIC_VERSION = CURRENT_VERSION.to_string()


class SemanticRegistry:

    def __init__(self):
        self._current = CURRENT_VERSION
        self._supported = list(SUPPORTED_VERSIONS)
        self._frozen = set(FROZEN_VERSIONS)

    @property
    def current_version(self) -> str:
        return self._current.to_string()

    @property
    def current_semver(self) -> SemanticVersion:
        return self._current

    @property
    def supported_versions(self) -> list[str]:
        return [v.to_string() for v in self._supported]

    @property
    def frozen_versions(self) -> list[str]:
        return [v.to_string() for v in self._frozen]

    def is_version_supported(self, version_str: str) -> bool:
        parts = version_str.split(".")
        if len(parts) != 3:
            return False
        try:
            version = SemanticVersion(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2]),
            )
        except (ValueError, TypeError):
            return False
        return any(version.is_compatible_with(v) for v in self._supported)

    def register_version(self, version: SemanticVersion):
        if version not in self._supported:
            self._supported.append(version)

    def check_compatibility(self, schema_version: str) -> bool:
        if schema_version == self.current_version:
            return True
        return self.is_version_supported(schema_version)

    def is_frozen(self, version_str: str) -> bool:
        parts = version_str.split(".")
        if len(parts) != 3:
            return False
        try:
            version = SemanticVersion(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2]),
            )
        except (ValueError, TypeError):
            return False
        return version in self._frozen

    def freeze_version(self, version: SemanticVersion) -> None:
        self._frozen.add(version)
