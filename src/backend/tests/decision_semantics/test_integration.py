import pytest

from app.decision_semantics.confidence_model import ConfidenceModel
from app.decision_semantics.mapper import SemanticMapper
from app.decision_semantics.reducer import SemanticReducer, ReductionInput
from app.decision_semantics.registry import SemanticRegistry, CURRENT_VERSION
from app.decision_semantics.schema import (
    DecisionSemantic,
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)
from app.decision_semantics.validator import SemanticValidator
from app.decision_transparency.factor_attribution import FactorAttributionEngine
from app.decision_transparency.scenario_simulator import ScenarioSimulator
from app.decision_transparency.signal_explainer import SignalExplainer
from app.domain.market.market_score import MarketScore


class TestFullPipelineIntegration:

    def setup_method(self):
        self._mapper = SemanticMapper()
        self._explainer = SignalExplainer()
        self._engine = FactorAttributionEngine()
        self._simulator = ScenarioSimulator()
        self._confidence = ConfidenceModel()
        self._validator = SemanticValidator()
        self._reducer = SemanticReducer()
        self._registry = SemanticRegistry()

    def test_full_pipeline_bullish(self):
        score = MarketScore(trend=90.0, liquidity=85.0, breadth=80.0, volatility=70.0, sentiment=75.0)
        explanation = self._explainer.explain(score)
        attribution = self._engine.attribute(score)
        scenario_results = self._simulator.simulate(
            trend=score.trend,
            liquidity=score.liquidity,
            breadth=score.breadth,
            volatility=score.volatility,
            sentiment=score.sentiment,
        )

        signal = self._mapper.map_signal(explanation)
        factors = self._mapper.map_factors(score, attribution)
        risk = self._mapper.map_risk_from_signals(attribution.items, scenario_results)
        scenario = self._mapper.map_scenario(scenario_results, signal.direction)
        confidence = self._confidence.compute(
            signal=signal, factors=factors, scenario=scenario, risk=risk
        )
        consistency = self._validator.validate(
            signal=signal, factors=factors, risk=risk, scenario=scenario
        )

        semantic = DecisionSemantic(
            symbol="TEST",
            name="Test Stock",
            signal=signal,
            factors=factors,
            risk=risk,
            scenario=scenario,
            confidence_score=confidence,
            consistency=consistency,
            action="APPROVE" if signal.direction == "LONG" else "HOLD",
            action_label="执行买入" if signal.direction == "LONG" else "等待确认信号",
            summary=explanation.summary,
            semantic_version=self._registry.current_version,
        )

        assert semantic.symbol == "TEST"
        assert semantic.signal.direction == "LONG"
        assert semantic.confidence_score > 0.5
        assert len(semantic.factors) == 5
        assert semantic.scenario is not None
        assert semantic.risk is not None
        assert semantic.semantic_version == "1.0.0"

    def test_full_pipeline_bearish(self):
        score = MarketScore(trend=10.0, liquidity=15.0, breadth=20.0, volatility=30.0, sentiment=12.0)
        explanation = self._explainer.explain(score)
        attribution = self._engine.attribute(score)
        scenario_results = self._simulator.simulate(
            trend=score.trend,
            liquidity=score.liquidity,
            breadth=score.breadth,
            volatility=score.volatility,
            sentiment=score.sentiment,
        )

        signal = self._mapper.map_signal(explanation)
        factors = self._mapper.map_factors(score, attribution)
        risk = self._mapper.map_risk_from_signals(attribution.items, scenario_results)
        scenario = self._mapper.map_scenario(scenario_results, signal.direction)
        confidence = self._confidence.compute(
            signal=signal, factors=factors, scenario=scenario, risk=risk
        )
        consistency = self._validator.validate(
            signal=signal, factors=factors, risk=risk, scenario=scenario
        )

        semantic = DecisionSemantic(
            symbol="TEST",
            name="Test Stock",
            signal=signal,
            factors=factors,
            risk=risk,
            scenario=scenario,
            confidence_score=confidence,
            consistency=consistency,
            action="REJECT",
            action_label="清仓离场",
            summary=explanation.summary,
            semantic_version=self._registry.current_version,
        )

        assert semantic.signal.direction == "SHORT"
        assert semantic.confidence_score > 0.0
        assert semantic.confidence_score < 1.0

    def test_full_pipeline_neutral(self):
        score = MarketScore(trend=50.0, liquidity=48.0, breadth=52.0, volatility=45.0, sentiment=55.0)
        explanation = self._explainer.explain(score)
        attribution = self._engine.attribute(score)
        scenario_results = self._simulator.simulate(
            trend=score.trend,
            liquidity=score.liquidity,
            breadth=score.breadth,
            volatility=score.volatility,
            sentiment=score.sentiment,
        )

        signal = self._mapper.map_signal(explanation)
        factors = self._mapper.map_factors(score, attribution)
        risk = self._mapper.map_risk_from_signals(attribution.items, scenario_results)
        scenario = self._mapper.map_scenario(scenario_results, signal.direction)
        confidence = self._confidence.compute(
            signal=signal, factors=factors, scenario=scenario, risk=risk
        )
        consistency = self._validator.validate(
            signal=signal, factors=factors, risk=risk, scenario=scenario
        )

        semantic = DecisionSemantic(
            symbol="TEST",
            name="Test Stock",
            signal=signal,
            factors=factors,
            risk=risk,
            scenario=scenario,
            confidence_score=confidence,
            consistency=consistency,
            action="HOLD",
            action_label="等待确认信号",
            summary=explanation.summary,
            semantic_version=self._registry.current_version,
        )

        assert semantic.signal.direction == "NEUTRAL"

    def test_deterministic_pipeline(self):
        score = MarketScore(trend=75.0, liquidity=60.0, breadth=55.0, volatility=45.0, sentiment=70.0)

        results = []
        for _ in range(5):
            explanation = self._explainer.explain(score)
            attribution = self._engine.attribute(score)
            scenario_results = self._simulator.simulate(
                trend=score.trend,
                liquidity=score.liquidity,
                breadth=score.breadth,
                volatility=score.volatility,
                sentiment=score.sentiment,
            )
            signal = self._mapper.map_signal(explanation)
            factors = self._mapper.map_factors(score, attribution)
            risk = self._mapper.map_risk_from_signals(attribution.items, scenario_results)
            scenario = self._mapper.map_scenario(scenario_results, signal.direction)
            confidence = self._confidence.compute(
                signal=signal, factors=factors, scenario=scenario, risk=risk
            )
            consistency = self._validator.validate(
                signal=signal, factors=factors, risk=risk, scenario=scenario
            )
            results.append({
                "direction": signal.direction,
                "strength": signal.strength,
                "confidence": confidence,
                "consistency_score": consistency.consistency_score,
            })

        for i in range(1, len(results)):
            assert results[i] == results[0]


class TestSemanticReducer:

    def setup_method(self):
        self._reducer = SemanticReducer()

    def test_reduce_single_input(self):
        signal = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.8,
            base_confidence=85.0,
        )
        factors = [
            FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
        ]
        inp = ReductionInput(
            symbol="TEST",
            name="Test Stock",
            signal=signal,
            factors=factors,
            confidence_score=0.75,
            action="APPROVE",
            action_label="执行买入",
        )

        result = self._reducer.reduce([inp])

        assert result.symbol == "TEST"
        assert result.signal.direction == "LONG"
        assert len(result.factors) == 1
        assert result.confidence_score == 0.75
        assert result.action == "APPROVE"

    def test_reduce_multiple_inputs(self):
        signal1 = SignalSemantic(
            direction="LONG",
            direction_label="看多",
            strength=0.8,
            base_confidence=85.0,
        )
        factors1 = [
            FactorSemantic(name="trend", label="趋势", value=85.0, weight=0.30, contribution=25.5, is_bullish=True, assessment="强"),
        ]
        factors2 = [
            FactorSemantic(name="liquidity", label="流动性", value=70.0, weight=0.25, contribution=17.5, is_bullish=True, assessment="偏强"),
        ]
        consistency1 = ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=1.0,
        )

        inp1 = ReductionInput(
            symbol="TEST",
            name="Test Stock",
            signal=signal1,
            factors=factors1,
            confidence_score=0.8,
            consistency=consistency1,
        )
        inp2 = ReductionInput(
            symbol="TEST",
            name="Test Stock",
            factors=factors2,
        )

        result = self._reducer.reduce([inp1, inp2])

        assert result.symbol == "TEST"
        assert len(result.factors) == 2

    def test_reduce_empty(self):
        result = self._reducer.reduce([])

        assert result.symbol == ""
        assert result.signal.direction == "NEUTRAL"
        assert result.action == "HOLD"


class TestSemanticRegistry:

    def setup_method(self):
        self._registry = SemanticRegistry()

    def test_current_version(self):
        assert self._registry.current_version == "1.0.0"

    def test_version_supported(self):
        assert self._registry.is_version_supported("1.0.0")
        assert self._registry.is_version_supported("1.0.5")
        assert self._registry.is_version_supported("2.0.0")
        assert not self._registry.is_version_supported("3.0.0")
        assert not self._registry.is_version_supported("invalid")

    def test_compatibility_check(self):
        assert self._registry.check_compatibility("1.0.0")
        assert not self._registry.check_compatibility("3.0.0")

    def test_supported_versions_list(self):
        versions = self._registry.supported_versions
        assert "1.0.0" in versions
