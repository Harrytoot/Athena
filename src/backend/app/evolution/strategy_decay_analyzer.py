import math
from dataclasses import dataclass, field

from app.portfolio.portfolio_engine import StrategyInput
from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy.portfolio_builder import PortfolioHistory


@dataclass
class StrategyDecaySignal:
    strategy_id: str
    sharpe_trend: float
    return_trend: float
    drawdown_trend: float
    win_rate_trend: float
    volatility_trend: float
    alpha_half_life_days: float
    decay_score: float
    performance_erosion: float
    decay_assessment: str


@dataclass
class StrategyDecayReport:
    decay_signals: list[StrategyDecaySignal] = field(default_factory=list)
    overall_decay_score: float = 0.0
    most_decayed: list[str] = field(default_factory=list)
    still_strong: list[str] = field(default_factory=list)
    assessment: str = ""

    @property
    def decay_severity(self) -> str:
        if self.overall_decay_score >= 0.7:
            return "critical"
        if self.overall_decay_score >= 0.5:
            return "significant"
        if self.overall_decay_score >= 0.3:
            return "moderate"
        return "low"


class StrategyDecayAnalyzer:

    def __init__(
        self,
        window_size: int = 30,
        min_history: int = 60,
        decay_threshold: float = 0.5,
        erosion_threshold: float = 0.15,
    ):
        self.window_size = window_size
        self.min_history = min_history
        self.decay_threshold = decay_threshold
        self.erosion_threshold = erosion_threshold

    def analyze(self, strategies: list[StrategyInput]) -> StrategyDecayReport:
        if not strategies:
            return StrategyDecayReport(assessment="无策略数据")

        decay_signals: list[StrategyDecaySignal] = []
        for s in strategies:
            signal = self._analyze_single_strategy(s)
            if signal:
                decay_signals.append(signal)

        decay_signals.sort(key=lambda d: d.decay_score, reverse=True)

        overall_score = self._compute_overall_decay(decay_signals)
        most_decayed = [d.strategy_id for d in decay_signals if d.decay_score >= self.decay_threshold]
        still_strong = [d.strategy_id for d in decay_signals if d.decay_score < 0.3]
        assessment = self._assess_decay(decay_signals, overall_score)

        return StrategyDecayReport(
            decay_signals=decay_signals,
            overall_decay_score=round(overall_score, 4),
            most_decayed=most_decayed,
            still_strong=still_strong,
            assessment=assessment,
        )

    def _analyze_single_strategy(
        self, strategy: StrategyInput
    ) -> StrategyDecaySignal | None:
        history = strategy.history
        perf = strategy.performance

        if history is None or not history.snapshots:
            return self._analyze_from_snapshot(perf, strategy.strategy_id)

        snapshots = history.snapshots
        n = len(snapshots)
        if n < self.min_history:
            return self._analyze_from_snapshot(perf, strategy.strategy_id)

        daily_returns = history.daily_returns
        navs = history.nav_series

        rolling_sharpes = self._compute_rolling_sharpes(daily_returns)
        sharpe_trend = self._linear_trend(rolling_sharpes) if rolling_sharpes else 0.0

        rolling_returns = self._compute_rolling_returns(daily_returns)
        return_trend = self._linear_trend(rolling_returns) if rolling_returns else 0.0

        rolling_drawdowns = self._compute_rolling_max_drawdowns(navs)
        drawdown_trend = self._linear_trend(rolling_drawdowns) if rolling_drawdowns else 0.0

        rolling_win_rates = self._compute_rolling_win_rates(daily_returns)
        win_rate_trend = self._linear_trend(rolling_win_rates) if rolling_win_rates else 0.0

        rolling_vols = self._compute_rolling_volatilities(daily_returns)
        volatility_trend = self._linear_trend(rolling_vols) if rolling_vols else 0.0

        alpha_half_life = self._estimate_half_life(
            sharpe_trend, return_trend, daily_returns
        )

        performance_erosion = self._compute_performance_erosion(
            sharpe_trend, drawdown_trend, win_rate_trend
        )

        decay_score = self._compute_decay_score(
            sharpe_trend, return_trend, drawdown_trend, win_rate_trend, volatility_trend,
            performance_erosion
        )

        assessment = self._assess_single_decay(
            strategy.strategy_id, decay_score, sharpe_trend, performance_erosion, alpha_half_life
        )

        return StrategyDecaySignal(
            strategy_id=strategy.strategy_id,
            sharpe_trend=round(sharpe_trend, 6),
            return_trend=round(return_trend, 6),
            drawdown_trend=round(drawdown_trend, 6),
            win_rate_trend=round(win_rate_trend, 6),
            volatility_trend=round(volatility_trend, 6),
            alpha_half_life_days=round(alpha_half_life, 1),
            decay_score=round(decay_score, 4),
            performance_erosion=round(performance_erosion, 4),
            decay_assessment=assessment,
        )

    def _analyze_from_snapshot(
        self, perf: StrategyPerformanceReport, strategy_id: str
    ) -> StrategyDecaySignal | None:
        sharpe_score = 0.0
        if perf.sharpe_ratio < 0:
            sharpe_score = 0.8
        elif perf.sharpe_ratio < 0.3:
            sharpe_score = 0.5
        elif perf.sharpe_ratio < 0.6:
            sharpe_score = 0.3
        else:
            sharpe_score = 0.1

        dd_score = 0.0
        if perf.max_drawdown < -0.25:
            dd_score = 0.7
        elif perf.max_drawdown < -0.15:
            dd_score = 0.4
        elif perf.max_drawdown < -0.05:
            dd_score = 0.2

        decay_score = round(sharpe_score * 0.6 + dd_score * 0.4, 4)

        assessment = "历史数据不足" if perf.total_days < self.min_history else "无详细历史"

        return StrategyDecaySignal(
            strategy_id=strategy_id,
            sharpe_trend=0.0,
            return_trend=0.0,
            drawdown_trend=0.0,
            win_rate_trend=0.0,
            volatility_trend=0.0,
            alpha_half_life_days=0.0,
            decay_score=decay_score,
            performance_erosion=0.0,
            decay_assessment=assessment,
        )

    def _compute_rolling_sharpes(
        self, daily_returns: list[float]
    ) -> list[float]:
        return self._rolling_window(daily_returns, self._annualized_sharpe)

    def _compute_rolling_returns(
        self, daily_returns: list[float]
    ) -> list[float]:
        return self._rolling_window(daily_returns, self._annualized_return)

    def _compute_rolling_max_drawdowns(
        self, navs: list[float]
    ) -> list[float]:
        return self._rolling_window_nav(navs, self._max_drawdown)

    def _compute_rolling_win_rates(
        self, daily_returns: list[float]
    ) -> list[float]:
        return self._rolling_window(daily_returns, self._win_rate)

    def _compute_rolling_volatilities(
        self, daily_returns: list[float]
    ) -> list[float]:
        return self._rolling_window(daily_returns, self._annualized_volatility)

    def _rolling_window(
        self, values: list[float], metric_fn
    ) -> list[float]:
        n = len(values)
        if n < self.window_size:
            return []
        result: list[float] = []
        for i in range(self.window_size, n + 1):
            window = values[i - self.window_size:i]
            result.append(metric_fn(window))
        return result

    def _rolling_window_nav(
        self, values: list[float], metric_fn
    ) -> list[float]:
        n = len(values)
        if n < self.window_size:
            return []
        result: list[float] = []
        for i in range(self.window_size, n + 1):
            window = values[i - self.window_size:i]
            result.append(metric_fn(window))
        return result

    def _annualized_sharpe(self, window: list[float]) -> float:
        n = len(window)
        if n < 2:
            return 0.0
        mean_r = sum(window) / n
        var = sum((r - mean_r) ** 2 for r in window) / (n - 1)
        vol = math.sqrt(max(0.0, var))
        if vol == 0:
            return 0.0
        daily_rf = 0.02 / 252.0
        return ((mean_r - daily_rf) / vol) * math.sqrt(252.0)

    def _annualized_return(self, window: list[float]) -> float:
        mean_r = sum(window) / len(window) if window else 0.0
        return (1.0 + mean_r) ** 252.0 - 1.0

    def _annualized_volatility(self, window: list[float]) -> float:
        n = len(window)
        if n < 2:
            return 0.0
        mean_r = sum(window) / n
        var = sum((r - mean_r) ** 2 for r in window) / (n - 1)
        return math.sqrt(max(0.0, var)) * math.sqrt(252.0)

    def _win_rate(self, window: list[float]) -> float:
        if not window:
            return 0.0
        return sum(1 for r in window if r > 0) / len(window)

    def _max_drawdown(self, window: list[float]) -> float:
        if not window:
            return 0.0
        peak = window[0]
        max_dd = 0.0
        for v in window[1:]:
            if v > peak:
                peak = v
            dd = (peak - v) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        return -max_dd

    def _linear_trend(self, values: list[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def _estimate_half_life(
        self,
        sharpe_trend: float,
        return_trend: float,
        daily_returns: list[float],
    ) -> float:
        n = len(daily_returns)
        if n < 2:
            return 0.0
        mean_r = sum(daily_returns) / n
        var = sum((r - mean_r) ** 2 for r in daily_returns) / (n - 1)
        vol = math.sqrt(max(0.0, var))

        decay_rate = abs(sharpe_trend) if abs(sharpe_trend) > 1e-12 else abs(return_trend)

        if decay_rate < 1e-12 or abs(mean_r) < 1e-12:
            return float("inf")

        current_signal = abs(mean_r) / vol if vol > 0 else 0.0
        decay_rate_per_day = decay_rate * 252.0

        if decay_rate_per_day <= 0 or current_signal <= 0:
            return float("inf")

        half_life = math.log(max(0.01, 2.0)) / decay_rate_per_day
        return min(half_life, 3650.0)

    def _compute_performance_erosion(
        self,
        sharpe_trend: float,
        drawdown_trend: float,
        win_rate_trend: float,
    ) -> float:
        erosion = 0.0
        if sharpe_trend < 0:
            erosion += abs(sharpe_trend) * 0.5
        if drawdown_trend > 0:
            erosion += abs(drawdown_trend) * 0.3
        if win_rate_trend < 0:
            erosion += abs(win_rate_trend) * 0.2
        return min(1.0, erosion)

    def _compute_decay_score(
        self,
        sharpe_trend: float,
        return_trend: float,
        drawdown_trend: float,
        win_rate_trend: float,
        volatility_trend: float,
        performance_erosion: float,
    ) -> float:
        sharpe_component = 0.0
        if sharpe_trend < -0.0005:
            sharpe_component = min(1.0, abs(sharpe_trend) / 0.005) * 0.30
        elif sharpe_trend > 0.0005:
            sharpe_component = -0.10
        else:
            sharpe_component = 0.05

        return_component = 0.0
        if return_trend < -0.0002:
            return_component = min(1.0, abs(return_trend) / 0.003) * 0.15

        dd_component = 0.0
        if drawdown_trend > 0.0005:
            dd_component = min(1.0, abs(drawdown_trend) / 0.005) * 0.25

        wr_component = 0.0
        if win_rate_trend < -0.0002:
            wr_component = min(1.0, abs(win_rate_trend) / 0.003) * 0.15

        vol_component = 0.0
        if volatility_trend > 0.0005:
            vol_component = min(1.0, abs(volatility_trend) / 0.005) * 0.15

        score = (
            max(0.0, sharpe_component)
            + max(0.0, return_component)
            + max(0.0, dd_component)
            + max(0.0, wr_component)
            + max(0.0, vol_component)
        )
        return min(1.0, max(0.0, score))

    def _compute_overall_decay(
        self, signals: list[StrategyDecaySignal]
    ) -> float:
        if not signals:
            return 0.0
        return sum(s.decay_score for s in signals) / len(signals)

    def _assess_single_decay(
        self,
        strategy_id: str,
        decay_score: float,
        sharpe_trend: float,
        performance_erosion: float,
        alpha_half_life: float,
    ) -> str:
        parts: list[str] = []

        if decay_score >= 0.7:
            parts.append(f"策略 {strategy_id}: 严重衰减")
        elif decay_score >= 0.5:
            parts.append(f"策略 {strategy_id}: 显著衰减")
        elif decay_score >= 0.3:
            parts.append(f"策略 {strategy_id}: 轻微衰减")
        else:
            parts.append(f"策略 {strategy_id}: 状态良好")

        if sharpe_trend < -0.001:
            parts.append("夏普趋势下降")
        elif sharpe_trend > 0.001:
            parts.append("夏普趋势上升")

        if performance_erosion > 0.3:
            parts.append("绩效侵蚀显著")

        if 0 < alpha_half_life < 365:
            parts.append(f"Alpha半衰期: {alpha_half_life:.0f}天")
        elif alpha_half_life >= 3650:
            parts.append("Alpha半衰期: 极长(稳定)")
        else:
            parts.append("Alpha半衰期: 未测定")

        return " | ".join(parts)

    def _assess_decay(
        self,
        signals: list[StrategyDecaySignal],
        overall_score: float,
    ) -> str:
        parts: list[str] = []

        if overall_score >= 0.7:
            parts.append("策略衰减: 严重")
        elif overall_score >= 0.5:
            parts.append("策略衰减: 显著")
        elif overall_score >= 0.3:
            parts.append("策略衰减: 轻微")
        else:
            parts.append("策略衰减: 正常")

        parts.append(f"综合衰减评分: {overall_score:.2f}")

        decayed = [s for s in signals if s.decay_score >= 0.5]
        if decayed:
            parts.append(f"衰减策略数: {len(decayed)}")
            ids = ", ".join(s.strategy_id for s in decayed[:3])
            parts.append(f"主要衰减策略: {ids}")
        else:
            parts.append("无显著衰减策略")

        return " | ".join(parts)
