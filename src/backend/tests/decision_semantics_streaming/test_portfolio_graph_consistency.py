import pytest

from app.decision_semantics.streaming.portfolio_runtime_graph import (
    PortfolioRuntimeGraph,
    CorrelationEdge,
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


class TestPortfolioGraphConsistency:

    def setup_method(self):
        self._graph = PortfolioRuntimeGraph(correlation_threshold=0.3)

    def test_register_symbols(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)

        assert len(self._graph.get_all_symbols()) == 2
        assert self._graph.get_node("AAPL").active_semantic.action == "APPROVE"

    def test_correlation_insertion(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)

        self._graph.set_correlation("AAPL", "MSFT", 0.85)

        corr = self._graph.get_correlation("AAPL", "MSFT")
        assert abs(corr - 0.85) < 0.001

    def test_correlation_is_symmetric(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)

        self._graph.set_correlation("AAPL", "MSFT", 0.75)

        assert abs(self._graph.get_correlation("AAPL", "MSFT") - 0.75) < 0.001
        assert abs(self._graph.get_correlation("MSFT", "AAPL") - 0.75) < 0.001

    def test_consistency_no_conflicts_with_aligned_actions(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)
        self._graph.set_correlation("AAPL", "MSFT", 0.85)

        issues = self._graph.check_portfolio_consistency()
        assert len(issues) == 0

    def test_consistency_detects_divergent_actions_on_positive_correlation(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "REJECT")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)
        self._graph.set_correlation("AAPL", "MSFT", 0.85)

        issues = self._graph.check_portfolio_consistency()
        assert len(issues) >= 1
        assert any("AAPL" in issue and "MSFT" in issue for issue in issues)

    def test_consistency_detects_identical_actions_on_negative_correlation(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_xom = _make_semantic("XOM", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("XOM", s_xom)
        self._graph.set_correlation("AAPL", "XOM", -0.75)

        issues = self._graph.check_portfolio_consistency()
        assert len(issues) >= 1

    def test_hold_does_not_trigger_conflicts(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "HOLD")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)
        self._graph.set_correlation("AAPL", "MSFT", 0.90)

        issues = self._graph.check_portfolio_consistency()
        assert len(issues) == 0

    def test_no_correlation_no_consistency_issues(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_gold = _make_semantic("GOLD", "REJECT")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("GOLD", s_gold)

        issues = self._graph.check_portfolio_consistency()
        assert len(issues) == 0

    def test_symbol_update_propagates_to_dependents(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)
        self._graph.set_correlation("AAPL", "MSFT", 0.80)

        s_aapl_updated = _make_semantic("AAPL", "REJECT")
        result = self._graph.update_symbol("AAPL", s_aapl_updated)

        assert result.applied is True
        assert "MSFT" in result.propagated_to

    def test_correlation_impact_query(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)
        self._graph.set_correlation("AAPL", "MSFT", 0.70)

        impact = self._graph.query_impact("AAPL", {"confidence": 0.15})
        assert "MSFT" in impact
        assert impact["MSFT"] > 0

    def test_graph_reset(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.set_correlation("AAPL", "MSFT", 0.80)

        self._graph.reset()

        assert len(self._graph.get_all_symbols()) == 0
        assert len(self._graph.get_all_edges()) == 0

    def test_correlation_edge_deterministic_id(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        self._graph.register_symbol("AAPL", s_aapl)
        self._graph.register_symbol("MSFT", s_msft)

        ids = []
        for _ in range(5):
            g = PortfolioRuntimeGraph(correlation_threshold=0.3)
            g.register_symbol("AAPL", s_aapl)
            g.register_symbol("MSFT", s_msft)
            edge = g.set_correlation("AAPL", "MSFT", 0.75)
            ids.append(edge.edge_id)

        for i in range(1, len(ids)):
            assert ids[i] == ids[0]
