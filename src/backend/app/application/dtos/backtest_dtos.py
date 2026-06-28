from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EquityPointDTO(BaseModel):
    time: str
    value: float


class TradeMarkDTO(BaseModel):
    time: str
    type: str
    price: float


class DrawdownPeriodDTO(BaseModel):
    maxDrawdown: float = Field(alias="max_drawdown")
    start: str
    end: str
    peakValue: float = Field(default=0.0, alias="peak_value")
    troughValue: float = Field(default=0.0, alias="trough_value")

    model_config = {"populate_by_name": True}


class PeriodMetricsDTO(BaseModel):
    ic: float = 0.0
    rankIc: float = Field(default=0.0, alias="rank_ic")
    sharpe: float = 0.0
    winRate: float = Field(default=0.0, alias="win_rate")
    meanReturn: float = Field(default=0.0, alias="mean_return")
    nObservations: int = Field(default=0, alias="n_observations")

    model_config = {"populate_by_name": True}


class BacktestResponse(BaseModel):
    totalObservations: int = Field(alias="total_observations")
    signalCount: int = Field(alias="signal_count")
    longCount: int = Field(alias="long_count")
    shortCount: int = Field(alias="short_count")
    neutralCount: int = Field(alias="neutral_count")
    scoreMin: float = Field(alias="score_min")
    scoreMax: float = Field(alias="score_max")
    scoreMean: float = Field(alias="score_mean")
    maxDrawdown: Optional[float] = Field(default=None, alias="max_drawdown")
    annualReturn: Optional[float] = Field(default=None, alias="annual_return")
    annualVolatility: Optional[float] = Field(default=None, alias="annual_volatility")
    period5d: PeriodMetricsDTO = Field(default_factory=PeriodMetricsDTO, alias="period_5d")
    period10d: PeriodMetricsDTO = Field(default_factory=PeriodMetricsDTO, alias="period_10d")
    period20d: PeriodMetricsDTO = Field(default_factory=PeriodMetricsDTO, alias="period_20d")
    equityCurve: list[EquityPointDTO] = Field(default_factory=list, alias="equity_curve")
    benchmarkCurve: list[EquityPointDTO] = Field(default_factory=list, alias="benchmark_curve")
    trades: list[TradeMarkDTO] = Field(default_factory=list)
    drawdownPeriods: list[DrawdownPeriodDTO] = Field(default_factory=list, alias="drawdown_periods")

    model_config = {"populate_by_name": True}

    @classmethod
    def from_report(cls, report) -> "BacktestResponse":
        return cls(
            total_observations=report.total_observations,
            signal_count=report.signal_count,
            long_count=report.long_count,
            short_count=report.short_count,
            neutral_count=report.neutral_count,
            score_min=report.score_min,
            score_max=report.score_max,
            score_mean=report.score_mean,
            max_drawdown=report.max_drawdown,
            annual_return=report.annual_return,
            annual_volatility=report.annual_volatility,
            period_5d=PeriodMetricsDTO(
                ic=report.period_5d.ic,
                rank_ic=report.period_5d.rank_ic,
                sharpe=report.period_5d.sharpe,
                win_rate=report.period_5d.win_rate,
                mean_return=report.period_5d.mean_return,
                n_observations=report.period_5d.n_observations,
            ),
            period_10d=PeriodMetricsDTO(
                ic=report.period_10d.ic,
                rank_ic=report.period_10d.rank_ic,
                sharpe=report.period_10d.sharpe,
                win_rate=report.period_10d.win_rate,
                mean_return=report.period_10d.mean_return,
                n_observations=report.period_10d.n_observations,
            ),
            period_20d=PeriodMetricsDTO(
                ic=report.period_20d.ic,
                rank_ic=report.period_20d.rank_ic,
                sharpe=report.period_20d.sharpe,
                win_rate=report.period_20d.win_rate,
                mean_return=report.period_20d.mean_return,
                n_observations=report.period_20d.n_observations,
            ),
            equity_curve=[EquityPointDTO(time=p.time, value=p.value) for p in report.equity_curve],
            benchmark_curve=[EquityPointDTO(time=p.time, value=p.value) for p in report.benchmark_curve],
            trades=[TradeMarkDTO(time=t.time, type=t.type, price=t.price) for t in report.trades],
            drawdown_periods=[
                DrawdownPeriodDTO(
                    max_drawdown=d.max_drawdown,
                    start=d.start,
                    end=d.end,
                    peak_value=d.peak_value,
                    trough_value=d.trough_value,
                )
                for d in report.drawdown_periods
            ],
        )


class BacktestRequest(BaseModel):
    symbol: str = "000001"
    days: int = Field(default=120, ge=30, le=500)
