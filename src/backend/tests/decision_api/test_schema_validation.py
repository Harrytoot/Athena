import pytest
from pydantic import ValidationError

from app.decision_api.semantic_serializer import (
    BatchRequest,
    BatchResponse,
    DecisionSemanticResponse,
    ExplainResponse,
    SemanticSerializer,
)
from app.decision_semantics.schema import (
    ConsistencyReport,
    DecisionSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    SignalSemantic,
)


class TestDecisionSemanticResponseSchema:

    def setup_method(self):
        self._serializer = SemanticSerializer()

    def _make_semantic(self, **overrides) -> DecisionSemantic:
        defaults = {
            "symbol": "TEST",
            "name": "Test Stock",
            "signal": SignalSemantic(direction="LONG", direction_label="看多", strength=0.8, base_confidence=85.0),
            "factors": [
                FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
            ],
            "risk": RiskSemantic(overall_level="LOW", drawdown_risk=0.1, volatility_risk=0.2, correlation_risk=0.0, scenario_vulnerability=0.15),
            "scenario": ScenarioSemantic(stability_score=0.9, worst_case_score_change=-5.0, state_change_count=0),
            "confidence_score": 0.75,
            "consistency": ConsistencyReport(is_consistent=True),
            "action": "APPROVE",
            "action_label": "执行买入",
            "summary": "测试摘要",
        }
        defaults.update(overrides)
        return DecisionSemantic(**defaults)

    def test_response_contains_only_semantic_fields(self):
        semantic = self._make_semantic()
        response = self._serializer.serialize(semantic)

        data = response.model_dump(by_alias=True)

        allowed_fields = {
            "symbol", "name", "signal", "factors", "risk", "scenario",
            "execution", "confidenceScore", "consistency", "action",
            "actionLabel", "summary", "semanticVersion", "generatedAt",
        }

        for key in data:
            assert key in allowed_fields, f"Field '{key}' should not be in response"

    def test_response_excludes_legacy_fields(self):
        semantic = self._make_semantic()
        response = self._serializer.serialize(semantic)

        data = response.model_dump(by_alias=True)

        forbidden_fields = [
            "consensusItems", "riskItems", "scenarios",
            "signalLabel", "explanation",
        ]
        for field in forbidden_fields:
            assert field not in data, f"Legacy field '{field}' leaked into response"

    def test_response_excludes_legacy_signal_enum(self):
        semantic = self._make_semantic(signal=SignalSemantic(direction="LONG", direction_label="看多", strength=0.9, base_confidence=90.0))
        response = self._serializer.serialize(semantic)

        data = response.model_dump(by_alias=True)

        assert "signal" in data
        assert isinstance(data["signal"], dict)
        assert "direction" in data["signal"]
        assert "directionLabel" in data["signal"]
        assert data["signal"]["direction"] == "LONG"

    def test_signal_semantic_structure(self):
        signal = SignalSemantic(direction="NEUTRAL", direction_label="中性", strength=0.0, base_confidence=50.0)
        semantic = self._make_semantic(signal=signal)
        response = self._serializer.serialize(semantic)

        sig = response.model_dump(by_alias=True)["signal"]
        assert sig["direction"] == "NEUTRAL"
        assert sig["directionLabel"] == "中性"
        assert sig["strength"] == 0.0
        assert sig["baseConfidence"] == 50.0

    def test_risk_semantic_structure(self):
        risk = RiskSemantic(
            overall_level="HIGH",
            drawdown_risk=0.8,
            volatility_risk=0.7,
            correlation_risk=0.5,
            scenario_vulnerability=0.9,
            warnings=["高风险警告"],
        )
        semantic = self._make_semantic(risk=risk)
        response = self._serializer.serialize(semantic)

        r = response.model_dump(by_alias=True)["risk"]
        assert r["overallLevel"] == "HIGH"
        assert r["drawdownRisk"] == 0.8
        assert r["volatilityRisk"] == 0.7
        assert r["correlationRisk"] == 0.5
        assert r["scenarioVulnerability"] == 0.9
        assert r["warnings"] == ["高风险警告"]

    def test_scenario_semantic_structure(self):
        scenario = ScenarioSemantic(
            stability_score=0.5,
            worst_case_score_change=-25.0,
            state_change_count=3,
            entries=[{"name": "crash", "score_change": -25.0}],
        )
        semantic = self._make_semantic(scenario=scenario)
        response = self._serializer.serialize(semantic)

        s = response.model_dump(by_alias=True)["scenario"]
        assert s["stabilityScore"] == 0.5
        assert s["worstCaseScoreChange"] == -25.0
        assert s["stateChangeCount"] == 3
        assert len(s["entries"]) == 1

    def test_null_optional_fields_serialized_as_none(self):
        semantic = self._make_semantic(risk=None, scenario=None, consistency=None, execution=None)
        response = self._serializer.serialize(semantic)

        data = response.model_dump(by_alias=True)
        assert data["risk"] is None
        assert data["scenario"] is None
        assert data["execution"] is None
        assert data["consistency"] is None

    def test_consistency_report_structure(self):
        from app.decision_semantics.schema import ContradictionEntry

        consistency = ConsistencyReport(
            is_consistent=False,
            contradictions=[
                ContradictionEntry(contradiction_type="signal_vs_risk", severity="high", description="冲突描述"),
            ],
            consistency_score=0.7,
        )
        semantic = self._make_semantic(consistency=consistency)
        response = self._serializer.serialize(semantic)

        c = response.model_dump(by_alias=True)["consistency"]
        assert c["isConsistent"] is False
        assert c["consistencyScore"] == 0.7
        assert len(c["contradictions"]) == 1
        assert c["contradictions"][0]["contradictionType"] == "signal_vs_risk"
        assert c["contradictions"][0]["severity"] == "high"

    def test_batch_request_validation(self):
        valid = BatchRequest(symbols=["AAPL", "600519"])
        assert valid.symbols == ["AAPL", "600519"]

        with pytest.raises(ValidationError):
            BatchRequest(symbols=123)

    def test_batch_response_validation(self):
        semantic = self._make_semantic()
        serialized = self._serializer.serialize(semantic)
        response = BatchResponse(results=[serialized])
        assert len(response.results) == 1

    def test_explain_response_structure(self):
        semantic = self._make_semantic()
        explain = self._serializer.serialize_explain(semantic)

        data = explain.model_dump(by_alias=True)
        allowed = {"symbol", "name", "action", "actionLabel", "summary",
                     "direction", "directionLabel", "confidenceScore",
                     "semanticVersion", "generatedAt", "factors",
                     "riskWarnings", "scenarioSummary"}

        for key in data:
            assert key in allowed, f"Field '{key}' should not be in explain response"

        assert data["action"] == "APPROVE"
        assert data["direction"] == "LONG"
