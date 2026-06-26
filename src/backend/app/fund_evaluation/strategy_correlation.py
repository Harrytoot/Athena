import math
from dataclasses import dataclass, field
from statistics import mean as stat_mean

from app.portfolio.portfolio_engine import StrategyInput

TRADING_DAYS = 252.0


@dataclass
class CorrelationMatrix:
    strategy_ids: list[str] = field(default_factory=list)
    pearson: list[list[float]] = field(default_factory=list)
    spearman: list[list[float]] = field(default_factory=list)
    avg_pearson: float = 0.0
    avg_spearman: float = 0.0
    min_pearson: float = 0.0
    max_pearson: float = 0.0
    n_observations: int = 0

    @property
    def is_positive_definite(self) -> bool:
        return self.avg_pearson > -1.0 / (len(self.strategy_ids) - 1) if len(self.strategy_ids) > 1 else True

    def get_pearson(self, id_i: str, id_j: str) -> float:
        if id_i not in self.strategy_ids or id_j not in self.strategy_ids:
            return 0.0
        i = self.strategy_ids.index(id_i)
        j = self.strategy_ids.index(id_j)
        return self.pearson[i][j] if i < len(self.pearson) and j < len(self.pearson[i]) else 0.0


@dataclass
class StrategyCorrelationResult:
    correlation_matrix: CorrelationMatrix = field(default_factory=CorrelationMatrix)
    diversification_ratio: float = 0.0
    effective_n: float = 0.0
    avg_pairwise_corr: float = 0.0


class StrategyCorrelationAnalyzer:

    def analyze(
        self,
        strategies: list[StrategyInput],
        correlation_matrix_input: dict[str, dict[str, float]] | None = None,
    ) -> StrategyCorrelationResult:
        if not strategies or len(strategies) < 2:
            return StrategyCorrelationResult()

        ids = [s.strategy_id for s in strategies]

        return_lists, n_obs = self._align_returns(strategies)

        if return_lists and n_obs >= 3:
            pearson = self._pearson_matrix(return_lists)
            spearman = self._spearman_matrix(return_lists)
            avg_pearson, min_pearson, max_pearson = self._corr_stats(pearson, len(ids))
            avg_spearman = self._avg_off_diag(spearman, len(ids))
        elif correlation_matrix_input:
            n_ids = len(ids)
            pearson = [[0.0] * n_ids for _ in range(n_ids)]
            spearman = [[0.0] * n_ids for _ in range(n_ids)]
            for i, id_i in enumerate(ids):
                for j, id_j in enumerate(ids):
                    if i == j:
                        pearson[i][j] = 1.0
                        spearman[i][j] = 1.0
                    else:
                        val = correlation_matrix_input.get(id_i, {}).get(id_j, 0.3)
                        pearson[i][j] = val
                        spearman[i][j] = val
            avg_pearson, min_pearson, max_pearson = self._corr_stats(pearson, len(ids))
            avg_spearman = avg_pearson
        else:
            return StrategyCorrelationResult(
                correlation_matrix=CorrelationMatrix(strategy_ids=ids),
            )

        avg_pairwise = avg_pearson

        div_ratio, eff_n = self._compute_diversification(strategies, pearson, ids)

        matrix = CorrelationMatrix(
            strategy_ids=ids,
            pearson=pearson,
            spearman=spearman,
            avg_pearson=round(avg_pearson, 6),
            avg_spearman=round(avg_spearman, 6),
            min_pearson=round(min_pearson, 6),
            max_pearson=round(max_pearson, 6),
            n_observations=n_obs,
        )

        return StrategyCorrelationResult(
            correlation_matrix=matrix,
            diversification_ratio=round(div_ratio, 6),
            effective_n=round(eff_n, 4),
            avg_pairwise_corr=round(avg_pairwise, 6),
        )

    def _align_returns(
        self,
        strategies: list[StrategyInput],
    ) -> tuple[list[list[float]], int]:
        ret_lists: list[list[float]] = []
        for s in strategies:
            if s.history and s.history.snapshots:
                ret_lists.append(s.history.daily_returns)
            else:
                return [], 0

        if not ret_lists:
            return [], 0

        min_len = min(len(rl) for rl in ret_lists)
        if min_len < 3:
            return [], 0

        aligned = [rl[:min_len] for rl in ret_lists]
        return aligned, min_len

    def _pearson_matrix(
        self,
        return_lists: list[list[float]],
    ) -> list[list[float]]:
        n = len(return_lists)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                corr = self._pearson_correlation(return_lists[i], return_lists[j])
                matrix[i][j] = corr
                matrix[j][i] = corr
        return matrix

    def _spearman_matrix(
        self,
        return_lists: list[list[float]],
    ) -> list[list[float]]:
        n = len(return_lists)
        matrix = [[0.0] * n for _ in range(n)]

        def rank(values: list[float]) -> list[float]:
            indexed = sorted((v, idx) for idx, v in enumerate(values))
            ranks = [0.0] * len(values)
            for pos, (_, idx) in enumerate(indexed):
                ranks[idx] = float(pos + 1)
            return ranks

        ranked = [rank(rl) for rl in return_lists]

        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                corr = self._pearson_correlation(ranked[i], ranked[j])
                matrix[i][j] = corr
                matrix[j][i] = corr
        return matrix

    def _pearson_correlation(self, x: list[float], y: list[float]) -> float:
        n_val = len(x)
        if n_val < 3 or len(y) != n_val:
            return 0.0
        mx = sum(x) / n_val
        my = sum(y) / n_val
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n_val))
        sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
        sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
        if sx == 0 or sy == 0:
            return 0.0
        return round(cov / (sx * sy), 6)

    def _corr_stats(
        self,
        matrix: list[list[float]],
        n: int,
    ) -> tuple[float, float, float]:
        off_diag: list[float] = []
        for i in range(n):
            for j in range(i + 1, n):
                off_diag.append(matrix[i][j])
        if not off_diag:
            return 0.0, 0.0, 0.0
        avg = sum(off_diag) / len(off_diag)
        min_c = min(off_diag)
        max_c = max(off_diag)
        return avg, min_c, max_c

    def _avg_off_diag(self, matrix: list[list[float]], n: int) -> float:
        off_diag: list[float] = []
        for i in range(n):
            for j in range(i + 1, n):
                off_diag.append(matrix[i][j])
        if not off_diag:
            return 0.0
        return sum(off_diag) / len(off_diag)

    def _compute_diversification(
        self,
        strategies: list[StrategyInput],
        pearson: list[list[float]],
        ids: list[str],
    ) -> tuple[float, float]:
        n = len(ids)
        if n < 2:
            return 1.0, 1.0

        volatilities = [
            s.performance.daily_volatility * math.sqrt(TRADING_DAYS)
            for s in strategies
        ]
        equal_w = 1.0 / n

        weighted_vol = sum(equal_w * v for v in volatilities)

        port_var = 0.0
        for i in range(n):
            for j in range(n):
                port_var += equal_w * equal_w * volatilities[i] * volatilities[j] * pearson[i][j]
        port_vol = math.sqrt(max(0.0, port_var))

        div_ratio = weighted_vol / port_vol if port_vol > 0 else 1.0

        avg_corr = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                avg_corr += pearson[i][j]
                count += 1
        avg_corr = avg_corr / count if count > 0 else 0.0

        if abs(avg_corr) > 1.0 - 1e-10:
            eff_n = 1.0
        elif avg_corr < 0 and n > 2:
            eff_n = float(n) / (1.0 + (n - 1) * avg_corr)
        elif avg_corr <= 0:
            eff_n = float(n)
        else:
            denom = 1.0 + (n - 1) * avg_corr
            eff_n = float(n) / denom if denom > 0 else 1.0

        return div_ratio, eff_n
