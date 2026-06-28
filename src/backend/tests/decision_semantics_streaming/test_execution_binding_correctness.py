import pytest

from app.decision_semantics.streaming.execution_binding_layer import (
    ExecutionBindingLayer,
    ExecutionIntent,
    ExecutionBindingResult,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ExecutionSemantic,
    ConsistencyReport,
)


def _make_semantic(
    symbol: str = "AAPL",
    action: str = "APPROVE",
    feasibility: float = 0.85,
    slippage_bps: float = 5.0,
) -> DecisionSemantic:
    return DecisionSemantic(
        symbol=symbol,
        name=f"Strategy_{symbol}",
        signal=SignalSemantic(
            direction="LONG" if action == "APPROVE" else "SHORT",
            direction_label="看多" if action == "APPROVE" else "看空",
            strength=0.85,
            base_confidence=82.0,
        ),
        factors=[
            FactorSemantic(
                name="trend",
                label="趋势",
                value=88.0,
                weight=0.40,
                contribution=35.2,
                is_bullish=True,
                assessment="强看多",
            ),
        ],
        risk=RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.35,
            warnings=[],
        ),
        scenario=ScenarioSemantic(
            stability_score=0.75,
            worst_case_score_change=-18.0,
            state_change_count=1,
            entries=[],
        ),
        execution=ExecutionSemantic(
            feasibility=feasibility,
            estimated_slippage_bps=slippage_bps,
            estimated_fill_rate=0.95,
            quality_grade="A" if feasibility > 0.8 else "B",
            warnings=[],
        ),
        confidence_score=0.85,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action=action,
        action_label="执行买入" if action == "APPROVE" else "执行卖出",
        summary="Execution test summary",
        semantic_version="1.0.0",
    )


class TestExecutionBindingCorrectness:

    def setup_method(self):
        self._layer = ExecutionBindingLayer(default_notional=50000.0, default_price=150.0)

    def test_bind_approve_produces_buy_intent(self):
        semantic = _make_semantic("AAPL", "APPROVE", feasibility=0.90)
        intent = self._layer.bind(semantic)

        assert intent.action == "BUY"
        assert intent.symbol == "AAPL"
        assert intent.target_notional == 50000.0
        assert intent.reference_price == 150.0
        assert intent.is_active is True

    def test_bind_reject_produces_sell_intent(self):
        semantic = _make_semantic("AAPL", "REJECT", feasibility=0.90)
        intent = self._layer.bind(semantic)

        assert intent.action == "SELL"
        assert intent.is_active is True

    def test_bind_hold_produces_hold_intent(self):
        semantic = _make_semantic("AAPL", "HOLD")
        intent = self._layer.bind(semantic)

        assert intent.action == "HOLD"
        assert intent.is_active is False

    def test_bind_includes_execution_metadata(self):
        semantic = _make_semantic("AAPL", "APPROVE", feasibility=0.88, slippage_bps=12.5)
        intent = self._layer.bind(semantic)

        assert intent.metadata["feasibility"] == 0.88
        assert intent.metadata["estimated_slippage_bps"] == 12.5
        assert intent.metadata["quality_grade"] == "A"

    def test_bind_intent_is_deterministic(self):
        semantic = _make_semantic("AAPL", "APPROVE")

        intents = []
        for _ in range(5):
            layer = ExecutionBindingLayer(default_notional=50000.0, default_price=150.0)
            intents.append(layer.bind(semantic))

        for i in range(1, len(intents)):
            assert intents[i].intent_id == intents[0].intent_id
            assert intents[i].action == intents[0].action
            assert intents[i].target_notional == intents[0].target_notional

    def test_high_slippage_reduces_urgency(self):
        semantic = _make_semantic("AAPL", "APPROVE", feasibility=0.85, slippage_bps=75.0)
        intent = self._layer.bind(semantic)
        assert intent.urgency == "PASSIVE"

    def test_bind_portfolio_multiple_symbols(self):
        s_aapl = _make_semantic("AAPL", "APPROVE", feasibility=0.90)
        s_msft = _make_semantic("MSFT", "REJECT", feasibility=0.85)
        s_tsla = _make_semantic("TSLA", "HOLD", feasibility=0.50)

        semantics = {
            "AAPL": s_aapl,
            "MSFT": s_msft,
            "TSLA": s_tsla,
        }
        result = self._layer.bind_portfolio(semantics)

        assert len(result.executions) >= 2
        assert result.total_intents >= 2

    def test_low_feasibility_blocks_execution(self):
        semantic = _make_semantic("RISKY", "APPROVE", feasibility=0.15)
        intent = self._layer.bind(semantic)

        semantics = {"RISKY": semantic}
        result = self._layer.bind_portfolio(semantics)

        assert len(result.blocked_executions) == 1
        blocked = result.blocked_executions[0]
        assert blocked.intent.symbol == "RISKY"

    def test_intent_to_dict_format(self):
        semantic = _make_semantic("AAPL", "APPROVE")
        intent = self._layer.bind(semantic, notional_override=25000.0, price_override=200.0)

        d = intent.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["action"] == "BUY"
        assert d["target_notional"] == 25000.0
        assert d["reference_price"] == 200.0

    def test_intent_to_execution_order_format(self):
        semantic = _make_semantic("AAPL", "APPROVE")
        intent = self._layer.bind(semantic)

        order = intent.to_execution_order()
        assert order["symbol"] == "AAPL"
        assert order["side"] == "buy"
        assert "notional" in order
        assert "price" in order

    def test_execution_binding_history_tracked(self):
        s1 = _make_semantic("AAPL", "APPROVE")
        s2 = _make_semantic("MSFT", "REJECT")

        semantics = {"AAPL": s1, "MSFT": s2}
        self._layer.bind_portfolio(semantics)

        history = self._layer.get_binding_history()
        assert len(history) == 2

    def test_portfolio_consistency_validation(self):
        s_aapl = _make_semantic("AAPL", "APPROVE", feasibility=0.90)
        s_msft = _make_semantic("MSFT", "REJECT", feasibility=0.85)

        semantics = {"AAPL": s_aapl, "MSFT": s_msft}
        self._layer.bind_portfolio(semantics)

        is_consistent = self._layer.validate_portfolio_consistency([], [("AAPL", "MSFT")])
        assert isinstance(is_consistent, bool)
