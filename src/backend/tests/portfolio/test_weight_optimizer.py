import pytest

from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.robustness_report import RobustnessReport, CostAdjustedMetrics, StabilityMetrics
from app.portfolio.weight_optimizer import WeightOptimizer, StrategyWeight, WeightResult, DEFAULT_MAX_WEIGHT, DEFAULT_MIN_WEIGHT


def _make_perf(sharpe=1.0, daily_vol=0.01, calmar=1.0, max_dd=-0.10, annual_ret=0.15, total_ret=0.30):
    return StrategyPerformanceReport(
        total_return=total_ret,
        annualized_return=annual_ret,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        max_drawdown_duration=5,
        win_rate=0.55,
        avg_daily_return=0.001,
        daily_volatility=daily_vol,
        calmar_ratio=calmar,
        total_days=252,
        avg_leverage=0.5,
    )


def _make_robust(cost_sharpe=0.9, stability=0.7, friction_ratio=0.01):
    return RobustnessReport(
        cost_metrics=CostAdjustedMetrics(
            raw_sharpe=1.0,
            cost_adjusted_sharpe=cost_sharpe,
            total_transaction_costs=100.0,
            cost_ratio=0.01,
            total_slippage=50.0,
            slippage_ratio=0.005,
            total_market_impact=30.0,
            impact_ratio=0.003,
            total_friction=180.0,
            friction_ratio=friction_ratio,
        ),
        stability=StabilityMetrics(
            perturbation_stability=stability,
            perturbation_mean_sharpe=cost_sharpe,
            perturbation_sharpe_std=0.1,
            stress_scenarios_passed=5,
            stress_scenarios_total=6,
            stress_resilience_score=0.83,
        ),
        overall_stability_score=stability,
        overall_assessment="good",
    )


class TestWeightOptimizer:

    def test_empty_input(self):
        opt = WeightOptimizer()
        result = opt.optimize([])
        assert isinstance(result, WeightResult)
        assert len(result.weights) == 0

    def test_single_strategy_gets_full_weight(self):
        perf = _make_perf(sharpe=1.5)
        robust = _make_robust(cost_sharpe=1.3, stability=0.8)
        data = [("strat_a", perf, robust)]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        assert len(result.weights) == 1
        assert result.weights[0].constrained_weight == pytest.approx(1.0, rel=1e-4)
        assert result.total_weight == pytest.approx(1.0, rel=1e-4)

    def test_two_strategies_equal_quality(self):
        perf = _make_perf(sharpe=1.0)
        robust = _make_robust(cost_sharpe=0.9, stability=0.7)
        data = [
            ("strat_a", perf, robust),
            ("strat_b", perf, robust),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        assert len(result.weights) == 2
        assert result.weights[0].constrained_weight == pytest.approx(0.5, rel=1e-2)
        assert result.weights[1].constrained_weight == pytest.approx(0.5, rel=1e-2)

    def test_better_strategy_gets_higher_weight(self):
        perf_good = _make_perf(sharpe=2.0)
        perf_bad = _make_perf(sharpe=0.5, calmar=0.5, daily_vol=0.03)
        robust_good = _make_robust(cost_sharpe=1.8, stability=0.8)
        robust_bad = _make_robust(cost_sharpe=0.4, stability=0.4, friction_ratio=0.05)

        data = [
            ("strat_good", perf_good, robust_good),
            ("strat_bad", perf_bad, robust_bad),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        good_weight = result.weights[0].raw_weight
        bad_weight = result.weights[1].raw_weight
        assert good_weight > bad_weight

    def test_max_weight_cap(self):
        perf = _make_perf(sharpe=3.0)
        robust = _make_robust(cost_sharpe=2.5, stability=0.9)
        data = [
            ("strat_a", perf, robust),
            ("strat_b", _make_perf(sharpe=0.2), _make_robust(cost_sharpe=0.1, stability=0.3)),
        ]

        opt = WeightOptimizer(max_weight=0.60)
        result = opt.optimize(data)

        assert result.weights[0].constrained_weight <= 0.60 + 1e-4
        assert result.weights[0].capped

    def test_min_weight_floor(self):
        perf_a = _make_perf(sharpe=3.0)
        perf_b = _make_perf(sharpe=0.1, daily_vol=0.05)
        robust_a = _make_robust(cost_sharpe=2.5, stability=0.9)
        robust_b = _make_robust(cost_sharpe=0.05, stability=0.2)

        data = [
            ("strat_a", perf_a, robust_a),
            ("strat_b", perf_b, robust_b),
        ]

        opt = WeightOptimizer(min_weight=0.1)
        result = opt.optimize(data)

        assert result.weights[1].constrained_weight >= 0.1

    def test_regime_multipliers(self):
        perf = _make_perf(sharpe=1.0)
        robust = _make_robust(cost_sharpe=0.9, stability=0.7)
        data = [
            ("strat_a", perf, robust),
            ("strat_b", perf, robust),
        ]

        opt = WeightOptimizer(max_weight=1.0)
        regime = {"strat_a": 2.0, "strat_b": 0.5}
        result = opt.optimize(data, regime_multipliers=regime)

        assert result.weights[0].constrained_weight > result.weights[1].constrained_weight

    def test_normalized_weights_sum_to_one(self):
        perf = _make_perf(sharpe=1.2)
        robust = _make_robust(cost_sharpe=1.0, stability=0.7)
        data = [
            ("s1", perf, robust),
            ("s2", _make_perf(sharpe=0.8), _make_robust(cost_sharpe=0.7)),
            ("s3", _make_perf(sharpe=1.5), _make_robust(cost_sharpe=1.3)),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        assert sum(result.normalized_weights) == pytest.approx(1.0, rel=1e-4)

    def test_negative_sharpe_gets_zero_weight(self):
        perf_neg = _make_perf(sharpe=-0.5)
        perf_pos = _make_perf(sharpe=1.0)
        robust_neg = _make_robust(cost_sharpe=-0.4, stability=0.3)
        robust_pos = _make_robust(cost_sharpe=0.9, stability=0.7)

        data = [
            ("bad", perf_neg, robust_neg),
            ("good", perf_pos, robust_pos),
        ]

        opt = WeightOptimizer(min_acceptable_sharpe=0.0)
        result = opt.optimize(data)

        bad_weights = [w for w in result.weights if w.strategy_id == "bad"]
        assert bad_weights[0].constrained_weight == pytest.approx(0.0, abs=1e-4)

    def test_weight_result_properties(self):
        perf = _make_perf(sharpe=1.5)
        robust = _make_robust(cost_sharpe=1.3, stability=0.8)
        data = [
            ("s1", perf, robust),
            ("s2", _make_perf(sharpe=0.8), _make_robust(cost_sharpe=0.6)),
            ("s3", _make_perf(sharpe=1.0), _make_robust(cost_sharpe=0.9)),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        assert 0 < result.concentration_ratio <= 1.0
        assert result.effective_n >= 1.0
        assert isinstance(result.weighted_sharpe, float)

    def test_volatility_normalization(self):
        perf_high_vol = _make_perf(sharpe=1.0, daily_vol=0.04)
        perf_low_vol = _make_perf(sharpe=1.0, daily_vol=0.01)
        robust_high = _make_robust(cost_sharpe=0.9)
        robust_low = _make_robust(cost_sharpe=0.9)

        data = [
            ("high_vol", perf_high_vol, robust_high),
            ("low_vol", perf_low_vol, robust_low),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        low_vol_w = next(w for w in result.weights if w.strategy_id == "low_vol").raw_weight
        high_vol_w = next(w for w in result.weights if w.strategy_id == "high_vol").raw_weight
        assert low_vol_w > high_vol_w

    def test_calmar_drawdown_scoring(self):
        perf_bad_dd = _make_perf(sharpe=1.0, calmar=0.3, max_dd=-0.40)
        perf_good = _make_perf(sharpe=1.0, calmar=2.0, max_dd=-0.05)

        data = [
            ("bad_dd", perf_bad_dd, _make_robust()),
            ("good", perf_good, _make_robust()),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        good_w = next(w for w in result.weights if w.strategy_id == "good").raw_weight
        bad_w = next(w for w in result.weights if w.strategy_id == "bad_dd").raw_weight
        assert good_w > bad_w

    def test_stability_affects_weight(self):
        perf = _make_perf(sharpe=1.0)
        robust_high = _make_robust(stability=0.9)
        robust_low = _make_robust(stability=0.2)

        data = [
            ("stable", perf, robust_high),
            ("unstable", perf, robust_low),
        ]

        opt = WeightOptimizer()
        result = opt.optimize(data)

        stable_w = next(w for w in result.weights if w.strategy_id == "stable").raw_weight
        unstable_w = next(w for w in result.weights if w.strategy_id == "unstable").raw_weight
        assert stable_w > unstable_w

    def test_all_negative_sharpes_equal_weight(self):
        perf_a = _make_perf(sharpe=-0.5)
        perf_b = _make_perf(sharpe=-0.8)
        robust_a = _make_robust(cost_sharpe=-0.4, stability=0.2)
        robust_b = _make_robust(cost_sharpe=-0.7, stability=0.1)

        data = [
            ("a", perf_a, robust_a),
            ("b", perf_b, robust_b),
        ]

        opt = WeightOptimizer(min_acceptable_sharpe=-1.0)
        result = opt.optimize(data)

        assert result.weights[0].constrained_weight == pytest.approx(0.5, abs=0.05)
        assert result.weights[1].constrained_weight == pytest.approx(0.5, abs=0.05)
