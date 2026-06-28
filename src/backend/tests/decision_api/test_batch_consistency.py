from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import get_decision_service
from app.application.dtos.decision_dtos import (
    DecisionDTO,
    FactorSemanticDTO,
    SignalEnum,
    SignalSemanticDTO,
)
from app.providers.stock.detail_base import StockDetail


def _make_decision_dto(symbol: str, name: str, direction: str) -> DecisionDTO:
    direction_label_map = {"LONG": "看多", "SHORT": "看空", "NEUTRAL": "中性"}
    signal_enum_map = {"LONG": SignalEnum.STRONG_BUY, "SHORT": SignalEnum.STRONG_SELL, "NEUTRAL": SignalEnum.NEUTRAL}
    return DecisionDTO(
        symbol=symbol,
        name=name,
        signal=signal_enum_map.get(direction, SignalEnum.NEUTRAL),
        signal_label=direction_label_map.get(direction, "中性"),
        confidence=85.0,
        action="APPROVE",
        action_label="执行买入",
        factors=[
            FactorSemanticDTO(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
        ],
        signal_semantic=SignalSemanticDTO(direction=direction, direction_label=direction_label_map.get(direction, "中性"), strength=0.8, base_confidence=85.0),
        semantic_version="1.0.0",
    )


def _make_stock_detail(symbol: str, name: str) -> StockDetail:
    return StockDetail(
        symbol=symbol,
        name=name,
        price=100.0,
        changePct=1.0,
        open=99.0,
        high=101.0,
        low=98.0,
        volume=1000000,
        turnover=100000000.0,
        marketCap=1000000000.0,
        peRatio=20.0,
        pbRatio=2.0,
    )


class TestBatchConsistency:

    def test_same_symbol_serializes_identically(self):
        from app.decision_api.semantic_serializer import SemanticSerializer
        from app.decision_semantics.schema import (
            DecisionSemantic,
            FactorSemantic,
            SignalSemantic,
        )

        serializer = SemanticSerializer()

        semantic = DecisionSemantic(
            symbol="TEST",
            name="Test Stock",
            signal=SignalSemantic(direction="LONG", direction_label="看多", strength=0.8, base_confidence=85.0),
            factors=[FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强")],
            confidence_score=0.75,
            action="APPROVE",
            action_label="执行买入",
            summary="test",
            semantic_version="1.0.0",
        )

        result1 = serializer.serialize(semantic)
        result2 = serializer.serialize(semantic)

        assert result1.model_dump(by_alias=True) == result2.model_dump(by_alias=True)

    def test_batch_response_ordering(self):
        from app.decision_api.semantic_serializer import BatchResponse, SemanticSerializer
        from app.decision_semantics.schema import (
            DecisionSemantic,
            FactorSemantic,
            SignalSemantic,
        )

        serializer = SemanticSerializer()

        sem1 = DecisionSemantic(
            symbol="FIRST",
            name="First Stock",
            signal=SignalSemantic(direction="LONG", direction_label="看多", strength=0.8, base_confidence=85.0),
            factors=[FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强")],
            confidence_score=0.9,
            action="APPROVE",
            action_label="执行买入",
            semantic_version="1.0.0",
        )
        sem2 = DecisionSemantic(
            symbol="SECOND",
            name="Second Stock",
            signal=SignalSemantic(direction="NEUTRAL", direction_label="中性", strength=0.1, base_confidence=50.0),
            factors=[],
            action="HOLD",
            action_label="等待确认信号",
            semantic_version="1.0.0",
        )

        resp1 = serializer.serialize(sem1)
        resp2 = serializer.serialize(sem2)

        batch = BatchResponse(results=[resp1, resp2])
        assert len(batch.results) == 2
        assert batch.results[0].symbol == "FIRST"
        assert batch.results[1].symbol == "SECOND"

    def test_batch_empty_returns_empty_list(self):
        from app.decision_api.semantic_serializer import BatchResponse
        batch = BatchResponse(results=[])
        assert batch.results == []

    def test_all_responses_have_required_fields(self):
        from app.decision_api.semantic_serializer import SemanticSerializer
        from app.decision_semantics.schema import (
            DecisionSemantic,
            FactorSemantic,
            SignalSemantic,
        )

        serializer = SemanticSerializer()

        for direction in ["LONG", "SHORT", "NEUTRAL"]:
            semantic = DecisionSemantic(
                symbol=f"T_{direction}",
                name=f"Test {direction}",
                signal=SignalSemantic(direction=direction, direction_label="测试", strength=0.5, base_confidence=50.0),
                factors=[FactorSemantic(name="trend", label="趋势", value=50.0, weight=0.30, contribution=15.0, is_bullish=direction == "LONG", assessment="中性")],
                confidence_score=0.5,
                action="HOLD",
                action_label="等待",
                semantic_version="1.0.0",
            )
            response = serializer.serialize(semantic)
            data = response.model_dump(by_alias=True)

            required = ["symbol", "name", "signal", "confidenceScore", "action", "actionLabel", "semanticVersion", "generatedAt"]
            for field in required:
                assert field in data, f"Missing required field '{field}' in {direction} response"

    def test_explain_response_consistent_with_decision(self):
        from app.decision_api.semantic_serializer import SemanticSerializer
        from app.decision_semantics.schema import (
            ConsistencyReport,
            ContradictionEntry,
            DecisionSemantic,
            FactorSemantic,
            RiskSemantic,
            ScenarioSemantic,
            SignalSemantic,
        )

        serializer = SemanticSerializer()

        risk = RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.5,
            warnings=["测试警告"],
        )

        scenario = ScenarioSemantic(
            stability_score=0.6,
            worst_case_score_change=-15.0,
            state_change_count=2,
            entries=[
                {"name": "bear_crash", "score_change": -20.0, "state_changed": True},
                {"name": "bull", "score_change": 5.0, "state_changed": False},
            ],
        )

        consistency = ConsistencyReport(
            is_consistent=False,
            contradictions=[
                ContradictionEntry(contradiction_type="signal_vs_risk", severity="medium", description="信号与风险冲突"),
            ],
            consistency_score=0.85,
        )

        semantic = DecisionSemantic(
            symbol="CONSISTENCY",
            name="Consistency Test",
            signal=SignalSemantic(direction="LONG", direction_label="看多", strength=0.7, base_confidence=75.0),
            factors=[FactorSemantic(name="trend", label="趋势", value=70.0, weight=0.30, contribution=21.0, is_bullish=True, assessment="偏强")],
            risk=risk,
            scenario=scenario,
            confidence_score=0.65,
            consistency=consistency,
            action="HOLD",
            action_label="等待确认信号",
            summary="综合评分中等，方向看多但存风险",
            semantic_version="1.0.0",
        )

        decision_resp = serializer.serialize(semantic)
        explain_resp = serializer.serialize_explain(semantic)

        assert decision_resp.symbol == explain_resp.symbol
        assert decision_resp.name == explain_resp.name
        assert decision_resp.action == explain_resp.action
        assert decision_resp.action_label == explain_resp.action_label
        assert decision_resp.semantic_version == explain_resp.semantic_version
        assert decision_resp.generated_at == explain_resp.generated_at
        assert decision_resp.confidence_score == explain_resp.confidence_score
