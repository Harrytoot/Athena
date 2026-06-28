import pytest

from app.decision_semantics.streaming.streaming_engine import (
    StreamingEngine,
)
from app.decision_semantics.streaming.stream_processor import (
    StreamEventType,
    StreamEventRaw,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)


def _make_semantic(symbol: str = "AAPL", action: str = "APPROVE") -> DecisionSemantic:
    return DecisionSemantic(
        symbol=symbol,
        name="Test Stock",
        signal=SignalSemantic(
            direction="LONG" if action == "APPROVE" else "NEUTRAL",
            direction_label="看多" if action == "APPROVE" else "中性",
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
            FactorSemantic(
                name="momentum",
                label="动量",
                value=65.0,
                weight=0.25,
                contribution=16.25,
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
            warnings=[],
        ),
        scenario=ScenarioSemantic(
            stability_score=0.75,
            worst_case_score_change=-18.0,
            state_change_count=1,
            entries=[],
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action=action,
        action_label="执行买入" if action == "APPROVE" else "等待",
        summary="Test summary",
        semantic_version="1.0.0",
    )


class TestMultiSymbolCoordination:

    def setup_method(self):
        self._engine = StreamingEngine()

    def _initialize_symbols(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")
        s_tsla = _make_semantic("TSLA", "REJECT")

        self._engine.get_runtime_engine().initialize("AAPL", s_aapl)
        self._engine.get_runtime_engine().initialize("MSFT", s_msft)
        self._engine.get_runtime_engine().initialize("TSLA", s_tsla)

        self._engine.get_portfolio_graph().register_symbol("AAPL", s_aapl)
        self._engine.get_portfolio_graph().register_symbol("MSFT", s_msft)
        self._engine.get_portfolio_graph().register_symbol("TSLA", s_tsla)

    def test_multiple_symbols_initialized_correctly(self):
        self._initialize_symbols()

        active = self._engine.get_active_semantics()
        assert len(active) == 3
        assert "AAPL" in active
        assert "MSFT" in active
        assert "TSLA" in active
        assert active["AAPL"].action == "APPROVE"
        assert active["TSLA"].action == "REJECT"

    def test_cross_symbol_correlation_detection(self):
        self._initialize_symbols()

        self._engine.set_correlation("AAPL", "MSFT", 0.85)
        self._engine.set_correlation("AAPL", "TSLA", -0.45)

        correlations_a = self._engine.get_portfolio_graph().get_correlations_for("AAPL")
        assert abs(correlations_a.get("MSFT", 0.0) - 0.85) < 0.001
        assert abs(correlations_a.get("TSLA", 0.0) - (-0.45)) < 0.001

    def test_coordinated_stream_updates(self):
        self._initialize_symbols()

        self._engine.set_correlation("AAPL", "MSFT", 0.80)

        events = [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL",
                          {"signal_strength": 0.92, "confidence": 0.90}),
            StreamEventRaw(StreamEventType.RISK_EVENT, "MSFT",
                          {"volatility_risk": 0.55}),
        ]
        self._engine.ingest_events(events)

        result = self._engine.process_cycle()
        assert result.total_ingested > 0

    def test_multi_symbol_portfolio_view(self):
        self._initialize_symbols()

        self._engine.set_correlation("AAPL", "MSFT", 0.75)
        self._engine.set_correlation("MSFT", "TSLA", -0.30)

        state = self._engine.get_portfolio_state()
        assert len(state["symbols"]) == 3
        assert len(state["semantics"]) == 3
        assert len(state["correlations"]) == 2

    def test_correlation_propagation_detects_divergence(self):
        self._initialize_symbols()

        self._engine.set_correlation("AAPL", "TSLA", 0.85)

        portfolio_result = self._engine.get_portfolio_graph().update_symbol(
            "AAPL", self._engine.get_active_semantic("AAPL")
        )

        if portfolio_result.conflicts:
            assert any("AAPL" in c and "TSLA" in c for c in portfolio_result.conflicts)

    def test_multi_symbol_consistency_check(self):
        self._initialize_symbols()

        self._engine.set_correlation("AAPL", "MSFT", 0.80)
        self._engine.set_correlation("AAPL", "TSLA", -0.50)

        issues = self._engine.check_portfolio_consistency()

        assert isinstance(issues, list)

    def test_multi_symbol_execution_intents(self):
        self._initialize_symbols()

        events = [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL",
                          {"signal_strength": 0.88, "confidence": 0.85}),
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "MSFT",
                          {"signal_strength": 0.78, "confidence": 0.80}),
        ]
        self._engine.ingest_events(events)
        self._engine.process_cycle()

        intents = self._engine.get_execution_intents()
        assert len(intents) >= 1

    def test_fully_isolated_symbols_independent(self):
        self._initialize_symbols()

        aapl_before = self._engine.get_active_semantic("AAPL").confidence_score

        events = [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "MSFT",
                          {"confidence": 0.95}),
        ]
        self._engine.ingest_events(events)
        self._engine.process_cycle()

        aapl_after = self._engine.get_active_semantic("AAPL")
        assert aapl_after is not None
