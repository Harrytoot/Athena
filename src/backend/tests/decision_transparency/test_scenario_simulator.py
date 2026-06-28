import pytest

from app.decision_transparency.scenario_simulator import (
    ScenarioSimulator,
    ScenarioDefinition,
    SCENARIO_MARKET_SHOCK_NEG5,
    SCENARIO_VOLATILITY_SPIKE,
    SCENARIO_LIQUIDITY_DRYUP,
    SCENARIO_TREND_REVERSAL,
)


class TestScenarioSimulator:

    def test_all_default_scenarios(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=70.0, liquidity=65.0, breadth=60.0,
            volatility=50.0, sentiment=55.0,
        )
        assert len(results) >= 1
        for r in results:
            assert r.original_score > 0
            assert r.simulated_score >= 0
            assert len(r.impact_assessment) > 0
            assert len(r.direction_change) > 0

    def test_market_shock_reduces_score(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=70.0, liquidity=65.0, breadth=60.0,
            volatility=50.0, sentiment=55.0,
        )
        shock = next(r for r in results if r.scenario.scenario_id == SCENARIO_MARKET_SHOCK_NEG5)
        assert shock.score_change < 0

    def test_volatility_spike_changes_score(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=70.0, liquidity=65.0, breadth=60.0,
            volatility=50.0, sentiment=55.0,
        )
        vol_spike = next(r for r in results if r.scenario.scenario_id == SCENARIO_VOLATILITY_SPIKE)
        assert vol_spike.simulated_factors["volatility"] != 50.0

    def test_liquidity_dryup(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=70.0, liquidity=65.0, breadth=60.0,
            volatility=50.0, sentiment=55.0,
        )
        dryup = next(r for r in results if r.scenario.scenario_id == SCENARIO_LIQUIDITY_DRYUP)
        assert dryup.simulated_factors["liquidity"] < 65.0

    def test_trend_reversal(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=70.0, liquidity=65.0, breadth=60.0,
            volatility=50.0, sentiment=55.0,
        )
        reversal = next(r for r in results if r.scenario.scenario_id == SCENARIO_TREND_REVERSAL)
        assert reversal.simulated_factors["trend"] < 70.0

    def test_factor_bounds_clamped(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=95.0, liquidity=95.0, breadth=95.0,
            volatility=95.0, sentiment=95.0,
        )
        for r in results:
            for v in r.simulated_factors.values():
                assert 0.0 <= v <= 100.0

    def test_run_custom_scenario(self):
        sim = ScenarioSimulator()
        custom = ScenarioDefinition(
            scenario_id="custom_test",
            name="自定义测试",
            description="测试自定义场景",
            price_shift_pct=-0.08,
        )
        result = sim.run_custom(
            trend=65.0, liquidity=60.0, breadth=55.0,
            volatility=50.0, sentiment=45.0,
            scenario=custom,
        )
        assert result.scenario.scenario_id == "custom_test"
        assert result.score_change < 0

    def test_scenarios_property(self):
        sim = ScenarioSimulator()
        scenarios = sim.scenarios
        assert len(scenarios) > 0
        assert all(isinstance(s, ScenarioDefinition) for s in scenarios)

    def test_custom_scenarios_override(self):
        custom_scenarios = [
            ScenarioDefinition(
                scenario_id="test_only",
                name="测试",
                description="仅测试场景",
                price_shift_pct=-0.03,
            ),
        ]
        sim = ScenarioSimulator(scenarios=custom_scenarios)
        results = sim.simulate(
            trend=60.0, liquidity=55.0, breadth=50.0,
            volatility=50.0, sentiment=50.0,
        )
        assert len(results) == 1
        assert results[0].scenario.scenario_id == "test_only"

    def test_state_change_detected(self):
        sim = ScenarioSimulator()
        result = sim.run_custom(
            trend=55.0, liquidity=55.0, breadth=55.0,
            volatility=55.0, sentiment=55.0,
            scenario=ScenarioDefinition(
                scenario_id="big_drop",
                name="大跌",
                description="大跌测试",
                price_shift_pct=-0.50,
            ),
        )
        assert result.state_changed or result.score_change < -10

    def test_score_change_within_reasonable_range(self):
        sim = ScenarioSimulator()
        results = sim.simulate(
            trend=50.0, liquidity=50.0, breadth=50.0,
            volatility=50.0, sentiment=50.0,
        )
        for r in results:
            assert -100.0 <= r.score_change <= 100.0
