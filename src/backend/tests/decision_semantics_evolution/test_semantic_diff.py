import pytest

from app.decision_semantics.evolution.semantic_diff import (
    SemanticDiff,
    SemanticDiffReport,
    FieldChange,
    DiffType,
)
from app.decision_semantics.evolution.schema_evolver import SchemaEvolver
from app.decision_semantics.evolution.version_manager import (
    SCHEMA_V1_0,
    SCHEMA_V1_1,
    SCHEMA_V2_0,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)


def _make_v1_semantic() -> DecisionSemantic:
    return DecisionSemantic(
        symbol="AAPL",
        name="Apple Inc.",
        signal=SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.85,
            base_confidence=82.0,
        ),
        factors=[
            FactorSemantic(
                name="trend",
                label="趋势",
                value=88.0,
                weight=0.30,
                contribution=26.4,
                is_bullish=True,
                assessment="强看多",
            ),
            FactorSemantic(
                name="liquidity",
                label="流动性",
                value=72.0,
                weight=0.25,
                contribution=18.0,
                is_bullish=True,
                assessment="偏多",
            ),
        ],
        risk=RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.35,
        ),
        scenario=ScenarioSemantic(
            stability_score=0.75,
            worst_case_score_change=-18.0,
            state_change_count=1,
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            consistency_score=0.95,
        ),
        action="APPROVE",
        action_label="执行买入",
        summary="基于趋势因子的看多信号",
        semantic_version=SCHEMA_V1_0,
    )


class TestSemanticDiff:

    def setup_method(self):
        self._differ = SemanticDiff()
        self._evolver = SchemaEvolver()

    def test_diff_identical_versions(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()

        report = self._differ.diff(v1, v2)

        assert isinstance(report, SemanticDiffReport)
        assert report.from_version == SCHEMA_V1_0
        assert report.to_version == SCHEMA_V1_0
        assert report.change_count == 0
        assert report.symbol == "AAPL"

    def test_diff_v1_0_to_v1_1(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(v1, strategy_id="s1", source_pipeline="p1")

        report = self._differ.diff(v1, v1_1)

        assert report.from_version == SCHEMA_V1_0
        assert report.to_version == SCHEMA_V1_1
        added = [c for c in report.changes if c.diff_type == DiffType.FIELD_ADDED]
        assert len(added) >= 2

    def test_diff_v1_0_to_v2_0(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, tags=["tag"], narrative="V2 narrative")

        report = self._differ.diff(v1, v2)

        assert report.from_version == SCHEMA_V1_0
        assert report.to_version == SCHEMA_V2_0
        assert report.change_count > 0
        added = report.added_fields
        assert len(added) >= 2

    def test_diff_v1_1_to_v2_0(self):
        v1 = _make_v1_semantic()
        v1_1 = self._evolver.to_v1_1(v1, strategy_id="s1", source_pipeline="p1")
        v2 = self._evolver.to_v2_0(v1_1, tags=["tag"], narrative="V2 narrative")

        report = self._differ.diff(v1_1, v2)

        assert report.from_version == SCHEMA_V1_1
        assert report.to_version == SCHEMA_V2_0

    def test_diff_value_changes(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()
        v2.confidence_score = 0.95
        v2.signal.strength = 0.92

        report = self._differ.diff(v1, v2)

        changed = report.changed_fields
        assert "signal.strength" in changed
        assert "confidence_score" in changed

    def test_diff_report_structure(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1)

        report = self._differ.diff(v1, v2)

        assert report.diff_id != ""
        assert len(report.diff_id) == 16
        assert report.generated_at != ""
        assert report.summary != ""

    def test_diff_id_deterministic(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1)

        ids = []
        for _ in range(3):
            report = self._differ.diff(v1, v2)
            ids.append(report.diff_id)

        assert ids[0] == ids[1] == ids[2]

    def test_diff_detects_risk_removal(self):
        v1 = _make_v1_semantic()

        v_modified = _make_v1_semantic()
        v_modified.risk = None

        report = self._differ.diff(v1, v_modified)

        assert report.change_count > 0

    def test_diff_downgrade_structural_only(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, tags=["tag"])

        report = self._differ.diff(v1, v2)

        assert report.is_structural_only

    def test_diff_empty_no_differences(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()

        report = self._differ.diff(v1, v2)

        assert report.change_count == 0
        assert len(report.added_fields) == 0
        assert len(report.removed_fields) == 0
        assert len(report.changed_fields) == 0
        assert not report.has_breaking_changes
        assert not report.is_structural_only

    def test_diff_version_change_tracked(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1)

        report = self._differ.diff(v1, v2)

        version_changes = [
            c for c in report.changes
            if c.field_path == "semantic_version"
        ]
        if version_changes:
            assert version_changes[0].diff_type == DiffType.FIELD_CHANGED

    def test_diff_factor_multiple_changes(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()
        v2.factors[0].value = 95.0
        v2.factors[1].value = 30.0
        v2.factors[1].is_bullish = False

        report = self._differ.diff(v1, v2)

        changed = report.changed_fields
        assert "factors.0.value" in changed
        assert "factors.1.value" in changed
        assert "factors.1.is_bullish" in changed

    def test_diff_risk_changes(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()
        v2.risk.overall_level = "HIGH"
        v2.risk.drawdown_risk = 0.8

        report = self._differ.diff(v1, v2)

        changed = report.changed_fields
        assert "risk.overall_level" in changed
        assert "risk.drawdown_risk" in changed

    def test_diff_narrative_summary_mapping(self):
        v1 = _make_v1_semantic()
        v2 = self._evolver.to_v2_0(v1, narrative="New narrative text")

        report = self._differ.diff(v1, v2)

        assert report.change_count > 0

    def test_diff_float_tolerance(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()

        v2.confidence_score = v1.confidence_score + 1e-10

        report = self._differ.diff(v1, v2)

        changed = report.changed_fields
        assert "confidence_score" not in changed


class TestSemanticDiffReport:

    def test_report_change_count(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()
        v2.action = "REJECT"

        differ = SemanticDiff()
        report = differ.diff(v1, v2)

        assert report.change_count == 1

    def test_report_has_breaking_changes_false_for_additions(self):
        v1 = _make_v1_semantic()
        evolver = SchemaEvolver()
        v1_1 = evolver.to_v1_1(v1, strategy_id="s1")

        differ = SemanticDiff()
        report = differ.diff(v1, v1_1)

        assert not report.has_breaking_changes

    def test_report_summary_description(self):
        v1 = _make_v1_semantic()
        evolver = SchemaEvolver()
        v2 = evolver.to_v2_0(v1, tags=["a", "b"], narrative="narrative")

        differ = SemanticDiff()
        report = differ.diff(v1, v2)

        assert len(report.summary) > 0
        assert "field(s)" in report.summary.lower()

    def test_report_no_changes_summary(self):
        v1 = _make_v1_semantic()
        v2 = _make_v1_semantic()

        differ = SemanticDiff()
        report = differ.diff(v1, v2)

        assert "No differences" in report.summary
