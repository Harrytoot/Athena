import pytest

from app.decision_semantics.mapper import SemanticMapper
from app.decision_semantics.schema import FactorSemantic, SignalSemantic
from app.decision_transparency.factor_attribution import FactorAttributionEngine
from app.decision_transparency.scenario_simulator import ScenarioSimulator
from app.decision_transparency.signal_explainer import SignalExplainer
from app.domain.market.market_score import MarketScore


class TestSignalMapping:

    def setup_method(self):
        self._mapper = SemanticMapper()
        self._explainer = SignalExplainer()

    def test_long_signal_mapping(self):
        score = MarketScore(trend=90.0, liquidity=85.0, breadth=80.0, volatility=70.0, sentiment=75.0)
        explanation = self._explainer.explain(score)
        result = self._mapper.map_signal(explanation)

        assert result.direction == "LONG"
        assert result.direction_label == "看多"
        assert result.strength > 0.5
        assert result.base_confidence > 0
        assert result.strength <= 1.0

    def test_short_signal_mapping(self):
        score = MarketScore(trend=10.0, liquidity=15.0, breadth=20.0, volatility=30.0, sentiment=12.0)
        explanation = self._explainer.explain(score)
        result = self._mapper.map_signal(explanation)

        assert result.direction == "SHORT"
        assert result.direction_label == "看空"
        assert result.strength > 0.5
        assert result.base_confidence > 0

    def test_neutral_signal_mapping(self):
        score = MarketScore(trend=50.0, liquidity=48.0, breadth=52.0, volatility=45.0, sentiment=55.0)
        explanation = self._explainer.explain(score)
        result = self._mapper.map_signal(explanation)

        assert result.direction == "NEUTRAL"
        assert result.direction_label == "中性"
        assert result.strength < 0.5

    def test_signal_strength_normalized(self):
        mapper = SemanticMapper()
        explainer = SignalExplainer()

        cases = [
            (MarketScore(trend=90.0, liquidity=90.0, breadth=90.0, volatility=90.0, sentiment=90.0), True),
            (MarketScore(trend=10.0, liquidity=10.0, breadth=10.0, volatility=10.0, sentiment=10.0), True),
            (MarketScore(trend=50.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0), False),
        ]
        for score, expect_strong in cases:
            explanation = explainer.explain(score)
            result = mapper.map_signal(explanation)
            assert 0.0 <= result.strength <= 1.0
            if expect_strong:
                assert result.strength > 0.7
            else:
                assert result.strength < 0.3


class TestFactorMapping:

    def setup_method(self):
        self._mapper = SemanticMapper()
        self._engine = FactorAttributionEngine()

    def test_factor_mapping(self):
        score = MarketScore(trend=85.0, liquidity=75.0, breadth=65.0, volatility=55.0, sentiment=60.0)
        attribution = self._engine.attribute(score)
        factors = self._mapper.map_factors(score, attribution)

        assert len(factors) == 5
        names = {f.name for f in factors}
        assert names == {"trend", "liquidity", "breadth", "volatility", "sentiment"}

        for f in factors:
            assert f.weight > 0
            assert 0.0 <= f.value <= 100.0
            assert len(f.label) > 0
            assert len(f.assessment) > 0

    def test_factor_contributions(self):
        score = MarketScore(trend=100.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)
        attribution = self._engine.attribute(score)
        factors = self._mapper.map_factors(score, attribution)

        trend_factor = next(f for f in factors if f.name == "trend")
        assert trend_factor.contribution == pytest.approx(100.0 * 0.30, rel=1e-4)

        neutral_factor = next(f for f in factors if f.name == "liquidity")
        assert neutral_factor.contribution == pytest.approx(50.0 * 0.25, rel=1e-4)

    def test_factor_is_bullish_threshold(self):
        mapper = SemanticMapper()
        engine = FactorAttributionEngine()
        score = MarketScore(trend=51.0, liquidity=49.0, breadth=51.0, volatility=49.0, sentiment=51.0)
        attribution = engine.attribute(score)
        factors = mapper.map_factors(score, attribution)

        for f in factors:
            if f.name in ("trend", "breadth", "sentiment"):
                assert f.is_bullish
            else:
                assert not f.is_bullish

    def test_deterministic_factor_mapping(self):
        mapper = SemanticMapper()
        engine = FactorAttributionEngine()
        score = MarketScore(trend=75.0, liquidity=60.0, breadth=55.0, volatility=45.0, sentiment=70.0)

        results = []
        for _ in range(10):
            attribution = engine.attribute(score)
            factors = mapper.map_factors(score, attribution)
            results.append([(f.name, f.value, f.contribution, f.is_bullish) for f in factors])

        for i in range(1, len(results)):
            assert results[i] == results[0]


class TestScenarioMapping:

    def setup_method(self):
        self._mapper = SemanticMapper()
        self._simulator = ScenarioSimulator()

    def test_scenario_mapping(self):
        results = self._simulator.simulate(
            trend=75.0, liquidity=70.0, breadth=65.0, volatility=55.0, sentiment=60.0,
        )
        scenario_sem = self._mapper.map_scenario(results, "LONG")

        assert scenario_sem.stability_score > 0
        assert scenario_sem.stability_score <= 1.0
        assert scenario_sem.state_change_count >= 0
        assert scenario_sem.worst_case_score_change < 0
        assert len(scenario_sem.entries) == 8

    def test_scenario_stability_low_on_volatile(self):
        results = self._simulator.simulate(
            trend=20.0, liquidity=20.0, breadth=20.0, volatility=20.0, sentiment=20.0,
        )
        scenario_sem = self._mapper.map_scenario(results, "SHORT")

        assert scenario_sem.stability_score < 0.8

    def test_scenario_empty_results(self):
        scenario_sem = self._mapper.map_scenario(None, "LONG")

        assert scenario_sem.stability_score == 0.0
        assert scenario_sem.worst_case_score_change == 0.0
        assert scenario_sem.state_change_count == 0
        assert len(scenario_sem.entries) == 0


class TestRiskMapping:

    def setup_method(self):
        self._mapper = SemanticMapper()
        self._engine = FactorAttributionEngine()

    def test_risk_mapping_from_signals(self):
        score = MarketScore(trend=30.0, liquidity=25.0, breadth=35.0, volatility=40.0, sentiment=20.0)
        attribution = self._engine.attribute(score)
        simulator = ScenarioSimulator()
        scenario_results = simulator.simulate(
            trend=score.trend,
            liquidity=score.liquidity,
            breadth=score.breadth,
            volatility=score.volatility,
            sentiment=score.sentiment,
        )
        risk = self._mapper.map_risk_from_signals(attribution.items, scenario_results)

        assert risk.overall_level in ("HIGH", "MODERATE", "LOW")
        assert risk.drawdown_risk > 0
        assert len(risk.warnings) >= 0

    def test_risk_mapping_null_risk(self):
        risk = self._mapper.map_risk(None, None)

        assert risk.overall_level == "LOW"
        assert risk.drawdown_risk == 0.0
        assert risk.volatility_risk == 0.0
        assert risk.correlation_risk == 0.0
