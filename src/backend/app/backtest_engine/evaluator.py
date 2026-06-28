from dataclasses import dataclass, field
from typing import Optional

from app.backtest_engine.dataset_builder import BacktestDataset
from app.backtest_engine.metrics import (
    information_coefficient,
    rank_information_coefficient,
    sharpe_ratio,
    win_rate,
)


@dataclass
class PeriodMetrics:
    ic: float = 0.0
    rank_ic: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    mean_return: float = 0.0
    n_observations: int = 0


@dataclass
class EquityPoint:
    time: str
    value: float


@dataclass
class TradeMark:
    time: str
    type: str
    price: float


@dataclass
class DrawdownPeriod:
    max_drawdown: float
    start: str
    end: str
    peak_value: float = 0.0
    trough_value: float = 0.0


@dataclass
class BacktestReport:
    total_observations: int = 0
    signal_count: int = 0
    long_count: int = 0
    short_count: int = 0
    neutral_count: int = 0
    period_5d: PeriodMetrics = field(default_factory=PeriodMetrics)
    period_10d: PeriodMetrics = field(default_factory=PeriodMetrics)
    period_20d: PeriodMetrics = field(default_factory=PeriodMetrics)
    score_min: float = 0.0
    score_max: float = 0.0
    score_mean: float = 0.0
    equity_curve: list[EquityPoint] = field(default_factory=list)
    benchmark_curve: list[EquityPoint] = field(default_factory=list)
    trades: list[TradeMark] = field(default_factory=list)
    drawdown_periods: list[DrawdownPeriod] = field(default_factory=list)
    max_drawdown: Optional[float] = None
    annual_return: Optional[float] = None
    annual_volatility: Optional[float] = None


class Evaluator:

    def evaluate(self, dataset: BacktestDataset) -> BacktestReport:
        if not dataset.rows:
            return BacktestReport()

        scores = dataset.scores
        signals = dataset.signals

        report = BacktestReport(
            total_observations=len(dataset.rows),
            signal_count=sum(1 for s in signals if s != 0),
            long_count=sum(1 for s in signals if s > 0),
            short_count=sum(1 for s in signals if s < 0),
            neutral_count=sum(1 for s in signals if s == 0),
            score_min=round(min(scores), 2),
            score_max=round(max(scores), 2),
            score_mean=round(sum(scores) / len(scores), 2),
        )

        report.period_5d = self._eval_period(scores, signals, dataset.forward_returns_5d)
        report.period_10d = self._eval_period(scores, signals, dataset.forward_returns_10d)
        report.period_20d = self._eval_period(scores, signals, dataset.forward_returns_20d)

        self._compute_equity_curve(report, dataset)
        self._compute_drawdowns(report)
        self._compute_trades(report, dataset)
        self._compute_summary_stats(report)

        return report

    def _eval_period(
        self, scores: list[float], signals: list[int], forward_returns: list[float]
    ) -> PeriodMetrics:
        if len(scores) < 3 or len(scores) != len(forward_returns):
            return PeriodMetrics()

        ic = information_coefficient(scores, forward_returns)
        rank_ic = rank_information_coefficient(scores, forward_returns)
        wr = win_rate(signals, forward_returns)

        strategy_returns = []
        for s, r in zip(signals, forward_returns):
            if s != 0:
                strategy_returns.append(s * r)

        shr = sharpe_ratio(strategy_returns) if strategy_returns else 0.0
        mean_r = round(sum(forward_returns) / len(forward_returns), 6) if forward_returns else 0.0

        return PeriodMetrics(
            ic=ic,
            rank_ic=rank_ic,
            sharpe=shr,
            win_rate=wr,
            mean_return=mean_r,
            n_observations=len(scores),
        )

    def _compute_equity_curve(self, report: BacktestReport, dataset: BacktestDataset) -> None:
        rows = dataset.rows
        if not rows:
            return

        signals = dataset.signals
        prices = [r.price for r in rows]

        strategy_nav = 1.0
        benchmark_nav = 1.0

        for i, row in enumerate(rows):
            time_str = row.timestamp.strftime("%Y-%m-%d") if hasattr(row.timestamp, "strftime") else str(row.timestamp)

            if i < len(row.forward_return_5d if hasattr(row, 'forward_return_5d') else []):
                pass

        for i, row in enumerate(rows):
            time_str = row.timestamp.strftime("%Y-%m-%d") if hasattr(row.timestamp, "strftime") else str(row.timestamp)

            ret_5d = row.forward_return_5d if i < len(dataset.forward_returns_5d) else 0.0
            sig = signals[i] if i < len(signals) else 0
            strategy_daily_return = sig * ret_5d if sig != 0 else 0.0
            strategy_nav *= (1 + strategy_daily_return)

            if i < len(prices) and i < len(prices) - 1 and prices[i] > 0:
                if i == 0:
                    benchmark_daily_return = 0.0
                else:
                    benchmark_daily_return = (prices[i] - prices[i - 1]) / prices[i - 1]
            else:
                benchmark_daily_return = 0.0
            benchmark_nav *= (1 + benchmark_daily_return)

            report.equity_curve.append(EquityPoint(time=time_str, value=round(strategy_nav, 6)))
            report.benchmark_curve.append(EquityPoint(time=time_str, value=round(benchmark_nav, 6)))

    def _compute_drawdowns(self, report: BacktestReport) -> None:
        if not report.equity_curve:
            return

        peak = report.equity_curve[0].value
        max_dd = 0.0
        dd_start: str | None = None
        dd_end: str | None = None
        peak_at = report.equity_curve[0].time
        trough_value = peak

        current_dd_start: str | None = None
        current_dd = 0.0

        for point in report.equity_curve:
            nav = point.value
            if nav > peak:
                if current_dd_start and current_dd > 0.02:
                    report.drawdown_periods.append(DrawdownPeriod(
                        max_drawdown=round(current_dd, 6),
                        start=current_dd_start,
                        end=point.time,
                        peak_value=round(peak, 4),
                        trough_value=round(trough_value, 4),
                    ))
                peak = nav
                peak_at = point.time
                current_dd_start = None
                current_dd = 0.0
                trough_value = nav
            else:
                dd = (nav - peak) / peak
                if dd < current_dd:
                    current_dd = dd
                    trough_value = nav
                    if current_dd_start is None:
                        current_dd_start = point.time
                if abs(dd) > abs(max_dd):
                    max_dd = dd
                    dd_start = peak_at
                    dd_end = point.time
                    trough_value = nav

        if current_dd_start and abs(current_dd) > 0.02:
            report.drawdown_periods.append(DrawdownPeriod(
                max_drawdown=round(current_dd, 6),
                start=current_dd_start,
                end=report.equity_curve[-1].time,
                peak_value=round(peak, 4),
                trough_value=round(trough_value, 4),
            ))

        if abs(max_dd) > 0:
            report.max_drawdown = round(abs(max_dd), 6)

    def _compute_trades(self, report: BacktestReport, dataset: BacktestDataset) -> None:
        signals = dataset.signals
        rows = dataset.rows
        if len(signals) < 2:
            return

        for i in range(len(signals)):
            sig = signals[i]
            prev_sig = signals[i - 1] if i > 0 else 0
            time_str = rows[i].timestamp.strftime("%Y-%m-%d") if hasattr(rows[i].timestamp, "strftime") else str(rows[i].timestamp)
            price = rows[i].price

            if sig == 1 and prev_sig != 1:
                report.trades.append(TradeMark(time=time_str, type="BUY", price=price))
            elif sig == -1 and prev_sig != -1:
                report.trades.append(TradeMark(time=time_str, type="SELL", price=price))
            elif sig == 0 and prev_sig != 0:
                report.trades.append(TradeMark(time=time_str, type="FLAT", price=price))

    def _compute_summary_stats(self, report: BacktestReport) -> None:
        if not report.equity_curve or len(report.equity_curve) < 2:
            return

        navs = [p.value for p in report.equity_curve]
        n = len(navs)

        daily_returns = []
        for i in range(1, n):
            if navs[i - 1] > 0:
                daily_returns.append((navs[i] - navs[i - 1]) / navs[i - 1])

        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            report.annual_return = round(mean_return * 252, 6)

            variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            import math
            daily_vol = math.sqrt(variance) if variance > 0 else 0.0
            report.annual_volatility = round(daily_vol * math.sqrt(252), 6)
