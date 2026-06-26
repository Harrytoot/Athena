import math
from dataclasses import dataclass, field

from app.portfolio.weight_optimizer import StrategyWeight, WeightResult

TRADING_DAYS = 252.0


@dataclass
class RiskBudget:
    strategy_id: str
    weight: float
    standalone_vol: float
    marginal_risk: float
    risk_contribution: float
    risk_ratio: float


@dataclass
class RiskConstraint:
    max_portfolio_vol: float = 0.25
    max_single_risk_ratio: float = 0.40
    target_portfolio_vol: float = 0.15
    use_risk_parity: bool = False


@dataclass
class RiskBudgetResult:
    budgets: list[RiskBudget] = field(default_factory=list)
    portfolio_vol: float = 0.0
    constrained: bool = False
    constraint_details: str = ""

    @property
    def risk_concentration(self) -> float:
        if not self.budgets:
            return 0.0
        ratios = [b.risk_ratio for b in self.budgets]
        return sum(r ** 2 for r in ratios)

    @property
    def effective_n_risk(self) -> float:
        rc = self.risk_concentration
        if rc == 0:
            return 0.0
        return 1.0 / rc


class RiskBudgeting:

    def __init__(self, constraint: RiskConstraint | None = None):
        self.constraint = constraint or RiskConstraint()

    def compute_risk_budgets(
        self,
        weight_result: WeightResult,
        volatilities: dict[str, float],
        correlation_matrix: dict[str, dict[str, float]] | None = None,
    ) -> RiskBudgetResult:
        if not weight_result.weights:
            return RiskBudgetResult()

        norm_weights = weight_result.normalized_weights
        c = self.constraint

        n = len(norm_weights)

        if correlation_matrix is None:
            correlation_matrix = self._default_correlation_matrix(
                [w.strategy_id for w in weight_result.weights]
            )

        portfolio_vol = self._compute_portfolio_vol(
            weight_result, volatilities, correlation_matrix
        )

        constrained = False
        details = ""
        adjusted_weights = list(norm_weights)

        if portfolio_vol > c.max_portfolio_vol:
            scale = c.max_portfolio_vol / portfolio_vol
            adjusted_weights = [w * scale for w in adjusted_weights]
            total = sum(adjusted_weights)
            adjusted_weights = [w / total for w in adjusted_weights]
            portfolio_vol = c.max_portfolio_vol
            constrained = True
            details = f"vol_capped:{c.max_portfolio_vol:.4f}"

        budgets: list[RiskBudget] = []
        for i, sw in enumerate(weight_result.weights):
            vol = volatilities.get(sw.strategy_id, sw.volatility)
            marginal = self._marginal_risk(
                i, adjusted_weights, list(volatilities.values()), correlation_matrix
            )
            risk_contribution = adjusted_weights[i] * marginal
            risk_ratio = risk_contribution / portfolio_vol if portfolio_vol > 0 else 0.0

            if risk_ratio > c.max_single_risk_ratio:
                constrained = True
                details = self._append_detail(
                    details, f"{sw.strategy_id}_risk_ratio_capped:{risk_ratio:.4f}"
                )

            budgets.append(
                RiskBudget(
                    strategy_id=sw.strategy_id,
                    weight=round(adjusted_weights[i], 6),
                    standalone_vol=round(vol, 6),
                    marginal_risk=round(marginal, 6),
                    risk_contribution=round(risk_contribution, 6),
                    risk_ratio=round(risk_ratio, 6),
                )
            )

        return RiskBudgetResult(
            budgets=budgets,
            portfolio_vol=round(portfolio_vol, 6),
            constrained=constrained,
            constraint_details=details,
        )

    def compute_risk_parity_weights(
        self,
        weight_result: WeightResult,
        volatilities: dict[str, float],
        correlation_matrix: dict[str, dict[str, float]] | None = None,
        max_iterations: int = 50,
    ) -> list[float]:
        n = len(weight_result.weights)
        if n < 2:
            return weight_result.normalized_weights

        ids = [w.strategy_id for w in weight_result.weights]
        vols = [volatilities.get(sid, 0.01) for sid in ids]

        if correlation_matrix is None:
            correlation_matrix = self._default_correlation_matrix(ids)

        weights = [1.0 / n] * n

        for _ in range(max_iterations):
            marginal_risks = [
                self._marginal_risk(i, weights, vols, correlation_matrix)
                for i in range(n)
            ]
            risk_contributions = [weights[i] * marginal_risks[i] for i in range(n)]

            if all(rc > 0 for rc in risk_contributions):
                target_rc = 1.0 / n
                new_weights = [target_rc / rc for rc in risk_contributions]
                total = sum(new_weights)
                weights = [w / total for w in new_weights]
            else:
                break

        return [round(w, 6) for w in weights]

    def _compute_portfolio_vol(
        self,
        weight_result: WeightResult,
        volatilities: dict[str, float],
        correlation_matrix: dict[str, dict[str, float]],
    ) -> float:
        norm = weight_result.normalized_weights
        ids = [w.strategy_id for w in weight_result.weights]
        n = len(ids)
        if n == 0:
            return 0.0

        variance = 0.0
        for i in range(n):
            for j in range(n):
                vol_i = volatilities.get(ids[i], weight_result.weights[i].volatility)
                vol_j = volatilities.get(ids[j], weight_result.weights[j].volatility)
                rho = correlation_matrix.get(ids[i], {}).get(ids[j], 0.3 if i != j else 1.0)
                variance += norm[i] * norm[j] * vol_i * vol_j * rho * TRADING_DAYS

        return math.sqrt(max(0.0, variance))

    def _marginal_risk(
        self,
        idx: int,
        weights: list[float],
        vols: list[float],
        correlation_matrix: dict[str, dict[str, float]],
    ) -> float:
        n = len(weights)
        portfolio_var = 0.0
        for i in range(n):
            for j in range(n):
                rho = correlation_matrix.get(str(i), {}).get(str(j), 0.3 if i != j else 1.0)
                portfolio_var += weights[i] * weights[j] * vols[i] * vols[j] * rho * TRADING_DAYS

        portfolio_vol = math.sqrt(max(0.0, portfolio_var))
        if portfolio_vol == 0:
            return 0.0

        cov_sum = 0.0
        for j in range(n):
            rho = correlation_matrix.get(str(idx), {}).get(str(j), 0.3 if idx != j else 1.0)
            cov_sum += weights[j] * vols[idx] * vols[j] * rho * TRADING_DAYS

        return cov_sum / portfolio_vol

    def _default_correlation_matrix(
        self, strategy_ids: list[str]
    ) -> dict[str, dict[str, float]]:
        matrix: dict[str, dict[str, float]] = {}
        for i, id_i in enumerate(strategy_ids):
            matrix[id_i] = {}
            for j, id_j in enumerate(strategy_ids):
                matrix[id_i][id_j] = 1.0 if i == j else 0.3
        return matrix

    def _append_detail(self, current: str, detail: str) -> str:
        return f"{current};{detail}" if current else detail
