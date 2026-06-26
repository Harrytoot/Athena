import math
from dataclasses import dataclass, field

from app.strategy.portfolio_builder import PortfolioHistory, PortfolioSnapshot

TRADING_DAYS_PER_YEAR = 252.0


@dataclass
class DrawdownEvent:
    start_idx: int
    end_idx: int
    peak_nav: float
    trough_nav: float
    max_drawdown: float
    duration: int


@dataclass
class StrategyPerformanceReport:
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    avg_daily_return: float
    daily_volatility: float
    calmar_ratio: float
    total_days: int
    avg_leverage: float
    positive_days: int = 0
    negative_days: int = 0
    drawdown_events: list[DrawdownEvent] = field(default_factory=list)


class PnLAnalyzer:

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate

    def analyze(self, history: PortfolioHistory) -> StrategyPerformanceReport:
        if not history.snapshots:
            return self._empty_report()

        daily_returns = history.daily_returns
        n = len(daily_returns)

        total_return = history.total_return

        avg_daily_return = sum(daily_returns) / n if n > 0 else 0.0
        annualized_return = (1.0 + total_return) ** (TRADING_DAYS_PER_YEAR / n) - 1.0 if n > 0 else 0.0

        daily_vol = self._compute_daily_volatility(daily_returns)
        sharpe = self._compute_sharpe(daily_returns, daily_vol)

        positive_days = sum(1 for r in daily_returns if r > 0)
        negative_days = sum(1 for r in daily_returns if r < 0)
        win_rate = positive_days / n if n > 0 else 0.0

        max_dd, max_dd_duration, drawdown_events = self._compute_drawdowns(history.snapshots)

        calmar = 0.0
        if max_dd != 0:
            calmar = annualized_return / abs(max_dd)

        avg_leverage = 0.0
        if history.snapshots:
            avg_leverage = sum(s.leverage for s in history.snapshots) / len(history.snapshots)

        return StrategyPerformanceReport(
            total_return=round(total_return, 6),
            annualized_return=round(annualized_return, 6),
            sharpe_ratio=round(sharpe, 6),
            max_drawdown=round(max_dd, 6),
            max_drawdown_duration=max_dd_duration,
            win_rate=round(win_rate, 6),
            avg_daily_return=round(avg_daily_return, 6),
            daily_volatility=round(daily_vol, 6),
            calmar_ratio=round(calmar, 6),
            total_days=n,
            avg_leverage=round(avg_leverage, 6),
            positive_days=positive_days,
            negative_days=negative_days,
            drawdown_events=drawdown_events,
        )

    def _compute_daily_volatility(self, daily_returns: list[float]) -> float:
        n = len(daily_returns)
        if n < 2:
            return 0.0
        mean_r = sum(daily_returns) / n
        variance = sum((r - mean_r) ** 2 for r in daily_returns) / (n - 1)
        return math.sqrt(variance)

    def _compute_sharpe(self, daily_returns: list[float], daily_vol: float) -> float:
        n = len(daily_returns)
        if n < 2 or daily_vol == 0:
            return 0.0
        mean_r = sum(daily_returns) / n
        daily_rf = self.risk_free_rate / TRADING_DAYS_PER_YEAR
        excess = mean_r - daily_rf
        daily_sharpe = excess / daily_vol
        return daily_sharpe * math.sqrt(TRADING_DAYS_PER_YEAR)

    def _compute_drawdowns(
        self, snapshots: list[PortfolioSnapshot]
    ) -> tuple[float, int, list[DrawdownEvent]]:
        navs = [s.nav for s in snapshots]
        n = len(navs)
        if n == 0:
            return 0.0, 0, []

        peak = navs[0]
        max_dd = 0.0
        max_dd_duration = 0
        drawdown_events: list[DrawdownEvent] = []

        in_drawdown = False
        dd_start = 0
        dd_peak = navs[0]

        for i in range(1, n):
            if navs[i] > peak:
                peak = navs[i]
                if in_drawdown:
                    dd = (dd_peak - navs[i - 1]) / dd_peak if dd_peak != 0 else 0.0
                    duration = (i - 1) - dd_start
                    drawdown_events.append(
                        DrawdownEvent(
                            start_idx=dd_start,
                            end_idx=i - 1,
                            peak_nav=dd_peak,
                            trough_nav=navs[i - 1],
                            max_drawdown=-round(dd, 6),
                            duration=duration,
                        )
                    )
                    in_drawdown = False
            else:
                if not in_drawdown:
                    in_drawdown = True
                    dd_start = i - 1
                    dd_peak = peak
                current_dd = (peak - navs[i]) / peak if peak != 0 else 0.0
                if current_dd > max_dd:
                    max_dd = current_dd
                    max_dd_duration = i - dd_start

        if in_drawdown:
            dd = (dd_peak - navs[-1]) / dd_peak if dd_peak != 0 else 0.0
            drawdown_events.append(
                DrawdownEvent(
                    start_idx=dd_start,
                    end_idx=n - 1,
                    peak_nav=dd_peak,
                    trough_nav=navs[-1],
                    max_drawdown=-round(dd, 6),
                    duration=(n - 1) - dd_start,
                )
            )

        max_dd = -max_dd
        return max_dd, max_dd_duration, drawdown_events

    def _empty_report(self) -> StrategyPerformanceReport:
        return StrategyPerformanceReport(
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=0,
            win_rate=0.0,
            avg_daily_return=0.0,
            daily_volatility=0.0,
            calmar_ratio=0.0,
            total_days=0,
            avg_leverage=0.0,
        )
