from dataclasses import dataclass, field

from app.portfolio.weight_optimizer import StrategyWeight, WeightResult
from app.portfolio.risk_budgeting import RiskBudget, RiskBudgetResult

DEFAULT_CAPITAL = 1_000_000.0


@dataclass
class CapitalAllocation:
    strategy_id: str
    weight: float
    capital: float
    risk_budget: float
    capped_by_risk: bool = False


@dataclass
class AllocationResult:
    allocations: list[CapitalAllocation] = field(default_factory=list)
    total_capital: float = DEFAULT_CAPITAL
    deployed_capital: float = 0.0
    cash_reserve: float = 0.0

    @property
    def deployment_ratio(self) -> float:
        if self.total_capital == 0:
            return 0.0
        return self.deployed_capital / self.total_capital

    @property
    def max_single_concentration(self) -> float:
        if not self.allocations:
            return 0.0
        return max(a.weight for a in self.allocations)

    @property
    def allocation_count(self) -> int:
        return len([a for a in self.allocations if a.capital > 0])


class CapitalAllocator:

    def __init__(
        self,
        total_capital: float = DEFAULT_CAPITAL,
        min_capital_per_strategy: float = 0.0,
        max_capital_per_strategy: float | None = None,
        cash_reserve_pct: float = 0.0,
    ):
        self.total_capital = total_capital
        self.min_capital_per_strategy = min_capital_per_strategy
        self.max_capital_per_strategy = max_capital_per_strategy or float("inf")
        self.cash_reserve_pct = cash_reserve_pct

    def allocate(
        self,
        weight_result: WeightResult,
        risk_budget_result: RiskBudgetResult | None = None,
    ) -> AllocationResult:
        if not weight_result.weights:
            return AllocationResult(total_capital=self.total_capital)

        cash_reserve_amount = self.total_capital * self.cash_reserve_pct
        deployable = self.total_capital - cash_reserve_amount

        norm_weights = weight_result.normalized_weights
        risk_map: dict[str, float] = {}
        if risk_budget_result:
            risk_map = {b.strategy_id: b.risk_ratio for b in risk_budget_result.budgets}

        allocations: list[CapitalAllocation] = []
        deployed = 0.0

        for w, sw in zip(norm_weights, weight_result.weights):
            if w <= 0:
                raw_alloc = 0.0
            else:
                raw_alloc = deployable * w

                if raw_alloc < self.min_capital_per_strategy:
                    raw_alloc = 0.0

                if raw_alloc > self.max_capital_per_strategy:
                    raw_alloc = self.max_capital_per_strategy

            capped = abs(raw_alloc - deployable * w) > 1e-8 if w > 0 else False

            allocations.append(
                CapitalAllocation(
                    strategy_id=sw.strategy_id,
                    weight=round(w, 6),
                    capital=round(raw_alloc, 2),
                    risk_budget=round(risk_map.get(sw.strategy_id, 0.0), 6),
                    capped_by_risk=capped,
                )
            )
            deployed += raw_alloc

        return AllocationResult(
            allocations=allocations,
            total_capital=self.total_capital,
            deployed_capital=round(deployed, 2),
            cash_reserve=round(self.total_capital - deployed, 2),
        )

    def reallocate(
        self,
        current_allocations: list[CapitalAllocation],
        target_weights: WeightResult,
        max_turnover_pct: float = 0.30,
    ) -> tuple[list[CapitalAllocation], list[float]]:
        if not target_weights.weights or not current_allocations:
            return current_allocations, []

        actual_capital = sum(a.capital for a in current_allocations)
        target_allocs = self._compute_target_allocations(
            target_weights, actual_capital
        )

        current_map = {a.strategy_id: a.capital for a in current_allocations}
        target_map = {a.strategy_id: a.capital for a in target_allocs}

        all_ids = set(current_map.keys()) | set(target_map.keys())
        total_deviation = 0.0
        trades: list[float] = []

        for sid in all_ids:
            current = current_map.get(sid, 0.0)
            target = target_map.get(sid, 0.0)
            deviation = abs(target - current)
            total_deviation += deviation

        if actual_capital > 0:
            turnover_ratio = total_deviation / (2 * actual_capital)

            if turnover_ratio > max_turnover_pct:
                scale = max_turnover_pct / turnover_ratio
                adjusted: dict[str, float] = {}
                for sid in all_ids:
                    current = current_map.get(sid, 0.0)
                    target = target_map.get(sid, 0.0)
                    delta = (target - current) * scale
                    adjusted[sid] = current + delta
                    trades.append(delta)

                result = [
                    CapitalAllocation(
                        strategy_id=sid,
                        weight=0.0,
                        capital=round(adjusted.get(sid, 0.0), 2),
                        risk_budget=0.0,
                    )
                    for sid in all_ids
                ]
                return result, trades

        return target_allocs, [target_map.get(sid, 0.0) - current_map.get(sid, 0.0) for sid in all_ids]

    def _compute_target_allocations(
        self, weight_result: WeightResult, actual_capital: float
    ) -> list[CapitalAllocation]:
        norm_weights = weight_result.normalized_weights
        return [
            CapitalAllocation(
                strategy_id=sw.strategy_id,
                weight=round(w, 6),
                capital=round(actual_capital * w, 2),
                risk_budget=0.0,
            )
            for w, sw in zip(norm_weights, weight_result.weights)
        ]
