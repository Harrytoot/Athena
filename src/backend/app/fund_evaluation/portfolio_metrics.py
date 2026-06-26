import math
from dataclasses import dataclass, field

from app.portfolio.portfolio_engine import StrategyInput

TRADING_DAYS = 252.0
DEFAULT_WINDOW = 60
MIN_WINDOW = 20


@dataclass
class RollingSharpePoint:
    start_idx: int
    end_idx: int
    sharpe: float
    annualized_return: float
    annualized_volatility: float


@dataclass
class DistributionStats:
    mean: float
    std: float
    skewness: float
    kurtosis: float
    min_val: float
    max_val: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float


@dataclass
class MonthlyReturn:
    month: int
    year: int
    monthly_return: float
    trading_days: int


@dataclass
class PortfolioStabilityMetrics:
    rolling_sharpes: list[RollingSharpePoint] = field(default_factory=list)
    mean_rolling_sharpe: float = 0.0
    std_rolling_sharpe: float = 0.0
    sharpe_stability: float = 0.0
    distribution: DistributionStats | None = None
    positive_day_ratio: float = 0.0
    monthly_returns: list[MonthlyReturn] = field(default_factory=list)
    monthly_win_rate: float = 0.0
    avg_monthly_return: float = 0.0
    annualized_sharpe: float = 0.0


class PortfolioMetricsAnalyzer:

    def __init__(
        self,
        window_size: int = DEFAULT_WINDOW,
        risk_free_rate: float = 0.02,
    ):
        self.window_size = max(window_size, MIN_WINDOW)
        self.risk_free_rate = risk_free_rate

    def analyze(
        self,
        strategies: list[StrategyInput],
        weights: list[float],
    ) -> PortfolioStabilityMetrics:
        if not strategies or not weights:
            return PortfolioStabilityMetrics()

        daily_returns = self._compute_portfolio_returns(strategies, weights)
        if not daily_returns:
            return PortfolioStabilityMetrics()

        rolling = self._compute_rolling_sharpe(daily_returns)
        dist = self._compute_distribution(daily_returns)
        monthly = self._compute_monthly_returns(daily_returns)
        pos_ratio = sum(1 for r in daily_returns if r > 0) / len(daily_returns)

        annual_sharpe = self._compute_annualized_sharpe(daily_returns)

        if rolling:
            sharpes = [p.sharpe for p in rolling]
            mean_rs = sum(sharpes) / len(sharpes)
            var = sum((s - mean_rs) ** 2 for s in sharpes) / len(sharpes)
            std_rs = math.sqrt(var)
            stability = max(0.0, min(1.0, 1.0 - std_rs / abs(mean_rs))) if mean_rs != 0 else 0.0
        else:
            mean_rs = 0.0
            std_rs = 0.0
            stability = 0.0

        monthly_wins = sum(1 for m in monthly if m.monthly_return > 0)
        monthly_win_rate = monthly_wins / len(monthly) if monthly else 0.0
        avg_monthly = sum(m.monthly_return for m in monthly) / len(monthly) if monthly else 0.0

        return PortfolioStabilityMetrics(
            rolling_sharpes=rolling,
            mean_rolling_sharpe=round(mean_rs, 6),
            std_rolling_sharpe=round(std_rs, 6),
            sharpe_stability=round(stability, 4),
            distribution=dist,
            positive_day_ratio=round(pos_ratio, 6),
            monthly_returns=monthly,
            monthly_win_rate=round(monthly_win_rate, 6),
            avg_monthly_return=round(avg_monthly, 6),
            annualized_sharpe=round(annual_sharpe, 6),
        )

    def _compute_portfolio_returns(
        self,
        strategies: list[StrategyInput],
        weights: list[float],
    ) -> list[float]:
        return_lists: list[list[float]] = []
        for s in strategies:
            if s.history and s.history.snapshots:
                return_lists.append(s.history.daily_returns)
            else:
                return_lists.append([])

        if not return_lists or all(len(rl) == 0 for rl in return_lists):
            return []

        min_len = min(len(rl) for rl in return_lists if len(rl) > 0)
        valid_indices = [i for i, rl in enumerate(return_lists) if len(rl) > 0]

        if not valid_indices:
            return []

        effective_weights = [weights[i] for i in valid_indices]
        weight_sum = sum(effective_weights)
        if weight_sum == 0:
            return []
        norm_w = [w / weight_sum for w in effective_weights]

        portfolio_returns: list[float] = []
        for t in range(min_len):
            daily_r = sum(
                norm_w[j] * return_lists[valid_indices[j]][t]
                for j in range(len(valid_indices))
            )
            portfolio_returns.append(round(daily_r, 8))

        return portfolio_returns

    def _compute_rolling_sharpe(
        self,
        daily_returns: list[float],
    ) -> list[RollingSharpePoint]:
        n = len(daily_returns)
        if n < self.window_size:
            return []

        daily_rf = self.risk_free_rate / TRADING_DAYS
        points: list[RollingSharpePoint] = []

        for i in range(self.window_size, n + 1):
            window = daily_returns[i - self.window_size:i]
            mean_r = sum(window) / self.window_size
            excess = mean_r - daily_rf
            var = sum((r - mean_r) ** 2 for r in window) / (self.window_size - 1)
            vol = math.sqrt(max(0.0, var))
            if vol > 0:
                daily_sharpe = excess / vol
                sharpe = daily_sharpe * math.sqrt(TRADING_DAYS)
            else:
                sharpe = 0.0
            ann_ret = (1.0 + mean_r) ** TRADING_DAYS - 1.0
            ann_vol = vol * math.sqrt(TRADING_DAYS)

            points.append(
                RollingSharpePoint(
                    start_idx=i - self.window_size,
                    end_idx=i - 1,
                    sharpe=round(sharpe, 6),
                    annualized_return=round(ann_ret, 6),
                    annualized_volatility=round(ann_vol, 6),
                )
            )

        return points

    def _compute_distribution(self, returns: list[float]) -> DistributionStats:
        n = len(returns)
        if n < 2:
            return DistributionStats(
                mean=0.0, std=0.0, skewness=0.0, kurtosis=0.0,
                min_val=0.0, max_val=0.0,
                var_95=0.0, var_99=0.0, cvar_95=0.0, cvar_99=0.0,
            )

        mean_r = sum(returns) / n
        var = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
        std_r = math.sqrt(max(0.0, var))

        skew = 0.0
        kurt = 0.0
        if std_r > 0:
            skew = sum((r - mean_r) ** 3 for r in returns) / (n * std_r ** 3)
            kurt = sum((r - mean_r) ** 4 for r in returns) / (n * std_r ** 4) - 3.0

        sorted_returns = sorted(returns)
        var_95 = self._percentile(sorted_returns, 0.05)
        var_99 = self._percentile(sorted_returns, 0.01)
        cvar_95 = self._cvar(sorted_returns, var_95)
        cvar_99 = self._cvar(sorted_returns, var_99)

        return DistributionStats(
            mean=round(mean_r, 8),
            std=round(std_r, 8),
            skewness=round(skew, 6),
            kurtosis=round(kurt, 6),
            min_val=round(min(returns), 6),
            max_val=round(max(returns), 6),
            var_95=round(var_95, 6),
            var_99=round(var_99, 6),
            cvar_95=round(cvar_95, 6),
            cvar_99=round(cvar_99, 6),
        )

    def _percentile(self, sorted_data: list[float], p: float) -> float:
        n = len(sorted_data)
        if n == 0:
            return 0.0
        idx = int(n * p)
        idx = max(0, min(n - 1, idx))
        return sorted_data[idx]

    def _cvar(self, sorted_data: list[float], var: float) -> float:
        tail = [r for r in sorted_data if r <= var]
        if not tail:
            return var
        return sum(tail) / len(tail)

    def _compute_monthly_returns(self, daily_returns: list[float]) -> list[MonthlyReturn]:
        if not daily_returns:
            return []

        trade_days_per_month = 21
        monthly: list[MonthlyReturn] = []
        idx = 0
        month_counter = 1

        while idx < len(daily_returns):
            end = min(idx + trade_days_per_month, len(daily_returns))
            month_returns = daily_returns[idx:end]
            cum_return = 1.0
            for r in month_returns:
                cum_return *= (1.0 + r)
            month_r = cum_return - 1.0
            year = 2020 + (month_counter - 1) // 12
            month = ((month_counter - 1) % 12) + 1

            monthly.append(
                MonthlyReturn(
                    month=month,
                    year=year,
                    monthly_return=round(month_r, 6),
                    trading_days=len(month_returns),
                )
            )
            idx = end
            month_counter += 1

        return monthly

    def _compute_annualized_sharpe(self, daily_returns: list[float]) -> float:
        n = len(daily_returns)
        if n < 2:
            return 0.0
        mean_r = sum(daily_returns) / n
        var = sum((r - mean_r) ** 2 for r in daily_returns) / (n - 1)
        vol = math.sqrt(max(0.0, var))
        if vol == 0:
            return 0.0
        daily_rf = self.risk_free_rate / TRADING_DAYS
        daily_sharpe = (mean_r - daily_rf) / vol
        return daily_sharpe * math.sqrt(TRADING_DAYS)
