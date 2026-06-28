import pytest

from app.decision_semantics.schema import (
    ConsistencyReport,
    ContradictionEntry,
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
)
from app.decision_semantics.validator import SemanticValidator


class TestRiskContradictionDetection:

    def setup_method(self):
        self._validator = SemanticValidator()

    def test_long_signal_high_risk_contradiction(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.8,
            base_confidence=85.0,
        )
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=0.8,
            correlation_risk=0.7,
            scenario_vulnerability=0.9,
            warnings=["高风险"],
        )
        report = self._validator.validate(signal=signal, risk=risk)

        assert not report.is_consistent
        assert len(report.contradictions) > 0
        assert any(
            "做多" in c.description and "高风险" in c.description
            for c in report.contradictions
        )
        assert report.consistency_score < 1.0

    def test_long_signal_moderate_risk_warning(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.6,
            base_confidence=65.0,
        )
        risk = RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.5,
            volatility_risk=0.5,
            correlation_risk=0.5,
            scenario_vulnerability=0.5,
        )
        report = self._validator.validate(signal=signal, risk=risk)

        assert any(
            c.severity == "medium" for c in report.contradictions
        ) or report.is_consistent

    def test_short_signal_high_risk_contradiction(self):
        signal = SignalSemantic(
            direction="SHORT",
            direction_label="看空",
            strength=0.75,
            base_confidence=80.0,
        )
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=0.9,
            correlation_risk=0.8,
            scenario_vulnerability=0.95,
            warnings=["高风险"],
        )
        report = self._validator.validate(signal=signal, risk=risk)

        assert not report.is_consistent
        assert any(
            "做空" in c.description and "高风险" in c.description
            for c in report.contradictions
        )

    def test_neutral_signal_no_risk_contradiction(self):
        signal = SignalSemantic(
            direction="NEUTRAL",
            direction_label="中性",
            strength=0.1,
            base_confidence=50.0,
        )
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=1.0,
            correlation_risk=1.0,
            scenario_vulnerability=1.0,
            warnings=["高风险"],
        )
        report = self._validator.validate(signal=signal, risk=risk)

        assert report.is_consistent

    def test_strong_signal_high_risk_mismatch(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.85,
            base_confidence=90.0,
        )
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=1.0,
            correlation_risk=1.0,
            scenario_vulnerability=1.0,
            warnings=["高风险"],
        )
        report = self._validator.validate(signal=signal, risk=risk)

        assert not report.is_consistent
        assert any(
            c.severity == "high" for c in report.contradictions
        )

    def test_consistency_score_calculation(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.9,
            base_confidence=90.0,
        )
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=1.0,
            volatility_risk=1.0,
            correlation_risk=1.0,
            scenario_vulnerability=1.0,
            warnings=["高风险"],
        )
        report = self._validator.validate(signal=signal, risk=risk)

        assert 0.0 <= report.consistency_score <= 1.0
        expected_max = 1.0
        high_count = sum(1 for c in report.contradictions if c.severity == "high")
        medium_count = sum(1 for c in report.contradictions if c.severity == "medium")
        low_count = sum(1 for c in report.contradictions if c.severity == "low")
        expected = max(0.0, expected_max - high_count * 0.30 - medium_count * 0.15 - low_count * 0.05)
        assert report.consistency_score == pytest.approx(expected, rel=1e-4)
