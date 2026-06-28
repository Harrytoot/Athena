import pytest

from app.decision_semantics.schema import (
    FactorSemantic,
    SignalSemantic,
    ScenarioSemantic,
)
from app.decision_semantics.validator import SemanticValidator


class TestScenarioConsistencyValidation:

    def setup_method(self):
        self._validator = SemanticValidator()

    def test_stable_scenario_no_contradiction(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.7,
            base_confidence=75.0,
        )
        scenario = ScenarioSemantic(
            stability_score=0.95,
            worst_case_score_change=-5.0,
            state_change_count=0,
            entries=[{"name": "test", "score_change": -5.0, "state_changed": False}],
        )
        report = self._validator.validate(signal=signal, scenario=scenario)

        assert report.is_consistent

    def test_unstable_scenario_contradiction(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.7,
            base_confidence=75.0,
        )
        scenario = ScenarioSemantic(
            stability_score=0.2,
            worst_case_score_change=-50.0,
            state_change_count=7,
            entries=[
                {"name": "test", "score_change": -50.0, "state_changed": True},
            ],
        )
        report = self._validator.validate(signal=signal, scenario=scenario)

        assert not report.is_consistent
        assert any(
            "情景" in c.description or "stability" in c.description.lower()
            for c in report.contradictions
        )

    def test_majority_scenario_state_change(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.6,
            base_confidence=65.0,
        )
        scenario = ScenarioSemantic(
            stability_score=0.5,
            worst_case_score_change=-20.0,
            state_change_count=5,
            entries=[
                {"name": "s1", "state_changed": True},
                {"name": "s2", "state_changed": True},
                {"name": "s3", "state_changed": True},
                {"name": "s4", "state_changed": True},
                {"name": "s5", "state_changed": True},
                {"name": "s6", "state_changed": False},
                {"name": "s7", "state_changed": False},
                {"name": "s8", "state_changed": False},
            ],
        )
        report = self._validator.validate(signal=signal, scenario=scenario)

        assert not report.is_consistent
        assert any(
            "多数情景" in c.description
            for c in report.contradictions
        )

    def test_extreme_score_change_contradiction(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.5,
            base_confidence=55.0,
        )
        scenario = ScenarioSemantic(
            stability_score=0.7,
            worst_case_score_change=-35.0,
            state_change_count=1,
            entries=[
                {"name": "test", "score_change": -35.0, "state_changed": True},
            ],
        )
        report = self._validator.validate(signal=signal, scenario=scenario)

        assert not report.is_consistent
        assert any(
            "评分剧烈变化" in c.description
            for c in report.contradictions
        )

    def test_neutral_signal_stable_scenario(self):
        signal = SignalSemantic(
            direction="NEUTRAL",
            direction_label="中性",
            strength=0.1,
            base_confidence=50.0,
        )
        scenario = ScenarioSemantic(
            stability_score=0.95,
            worst_case_score_change=-3.0,
            state_change_count=0,
        )
        report = self._validator.validate(signal=signal, scenario=scenario)

        assert report.is_consistent


class TestFactorConflictDetection:

    def setup_method(self):
        self._validator = SemanticValidator()

    def test_factor_bull_bear_conflict(self):
        factors = [
            FactorSemantic(name="trend", label="趋势", value=90.0, weight=0.30, contribution=27.0, is_bullish=True, assessment="极强"),
            FactorSemantic(name="liquidity", label="流动性", value=10.0, weight=0.25, contribution=2.5, is_bullish=False, assessment="极弱"),
        ]
        report = self._validator.validate(
            signal=SignalSemantic(direction="NEUTRAL", direction_label="中性", strength=0.0, base_confidence=50.0),
            factors=factors,
        )

        assert not report.is_consistent
        assert any(
            c.contradiction_type == "factor_conflict"
            for c in report.contradictions
        )

    def test_extreme_polarization(self):
        factors = [
            FactorSemantic(name="trend", label="趋势", value=95.0, weight=0.30, contribution=28.5, is_bullish=True, assessment="极强"),
            FactorSemantic(name="sentiment", label="情绪", value=5.0, weight=0.10, contribution=0.5, is_bullish=False, assessment="极弱"),
        ]
        report = self._validator.validate(
            signal=SignalSemantic(direction="NEUTRAL", direction_label="中性", strength=0.0, base_confidence=50.0),
            factors=factors,
        )

        assert not report.is_consistent
        assert any(
            "两极化" in c.description
            for c in report.contradictions
        )

    def test_factor_vs_signal_direction_contradiction(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.6,
            base_confidence=65.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=80.0, weight=0.30, contribution=24.0, is_bullish=True, assessment="强"),
            FactorSemantic(name="liquidity", label="流动性", value=20.0, weight=0.25, contribution=5.0, is_bullish=False, assessment="弱"),
            FactorSemantic(name="breadth", label="宽度", value=85.0, weight=0.20, contribution=17.0, is_bullish=True, assessment="强"),
            FactorSemantic(name="volatility", label="波动率", value=15.0, weight=0.15, contribution=2.25, is_bullish=False, assessment="弱"),
            FactorSemantic(name="sentiment", label="情绪", value=10.0, weight=0.10, contribution=1.0, is_bullish=False, assessment="弱"),
        ]
        report = self._validator.validate(signal=signal, factors=factors)

        assert not report.is_consistent
        assert any(
            c.contradiction_type == "factor_conflict" and "多数因子" in c.description
            for c in report.contradictions
        )

    def test_no_conflict_all_aligned(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.8,
            base_confidence=85.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
            FactorSemantic(name="liquidity", label="流动性", value=75.0, weight=0.25, contribution=18.75, is_bullish=True, assessment="强"),
            FactorSemantic(name="breadth", label="宽度", value=70.0, weight=0.20, contribution=14.0, is_bullish=True, assessment="偏强"),
            FactorSemantic(name="volatility", label="波动率", value=65.0, weight=0.15, contribution=9.75, is_bullish=True, assessment="偏强"),
            FactorSemantic(name="sentiment", label="情绪", value=60.0, weight=0.10, contribution=6.0, is_bullish=True, assessment="偏强"),
        ]
        report = self._validator.validate(signal=signal, factors=factors)

        assert report.is_consistent
        assert report.consistency_score == 1.0

    def test_important_factor_vs_signal(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.6,
            base_confidence=65.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
            FactorSemantic(name="liquidity", label="流动性", value=20.0, weight=0.25, contribution=5.0, is_bullish=False, assessment="弱"),
            FactorSemantic(name="breadth", label="宽度", value=55.0, weight=0.20, contribution=11.0, is_bullish=True, assessment="中性"),
            FactorSemantic(name="volatility", label="波动率", value=60.0, weight=0.15, contribution=9.0, is_bullish=True, assessment="偏强"),
            FactorSemantic(name="sentiment", label="情绪", value=55.0, weight=0.10, contribution=5.5, is_bullish=True, assessment="中性"),
        ]
        report = self._validator.validate(signal=signal, factors=factors)

        assert any(
            "重要因子" in c.description
            for c in report.contradictions
        )
