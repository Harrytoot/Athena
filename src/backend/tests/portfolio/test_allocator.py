import pytest

from app.portfolio.weight_optimizer import StrategyWeight, WeightResult
from app.portfolio.risk_budgeting import RiskBudget, RiskBudgetResult
from app.portfolio.allocator import CapitalAllocator, CapitalAllocation, AllocationResult


def _make_weight_result(strategy_ids, weights):
    sws = [
        StrategyWeight(
            strategy_id=sid,
            raw_sharpe=1.0,
            cost_adjusted_sharpe=0.9,
            volatility=0.01,
            stability_score=0.7,
            raw_weight=w,
            constrained_weight=w,
        )
        for sid, w in zip(strategy_ids, weights)
    ]
    return WeightResult(weights=sws)


def _make_risk_result(strategy_ids, risk_ratios):
    budgets = [
        RiskBudget(
            strategy_id=sid,
            weight=0.0,
            standalone_vol=0.01,
            marginal_risk=0.0,
            risk_contribution=0.0,
            risk_ratio=rr,
        )
        for sid, rr in zip(strategy_ids, risk_ratios)
    ]
    return RiskBudgetResult(budgets=budgets)


class TestCapitalAllocator:

    def test_empty_weights(self):
        allocator = CapitalAllocator(total_capital=500_000)
        result = allocator.allocate(WeightResult())
        assert len(result.allocations) == 0
        assert result.total_capital == 500_000

    def test_single_strategy_full_allocation(self):
        wr = _make_weight_result(["s1"], [1.0])
        allocator = CapitalAllocator(total_capital=1_000_000)
        result = allocator.allocate(wr)

        assert len(result.allocations) == 1
        assert result.allocations[0].capital == pytest.approx(1_000_000, rel=1e-4)
        assert result.deployed_capital == pytest.approx(1_000_000, rel=1e-4)

    def test_proportional_allocation(self):
        wr = _make_weight_result(["s1", "s2"], [0.6, 0.4])
        allocator = CapitalAllocator(total_capital=1_000_000)
        result = allocator.allocate(wr)

        assert len(result.allocations) == 2
        assert result.allocations[0].capital == pytest.approx(600_000, rel=1e-4)
        assert result.allocations[1].capital == pytest.approx(400_000, rel=1e-4)

    def test_cash_reserve(self):
        wr = _make_weight_result(["s1"], [1.0])
        allocator = CapitalAllocator(total_capital=1_000_000, cash_reserve_pct=0.10)
        result = allocator.allocate(wr)

        assert result.cash_reserve == pytest.approx(100_000, rel=1e-4)
        assert result.allocations[0].capital == pytest.approx(900_000, rel=1e-4)

    def test_deployment_ratio(self):
        wr = _make_weight_result(["s1", "s2"], [0.5, 0.5])
        allocator = CapitalAllocator(total_capital=1_000_000)
        result = allocator.allocate(wr)

        assert result.deployment_ratio == pytest.approx(1.0, rel=1e-4)

    def test_allocation_result_properties(self):
        wr = _make_weight_result(["s1", "s2", "s3"], [0.5, 0.3, 0.2])
        allocator = CapitalAllocator(total_capital=500_000)
        result = allocator.allocate(wr)

        assert result.max_single_concentration == pytest.approx(0.5, rel=1e-4)
        assert result.allocation_count == 3

    def test_capital_allocation_preserves_risk_info(self):
        wr = _make_weight_result(["s1", "s2"], [0.6, 0.4])
        rb = _make_risk_result(["s1", "s2"], [0.55, 0.45])

        allocator = CapitalAllocator(total_capital=1_000_000)
        result = allocator.allocate(wr, rb)

        assert result.allocations[0].risk_budget == pytest.approx(0.55, rel=1e-4)
        assert result.allocations[1].risk_budget == pytest.approx(0.45, rel=1e-4)

    def test_min_capital_per_strategy_skips_small(self):
        wr = _make_weight_result(["s1", "s2"], [0.95, 0.05])
        allocator = CapitalAllocator(
            total_capital=1_000_000,
            min_capital_per_strategy=100_000,
        )
        result = allocator.allocate(wr)

        assert result.allocation_count == 1
        s2_alloc = next(a for a in result.allocations if a.strategy_id == "s2")
        assert s2_alloc.capital == 0.0

    def test_max_capital_per_strategy_cap(self):
        wr = _make_weight_result(["s1", "s2"], [0.8, 0.2])
        allocator = CapitalAllocator(
            total_capital=1_000_000,
            max_capital_per_strategy=600_000,
        )
        result = allocator.allocate(wr)

        s1_alloc = next(a for a in result.allocations if a.strategy_id == "s1")
        assert s1_alloc.capital <= 600_000
        assert s1_alloc.capped_by_risk

    def test_zero_weight_strategy_gets_zero_capital(self):
        wr = _make_weight_result(["s1", "s2"], [1.0, 0.0])
        allocator = CapitalAllocator(total_capital=1_000_000)
        result = allocator.allocate(wr)

        s2_alloc = next(a for a in result.allocations if a.strategy_id == "s2")
        assert s2_alloc.capital == 0.0

    def test_reallocate_no_turnover(self):
        wr = _make_weight_result(["s1", "s2"], [0.6, 0.4])
        allocator = CapitalAllocator(total_capital=1_000_000)
        target = allocator.allocate(wr)

        new_allocations, trades = allocator.reallocate(
            target.allocations, wr
        )

        assert len(new_allocations) == 2
        assert sum(abs(t) for t in trades) == pytest.approx(0.0, abs=100)

    def test_reallocate_with_turnover_cap(self):
        wr_new = _make_weight_result(["s1", "s2"], [0.8, 0.2])
        allocator = CapitalAllocator(total_capital=1_000_000)

        current = [
            CapitalAllocation(strategy_id="s1", weight=0.5, capital=500_000, risk_budget=0.5),
            CapitalAllocation(strategy_id="s2", weight=0.5, capital=500_000, risk_budget=0.5),
        ]

        new_allocations, trades = allocator.reallocate(
            current, wr_new, max_turnover_pct=0.15
        )

        assert len(new_allocations) == 2
        total_turnover = sum(abs(t) for t in trades)
        max_turnover_amount = 1_000_000 * 0.15
        assert total_turnover <= max_turnover_amount * 2 + 1

    def test_reallocate_empty_inputs(self):
        allocator = CapitalAllocator(total_capital=1_000_000)
        result, trades = allocator.reallocate([], WeightResult())
        assert len(result) == 0
        assert len(trades) == 0

    def test_negative_weight_strategy_weights(self):
        wr = _make_weight_result(["s1", "s2"], [0.7, -0.3])
        allocator = CapitalAllocator(total_capital=1_000_000)
        result = allocator.allocate(wr)

        s2_alloc = next(a for a in result.allocations if a.strategy_id == "s2")
        assert s2_alloc.capital == 0.0
