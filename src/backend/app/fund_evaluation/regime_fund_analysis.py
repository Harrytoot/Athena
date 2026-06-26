import math
from dataclasses import dataclass, field

from app.portfolio.portfolio_engine import StrategyInput

TRADING_DAYS = 252.0
REGIME_LOOKBACK = 60
BULL_THRESHOLD = 0.05
BEAR_THRESHOLD = -0.05


@dataclass
class RegimePeriod:
    regime: str
    start_idx: int
    end_idx: int
    n_days: int
    total_return: float
    annualized_return: float
    sharpe: float
    max_drawdown: float
    volatility: float


@dataclass
class FundRegimeResult:
    periods: list[RegimePeriod] = field(default_factory=list)
    bull_ratio: float = 0.0
    bear_ratio: float = 0.0
    sideways_ratio: float = 0.0
    bull_sharpe: float = 0.0
    bear_sharpe: float = 0.0
    sideways_sharpe: float = 0.0
    regime_consistency: float = 0.0
    max_regime_drawdown: str = ""


class FundRegimeAnalyzer:

    def __init__(
        self,
        lookback: int = REGIME_LOOKBACK,
        bull_threshold: float = BULL_THRESHOLD,
        bear_threshold: float = BEAR_THRESHOLD,
    ):
        self.lookback = lookback
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold

    def analyze(
        self,
        strategies: list[StrategyInput],
        weights: list[float],
        risk_free_rate: float = 0.02,
    ) -> FundRegimeResult:
        if not strategies or not weights:
            return FundRegimeResult()

        daily_returns = self._compute_portfolio_returns(strategies, weights)
        if len(daily_returns) < self.lookback:
            return FundRegimeResult()

        regimes = self._classify_regimes(daily_returns)
        periods = self._identify_periods(daily_returns, regimes, risk_free_rate)

        bull_days = sum(p.n_days for p in periods if p.regime == "Bull")
        bear_days = sum(p.n_days for p in periods if p.regime == "Bear")
        sideways_days = sum(p.n_days for p in periods if p.regime == "Sideways")
        total_days = bull_days + bear_days + sideways_days

        bull_r = bull_days / total_days if total_days > 0 else 0.0
        bear_r = bear_days / total_days if total_days > 0 else 0.0
        sideways_r = sideways_days / total_days if total_days > 0 else 0.0

        bull_sharpes = [p.sharpe for p in periods if p.regime == "Bull"]
        bear_sharpes = [p.sharpe for p in periods if p.regime == "Bear"]
        sideways_sharpes = [p.sharpe for p in periods if p.regime == "Sideways"]

        avg_bull = sum(bull_sharpes) / len(bull_sharpes) if bull_sharpes else 0.0
        avg_bear = sum(bear_sharpes) / len(bear_sharpes) if bear_sharpes else 0.0
        avg_sideways = sum(sideways_sharpes) / len(sideways_sharpes) if sideways_sharpes else 0.0

        consistency = self._compute_consistency(bull_sharpes, bear_sharpes, sideways_sharpes)

        max_dd_regime = ""
        max_dd_val = 0.0
        for p in periods:
            if abs(p.max_drawdown) > abs(max_dd_val):
                max_dd_val = p.max_drawdown
                max_dd_regime = p.regime

        return FundRegimeResult(
            periods=periods,
            bull_ratio=round(bull_r, 6),
            bear_ratio=round(bear_r, 6),
            sideways_ratio=round(sideways_r, 6),
            bull_sharpe=round(avg_bull, 6),
            bear_sharpe=round(avg_bear, 6),
            sideways_sharpe=round(avg_sideways, 6),
            regime_consistency=round(consistency, 4),
            max_regime_drawdown=max_dd_regime,
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

        if not valid_indices or min_len == 0:
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

    def _classify_regimes(self, daily_returns: list[float]) -> list[str]:
        n = len(daily_returns)
        regimes: list[str] = ["Sideways"] * n

        cum_returns: list[float] = []
        cum = 1.0
        for r in daily_returns:
            cum *= (1.0 + r)
            cum_returns.append(cum)

        for i in range(self.lookback - 1, n):
            lookback_return = (cum_returns[i] / cum_returns[i - self.lookback + 1]) - 1.0
            if lookback_return > self.bull_threshold:
                regimes[i] = "Bull"
            elif lookback_return < self.bear_threshold:
                regimes[i] = "Bear"
            else:
                regimes[i] = "Sideways"

        return regimes

    def _identify_periods(
        self,
        daily_returns: list[float],
        regimes: list[str],
        risk_free_rate: float,
    ) -> list[RegimePeriod]:
        n = len(daily_returns)
        periods: list[RegimePeriod] = []
        i = self.lookback - 1
        while i < n:
            current = regimes[i]
            j = i + 1
            while j < n and regimes[j] == current:
                j += 1

            seg_returns = daily_returns[i:j]
            seg_len = len(seg_returns)

            total_ret = 1.0
            for r in seg_returns:
                total_ret *= (1.0 + r)
            total_ret = total_ret - 1.0

            ann_ret = (1.0 + total_ret) ** (TRADING_DAYS / seg_len) - 1.0 if seg_len > 0 else 0.0

            sharpe = 0.0
            daily_vol = 0.0
            if seg_len >= 2:
                mean_r = sum(seg_returns) / seg_len
                var = sum((r - mean_r) ** 2 for r in seg_returns) / (seg_len - 1)
                daily_vol = math.sqrt(max(0.0, var))
                if daily_vol > 0:
                    daily_rf = risk_free_rate / TRADING_DAYS
                    daily_sharpe = (mean_r - daily_rf) / daily_vol
                    sharpe = daily_sharpe * math.sqrt(TRADING_DAYS)

            max_dd = 0.0
            peak = 1.0
            nav_val = 1.0
            for r in seg_returns:
                nav_val *= (1.0 + r)
                if nav_val > peak:
                    peak = nav_val
                else:
                    dd = (peak - nav_val) / peak if peak > 0 else 0.0
                    if dd > max_dd:
                        max_dd = dd
            max_dd = -max_dd

            periods.append(
                RegimePeriod(
                    regime=current,
                    start_idx=i,
                    end_idx=j - 1,
                    n_days=seg_len,
                    total_return=round(total_ret, 6),
                    annualized_return=round(ann_ret, 6),
                    sharpe=round(sharpe, 6),
                    max_drawdown=round(max_dd, 6),
                    volatility=round(daily_vol, 6),
                )
            )
            i = j

        return periods

    def _compute_consistency(
        self,
        bull_sharpes: list[float],
        bear_sharpes: list[float],
        sideways_sharpes: list[float],
    ) -> float:
        all_period_sharpes = bull_sharpes + bear_sharpes + sideways_sharpes
        if len(all_period_sharpes) < 2:
            return 0.0

        mean_s = sum(all_period_sharpes) / len(all_period_sharpes)
        if mean_s == 0:
            return 0.0

        var = sum((s - mean_s) ** 2 for s in all_period_sharpes) / len(all_period_sharpes)
        std_s = math.sqrt(var)
        cv = std_s / abs(mean_s)
        return max(0.0, min(1.0, 1.0 - cv))
