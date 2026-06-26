from datetime import datetime, timezone

from app.strategy.portfolio_builder import PortfolioHistory, PortfolioSnapshot
from app.strategy.position_sizer import StrategyPosition
from app.strategy.risk_manager import RiskResult, RiskAdjustedPosition, RiskConstraints, RiskManager


def _pos(
    direction: int = 0,
    position_pct: float = 0.0,
    ts: datetime | None = None,
) -> StrategyPosition:
    if ts is None:
        ts = datetime.now(timezone.utc)
    return StrategyPosition(
        timestamp=ts,
        direction=direction,
        signal_weight=abs(position_pct),
        position_pct=position_pct,
        notional=position_pct * 100000.0,
    )


def _build_history(
    position_pcts: list[float],
    prices: list[float],
    initial_nav: float = 100000.0,
) -> PortfolioHistory:
    from app.strategy.portfolio_builder import PortfolioBuilder

    ts = datetime.now(timezone.utc)
    positions = [_pos(position_pct=pct, ts=ts) for pct in position_pcts]
    builder = PortfolioBuilder(initial_nav=initial_nav)
    return builder.build(positions, prices)


def _risk_result(position_pcts: list[float]) -> RiskResult:
    ts = datetime.now(timezone.utc)
    positions = [_pos(position_pct=pct, ts=ts) for pct in position_pcts]
    mgr = RiskManager()
    return mgr.apply(positions)
