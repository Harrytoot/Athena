from datetime import datetime, timezone

from app.strategy.position_sizer import StrategyPosition
from app.strategy.portfolio_builder import PortfolioBuilder, PortfolioHistory, PortfolioSnapshot
from app.strategy.pnl_analyzer import StrategyPerformanceReport
from app.strategy_robustness.robustness_report import (
    CostAdjustedMetrics,
    RobustnessReport,
    StabilityMetrics,
)
from app.strategy_validation.performance_report import StrategyValidationReport
from app.portfolio.portfolio_engine import StrategyInput


def _pos(position_pct: float = 0.0, ts: datetime | None = None) -> StrategyPosition:
    if ts is None:
        ts = datetime.now(timezone.utc)
    return StrategyPosition(
        timestamp=ts,
        direction=1 if position_pct > 0 else (-1 if position_pct < 0 else 0),
        signal_weight=abs(position_pct),
        position_pct=position_pct,
        notional=position_pct * 100000.0,
    )


def _build_history(
    position_pcts: list[float],
    prices: list[float],
    initial_nav: float = 100000.0,
) -> PortfolioHistory:
    ts = datetime.now(timezone.utc)
    positions = [_pos(position_pct=pct, ts=ts) for pct in position_pcts]
    builder = PortfolioBuilder(initial_nav=initial_nav)
    return builder.build(positions, prices)


def _make_perf(sharpe=1.0, daily_vol=0.01, calmar=1.0, max_dd=-0.10, annual_ret=0.15, total_ret=0.30):
    return StrategyPerformanceReport(
        total_return=total_ret,
        annualized_return=annual_ret,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        max_drawdown_duration=5,
        win_rate=0.55,
        avg_daily_return=0.001,
        daily_volatility=daily_vol,
        calmar_ratio=calmar,
        total_days=252,
        avg_leverage=0.5,
        positive_days=130,
        negative_days=122,
    )


def _make_robust(cost_sharpe=0.9, stability=0.7):
    return RobustnessReport(
        cost_metrics=CostAdjustedMetrics(
            raw_sharpe=1.0,
            cost_adjusted_sharpe=cost_sharpe,
            total_transaction_costs=100.0,
            cost_ratio=0.01,
            total_slippage=50.0,
            slippage_ratio=0.005,
            total_market_impact=30.0,
            impact_ratio=0.003,
            total_friction=180.0,
            friction_ratio=0.01,
        ),
        stability=StabilityMetrics(
            perturbation_stability=stability,
            perturbation_mean_sharpe=cost_sharpe,
            perturbation_sharpe_std=0.1,
            stress_scenarios_passed=5,
            stress_scenarios_total=6,
            stress_resilience_score=0.83,
        ),
        overall_stability_score=stability,
        overall_assessment="good",
    )


def _make_strategy(
    sid: str,
    sharpe: float = 1.0,
    daily_vol: float = 0.01,
    max_dd: float = -0.10,
    history: PortfolioHistory | None = None,
) -> StrategyInput:
    return StrategyInput(
        strategy_id=sid,
        performance=_make_perf(sharpe=sharpe, daily_vol=daily_vol, max_dd=max_dd),
        robustness=_make_robust(cost_sharpe=sharpe * 0.9),
        history=history,
    )
