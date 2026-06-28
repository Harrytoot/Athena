import pytest

from app.decision_semantics.confidence_model import ConfidenceModel
from app.decision_semantics.schema import (
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ExecutionSemantic,
)


class TestConfidenceModel:

    def setup_method(self):
        self._model = ConfidenceModel()

    def test_deterministic_identical_inputs(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.8,
            base_confidence=85.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
            FactorSemantic(name="liquidity", label="流动性", value=75.0, weight=0.25, contribution=18.75, is_bullish=True, assessment="强"),
            FactorSemantic(name="breadth", label="宽度", value=65.0, weight=0.20, contribution=13.0, is_bullish=True, assessment="偏强"),
            FactorSemantic(name="volatility", label="波动率", value=55.0, weight=0.15, contribution=8.25, is_bullish=True, assessment="中性"),
            FactorSemantic(name="sentiment", label="情绪", value=60.0, weight=0.10, contribution=6.0, is_bullish=True, assessment="偏强"),
        ]

        result1 = self._model.compute(signal=signal, factors=factors)
        result2 = self._model.compute(signal=signal, factors=factors)
        result3 = self._model.compute(signal=signal, factors=factors)

        assert result1 == result2 == result3

    def test_confidence_bounds(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.9,
            base_confidence=95.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=98.0, weight=0.30, contribution=29.4, is_bullish=True, assessment="极强"),
        ]
        scenario = ScenarioSemantic(stability_score=0.95, worst_case_score_change=-5.0, state_change_count=0)
        result = self._model.compute(signal=signal, factors=factors, scenario=scenario)

        assert 0.0 <= result <= 1.0

        signal_weak = SignalSemantic(
            direction="SHORT",
            direction_label="看空",
            strength=0.1,
            base_confidence=10.0,
        )
        factors_weak = [
            FactorSemantic(name="trend", label="趋势", value=15.0, weight=0.30, contribution=4.5, is_bullish=False, assessment="极弱"),
        ]
        scenario_weak = ScenarioSemantic(stability_score=0.1, worst_case_score_change=-80.0, state_change_count=7)
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=1.0,
            correlation_risk=1.0,
            scenario_vulnerability=1.0,
            warnings=["高风险"],
        )
        result_weak = self._model.compute(signal=signal_weak, factors=factors_weak, scenario=scenario_weak, risk=risk)

        assert 0.0 <= result_weak <= 1.0

    def test_confidence_with_scenario(self):
        model = ConfidenceModel()
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.7,
            base_confidence=75.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=75.0, weight=0.30, contribution=22.5, is_bullish=True, assessment="偏强"),
            FactorSemantic(name="liquidity", label="流动性", value=70.0, weight=0.25, contribution=17.5, is_bullish=True, assessment="偏强"),
        ]

        stable_scenario = ScenarioSemantic(stability_score=0.95, worst_case_score_change=-3.0, state_change_count=0)
        unstable_scenario = ScenarioSemantic(stability_score=0.2, worst_case_score_change=-45.0, state_change_count=6)

        result_stable = model.compute(signal=signal, factors=factors, scenario=stable_scenario)
        result_unstable = model.compute(signal=signal, factors=factors, scenario=unstable_scenario)

        assert result_stable > result_unstable

    def test_confidence_with_risk_penalty(self):
        model = ConfidenceModel()
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.7,
            base_confidence=75.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=75.0, weight=0.30, contribution=22.5, is_bullish=True, assessment="偏强"),
        ]

        low_risk = RiskSemantic(
            overall_level="LOW",
            drawdown_risk=0.0,
            volatility_risk=0.0,
            correlation_risk=0.0,
            scenario_vulnerability=0.0,
        )
        high_risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=1.0,
            correlation_risk=1.0,
            scenario_vulnerability=1.0,
            warnings=["高风险"],
        )

        result_low = model.compute(signal=signal, factors=factors, risk=low_risk)
        result_high = model.compute(signal=signal, factors=factors, risk=high_risk)

        assert result_low > result_high

    def test_factor_consistency_scoring(self):
        model = ConfidenceModel()
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.5,
            base_confidence=50.0,
        )

        all_bullish = [
            FactorSemantic(name="trend", label="趋势", value=80.0, weight=0.30, contribution=24.0, is_bullish=True, assessment="强"),
            FactorSemantic(name="liquidity", label="流动性", value=75.0, weight=0.25, contribution=18.75, is_bullish=True, assessment="强"),
        ]
        all_bearish = [
            FactorSemantic(name="trend", label="趋势", value=20.0, weight=0.30, contribution=6.0, is_bullish=False, assessment="弱"),
            FactorSemantic(name="liquidity", label="流动性", value=25.0, weight=0.25, contribution=6.25, is_bullish=False, assessment="弱"),
        ]

        result_bullish = model.compute(signal=signal, factors=all_bullish)
        result_bearish = model.compute(signal=signal, factors=all_bearish)

        assert result_bullish > result_bearish

    def test_signal_dominates_when_extreme(self):
        model = ConfidenceModel()
        strong_signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.95,
            base_confidence=98.0,
        )
        weak_signal = SignalSemantic(
            direction="SHORT",
            direction_label="看空",
            strength=0.05,
            base_confidence=5.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=50.0, weight=0.30, contribution=15.0, is_bullish=True, assessment="中性"),
        ]

        result_strong = model.compute(signal=strong_signal, factors=factors)
        result_weak = model.compute(signal=weak_signal, factors=factors)

        assert result_strong > result_weak

    def test_custom_weights(self):
        model = ConfidenceModel(
            w_signal=0.50,
            w_factor=0.20,
            w_scenario=0.10,
            w_risk=0.15,
            w_execution=0.05,
        )
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.8,
            base_confidence=85.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
        ]
        result = model.compute(signal=signal, factors=factors)
        assert 0.0 <= result <= 1.0
