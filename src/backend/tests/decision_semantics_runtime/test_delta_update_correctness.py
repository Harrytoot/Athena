import pytest

from app.decision_semantics.runtime.semantic_delta_engine import (
    SemanticDeltaEngine,
    SemanticDelta,
    DeltaFieldChange,
    DeltaFieldChangeType,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)


def _make_base_semantic() -> DecisionSemantic:
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
            warnings=["波动率偏高"],
        ),
        scenario=ScenarioSemantic(
            stability_score=0.75,
            worst_case_score_change=-18.0,
            state_change_count=1,
            entries=[{"name": "crash", "impact": "medium"}],
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action="APPROVE",
        action_label="执行买入",
        summary="基于趋势和流动性因子的看多信号",
        semantic_version="1.0.0",
    )


class TestDeltaUpdateCorrectness:

    def setup_method(self):
        self._engine = SemanticDeltaEngine()

    def test_compute_delta_no_changes(self):
        base = _make_base_semantic()
        same = _make_base_semantic()

        delta = self._engine.compute_delta(base, same)
        assert delta.is_empty
        assert delta.change_count == 0

    def test_compute_delta_signal_changed(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.signal = SignalSemantic(
            direction="SHORT",
            direction_label="看空",
            strength=0.65,
            base_confidence=70.0,
        )
        modified.action = "REJECT"
        modified.action_label = "清仓"

        delta = self._engine.compute_delta(base, modified)
        assert not delta.is_empty
        assert delta.symbol == "AAPL"

        changed_paths = delta.changed_field_paths()
        assert "signal.direction" in changed_paths
        assert "signal.strength" in changed_paths
        assert "action" in changed_paths

    def test_compute_delta_confidence_changed(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.confidence_score = 0.92

        delta = self._engine.compute_delta(base, modified)
        changed_paths = delta.changed_field_paths()
        assert "confidence_score" in changed_paths

    def test_compute_delta_factor_changed(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.factors[0].value = 75.0
        modified.factors[0].contribution = 22.5
        modified.factors[0].is_bullish = False
        modified.factors[0].assessment = "偏空"

        delta = self._engine.compute_delta(base, modified)
        changed_paths = delta.changed_field_paths()
        assert "factors.0.value" in changed_paths
        assert "factors.0.contribution" in changed_paths
        assert "factors.0.is_bullish" in changed_paths
        assert "factors.0.assessment" in changed_paths

    def test_compute_delta_risk_changed(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.risk.overall_level = "HIGH"
        modified.risk.drawdown_risk = 0.7
        modified.risk.warnings.append("新增流动性风险")

        delta = self._engine.compute_delta(base, modified)
        changed_paths = delta.changed_field_paths()
        assert "risk.overall_level" in changed_paths
        assert "risk.drawdown_risk" in changed_paths
        assert "risk.warnings.1" in delta.added_field_paths() or "risk.warnings.1" in changed_paths

    def test_compute_delta_scenario_changed(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.scenario.stability_score = 0.55
        modified.scenario.state_change_count = 3

        delta = self._engine.compute_delta(base, modified)
        changed_paths = delta.changed_field_paths()
        assert "scenario.stability_score" in changed_paths
        assert "scenario.state_change_count" in changed_paths

    def test_apply_delta_signal_change(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.signal.direction = "NEUTRAL"
        modified.signal.strength = 0.40
        modified.action = "HOLD"

        delta = self._engine.compute_delta(base, modified)
        result = self._engine.apply_delta(base, delta)

        assert result.signal.direction == "NEUTRAL"
        assert result.signal.strength == 0.40
        assert result.action == "HOLD"
        assert result.symbol == "AAPL"
        assert result.factors[0].name == "trend"

    def test_apply_delta_factor_change(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.factors[0].value = 65.0
        modified.factors[0].contribution = 19.5
        modified.factors[0].is_bullish = False
        modified.factors[0].assessment = "偏空"

        delta = self._engine.compute_delta(base, modified)
        result = self._engine.apply_delta(base, delta)

        assert result.factors[0].value == 65.0
        assert result.factors[0].contribution == 19.5
        assert result.factors[0].is_bullish is False
        assert result.factors[0].assessment == "偏空"

    def test_apply_delta_all_fields(self):
        base = _make_base_semantic()
        modified = DecisionSemantic(
            symbol="AAPL",
            name="Apple Inc.",
            signal=SignalSemantic(
                direction="SHORT",
                direction_label="看空",
                strength=0.20,
                base_confidence=90.0,
            ),
            factors=[
                FactorSemantic(
                    name="trend",
                    label="趋势",
                    value=20.0,
                    weight=0.30,
                    contribution=6.0,
                    is_bullish=False,
                    assessment="强看空",
                ),
            ],
            risk=RiskSemantic(
                overall_level="HIGH",
                drawdown_risk=0.8,
                volatility_risk=0.9,
                correlation_risk=0.5,
                scenario_vulnerability=0.7,
                warnings=["极高风险"],
            ),
            confidence_score=0.15,
            consistency=ConsistencyReport(
                is_consistent=True,
                contradictions=[],
                consistency_score=1.0,
            ),
            action="REJECT",
            action_label="清仓",
            summary="风险过高，建议清仓",
            semantic_version="1.0.0",
        )

        delta = self._engine.compute_delta(base, modified)
        result = self._engine.apply_delta(base, delta)

        assert result.signal.direction == "SHORT"
        assert result.signal.strength == 0.20
        assert len(result.factors) == 1
        assert result.factors[0].value == 20.0
        assert result.risk.overall_level == "HIGH"
        assert result.confidence_score == 0.15
        assert result.action == "REJECT"
        assert result.summary == "风险过高，建议清仓"

    def test_is_delta_applicable_true(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.signal.strength = 0.75

        delta = self._engine.compute_delta(base, modified)
        assert self._engine.is_delta_applicable(base, delta)

    def test_is_delta_applicable_false_wrong_symbol(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.signal.strength = 0.75

        delta = self._engine.compute_delta(base, modified)
        delta.symbol = "TSLA"
        assert not self._engine.is_delta_applicable(base, delta)

    def test_empty_delta(self):
        base = _make_base_semantic()
        same = _make_base_semantic()

        delta = self._engine.compute_delta(base, same)
        result = self._engine.apply_delta(base, delta)

        assert result.signal.direction == base.signal.direction
        assert result.confidence_score == base.confidence_score
        assert len(result.factors) == len(base.factors)

    def test_delta_deterministic_id(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.confidence_score = 0.99

        ids = []
        for _ in range(5):
            delta = self._engine.compute_delta(base, modified)
            ids.append(delta.delta_id)

        for i in range(1, len(ids)):
            assert ids[i] == ids[0]

    def test_merge_deltas(self):
        base = _make_base_semantic()

        mod1 = _make_base_semantic()
        mod1.confidence_score = 0.90

        mod2 = _make_base_semantic()
        mod2.signal.strength = 0.95

        delta1 = self._engine.compute_delta(base, mod1)
        delta2 = self._engine.compute_delta(mod1, mod2)

        merged = self._engine.merge_deltas([delta1, delta2])

        changed = merged.changed_field_paths()
        assert "confidence_score" in changed
        assert "signal.strength" in changed

    def test_float_tolerance_no_false_positive(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.confidence_score = base.confidence_score + 1e-7

        delta = self._engine.compute_delta(base, modified)
        assert delta.is_empty

    def test_float_tolerance_detects_real_change(self):
        base = _make_base_semantic()
        modified = _make_base_semantic()
        modified.confidence_score = base.confidence_score + 1e-4

        delta = self._engine.compute_delta(base, modified)
        assert "confidence_score" in delta.changed_field_paths()
