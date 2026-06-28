import pytest

from app.decision_semantics.evolution.version_manager import (
    EvolutionVersionManager,
    EvolutionKind,
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
)
from app.decision_semantics.registry import SemanticRegistry


class TestEvolutionVersionManager:

    def setup_method(self):
        self._manager = EvolutionVersionManager()

    def test_all_versions_registered(self):
        versions = self._manager.all_versions()
        assert SCHEMA_V1_0 in versions
        assert SCHEMA_V1_1 in versions
        assert SCHEMA_V2_0 in versions
        assert len(versions) == 3

    def test_v1_0_is_frozen(self):
        assert self._manager.is_frozen(SCHEMA_V1_0)
        assert not self._manager.is_frozen(SCHEMA_V1_1)
        assert not self._manager.is_frozen(SCHEMA_V2_0)

    def test_v1_0_to_v1_1_additive_upgrade(self):
        path = self._manager.get_upgrade_path(SCHEMA_V1_0, SCHEMA_V1_1)
        assert path is not None
        assert path.is_additive is True
        assert path.is_breaking is False

    def test_v1_1_to_v2_0_restructure_upgrade(self):
        path = self._manager.get_upgrade_path(SCHEMA_V1_1, SCHEMA_V2_0)
        assert path is not None
        assert path.is_breaking is True

    def test_v1_0_to_v2_0_transitive_upgrade(self):
        path = self._manager.get_upgrade_path(SCHEMA_V1_0, SCHEMA_V2_0)
        assert path is not None
        assert len(path.rules) == 5

    def test_v1_1_to_v1_0_downgrade(self):
        path = self._manager.get_downgrade_path(SCHEMA_V1_1, SCHEMA_V1_0)
        assert path is not None
        assert len(path.rules) == 2

    def test_v2_0_to_v1_1_downgrade(self):
        path = self._manager.get_downgrade_path(SCHEMA_V2_0, SCHEMA_V1_1)
        assert path is not None
        assert len(path.rules) == 3

    def test_v2_0_to_v1_0_downgrade(self):
        path = self._manager.get_downgrade_path(SCHEMA_V2_0, SCHEMA_V1_0)
        assert path is not None
        assert len(path.rules) == 5

    def test_no_upgrade_same_version(self):
        path = self._manager.get_upgrade_path(SCHEMA_V1_0, SCHEMA_V1_0)
        assert path is None

    def test_no_downgrade_forward(self):
        path = self._manager.get_downgrade_path(SCHEMA_V1_0, SCHEMA_V1_1)
        assert path is None

    def test_is_upgrade_possible(self):
        assert self._manager.is_upgrade_possible(SCHEMA_V1_0, SCHEMA_V1_1)
        assert self._manager.is_upgrade_possible(SCHEMA_V1_1, SCHEMA_V2_0)
        assert self._manager.is_upgrade_possible(SCHEMA_V1_0, SCHEMA_V2_0)

    def test_is_downgrade_possible(self):
        assert self._manager.is_downgrade_possible(SCHEMA_V2_0, SCHEMA_V1_0)
        assert self._manager.is_downgrade_possible(SCHEMA_V2_0, SCHEMA_V1_1)
        assert self._manager.is_downgrade_possible(SCHEMA_V1_1, SCHEMA_V1_0)

    def test_backward_compatible_check(self):
        assert self._manager.is_backward_compatible(SCHEMA_V1_1, SCHEMA_V1_0)

    def test_not_backward_compatible_when_restructure(self):
        assert not self._manager.is_backward_compatible(SCHEMA_V2_0, SCHEMA_V1_0)
        assert not self._manager.is_backward_compatible(SCHEMA_V2_0, SCHEMA_V1_1)


class TestSemanticRegistryEvolution:

    def setup_method(self):
        self._registry = SemanticRegistry()

    def test_current_version_is_1_0_0(self):
        assert self._registry.current_version == "1.0.0"

    def test_all_versions_supported(self):
        versions = self._registry.supported_versions
        assert "1.0.0" in versions
        assert "1.1.0" in versions
        assert "2.0.0" in versions

    def test_v1_0_is_frozen(self):
        assert self._registry.is_frozen("1.0.0")
        assert not self._registry.is_frozen("1.1.0")
        assert not self._registry.is_frozen("2.0.0")

    def test_v1_1_compatible_with_v1_0(self):
        assert self._registry.is_version_supported("1.1.0")
        assert self._registry.check_compatibility("1.0.0")

    def test_v2_0_is_supported_in_registry(self):
        assert "2.0.0" in self._registry.supported_versions

    def test_frozen_versions_list(self):
        frozen = self._registry.frozen_versions
        assert "1.0.0" in frozen
        assert "1.1.0" not in frozen

    def test_register_new_version(self):
        from app.decision_semantics.registry import SemanticVersion
        new_version = SemanticVersion(major=3, minor=0, patch=0)
        self._registry.register_version(new_version)
        assert "3.0.0" in self._registry.supported_versions

    def test_freeze_version(self):
        from app.decision_semantics.registry import SemanticVersion
        v = SemanticVersion(major=1, minor=1, patch=0)
        self._registry.freeze_version(v)
        assert self._registry.is_frozen("1.1.0")
