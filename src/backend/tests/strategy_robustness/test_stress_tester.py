from datetime import datetime, timezone

import pytest

from app.strategy_robustness.stress_tester import (
    StressScenario,
    StressTestResult,
    StressTester,
    ShockScenario,
)
from tests.strategy_robustness import _build_history, _risk_result


class TestStressScenario:

    def test_enum_values(self):
        assert StressScenario.FLASH_CRASH == "flash_crash"
        assert StressScenario.BEAR_MARKET == "bear_market"
        assert StressScenario.VOLATILITY_SPIKE == "volatility_spike"
        assert StressScenario.RECOVERY_RALLY == "recovery_rally"
        assert StressScenario.SIDEWAYS_CHOP == "sideways_chop"
        assert StressScenario.GAP_RISK == "gap_risk"


class TestStressTester:

    def test_empty_history(self):
        tester = StressTester()
        history = _build_history([], [])
        risk = _risk_result([])
        results = tester.run(history, risk)
        assert len(results) == 0

    def test_stress_scenarios_generated(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 30,
            [100.0 + i * 0.5 for i in range(30)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 30)
        results = tester.run(history, risk)
        assert len(results) > 0
        assert all(isinstance(r, StressTestResult) for r in results)

    def test_baseline_comparison_available(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 20,
            [100.0 + i * 0.5 for i in range(20)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 20)
        results = tester.run(history, risk)
        for r in results:
            assert isinstance(r.return_delta_vs_baseline, float)
            assert isinstance(r.sharpe_delta_vs_baseline, float)
            assert isinstance(r.max_drawdown_delta_vs_baseline, float)

    def test_flash_crash_reduces_return(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 30,
            [100.0 + i * 0.5 for i in range(30)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 30)
        results = tester.run(history, risk)
        crash_results = [r for r in results if r.scenario == StressScenario.FLASH_CRASH]
        assert len(crash_results) > 0
        for cr in crash_results:
            assert cr.return_delta_vs_baseline <= 0
            assert cr.survived is True

    def test_bear_market_increases_drawdown(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 50,
            [100.0 + i * 0.2 for i in range(50)],
            initial_nav=100000.0,
        )
        risk = _risk_result([1.0] * 50)
        results = tester.run(history, risk)
        bear_results = [r for r in results if r.scenario == StressScenario.BEAR_MARKET]
        assert len(bear_results) > 0
        for br in bear_results:
            assert br.max_drawdown_delta_vs_baseline <= 0 or br.max_drawdown <= 0

    def test_perturbation_stability(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 50,
            [100.0 + i * 0.1 for i in range(50)],
            initial_nav=100000.0,
        )
        stability = tester.perturbation_stability(history, noise_scale=0.001, num_trials=10)
        assert "mean_sharpe" in stability
        assert "sharpe_std" in stability
        assert "stability" in stability
        assert 0.0 <= stability["stability"] <= 1.0

    def test_perturbation_stability_few_trials(self):
        tester = StressTester()
        history = _build_history(
            [0.5] * 20,
            [100.0 + i * 0.2 for i in range(20)],
            initial_nav=100000.0,
        )
        stability = tester.perturbation_stability(history, noise_scale=0.001, num_trials=3)
        assert stability["stability"] >= 0.0

    def test_perturbation_stability_empty_history(self):
        tester = StressTester()
        history = _build_history([], [])
        stability = tester.perturbation_stability(history)
        assert stability["stability"] == 0.0
        assert stability["mean_sharpe"] == 0.0
        assert stability["sharpe_std"] == 0.0

    def test_perturbation_stability_zero_trials(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 10,
            [100.0 + i for i in range(10)],
        )
        stability = tester.perturbation_stability(history, num_trials=0)
        assert stability["stability"] == 0.0

    def test_all_scenarios_survive_on_flat_strategy(self):
        tester = StressTester()
        history = _build_history(
            [0.0] * 30,
            [100.0] * 30,
            initial_nav=100000.0,
        )
        risk = _risk_result([0.0] * 30)
        results = tester.run(history, risk)
        for r in results:
            assert r.survived is True

    def test_deterministic_noise_produces_repeatable_results(self):
        tester = StressTester()
        history = _build_history(
            [1.0] * 20,
            [100.0 + i * 0.1 for i in range(20)],
            initial_nav=100000.0,
        )
        result1 = tester.perturbation_stability(history, noise_scale=0.001, num_trials=5)
        result2 = tester.perturbation_stability(history, noise_scale=0.001, num_trials=5)
        assert result1["stability"] == result2["stability"]

    def test_scenario_types_coverage(self):
        tester = StressTester()
        history = _build_history(
            [0.5] * 40,
            [100.0 + i * 0.3 for i in range(40)],
            initial_nav=100000.0,
        )
        risk = _risk_result([0.5] * 40)
        results = tester.run(history, risk)
        scenarios_found = {r.scenario for r in results}
        assert len(scenarios_found) >= 4
