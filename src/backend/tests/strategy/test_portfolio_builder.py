from datetime import datetime, timezone

import pytest

from app.strategy.portfolio_builder import (
    DEFAULT_INITIAL_NAV,
    PortfolioBuilder,
    PortfolioHistory,
    PortfolioSnapshot,
)
from app.strategy.position_sizer import StrategyPosition


def _pos(
    direction: int = 0,
    position_pct: float = 0.0,
    ts: datetime | None = None,
    notional: float = 0.0,
) -> StrategyPosition:
    if ts is None:
        ts = datetime.now(timezone.utc)
    return StrategyPosition(
        timestamp=ts,
        direction=direction,
        signal_weight=abs(position_pct),
        position_pct=position_pct,
        notional=notional,
    )


class TestPortfolioBuilder:

    def test_empty_positions_returns_empty_history(self):
        builder = PortfolioBuilder()
        history = builder.build([], [])
        assert len(history.snapshots) == 0

    def test_mismatched_lengths_returns_empty_history(self):
        builder = PortfolioBuilder()
        ts = datetime.now(timezone.utc)
        positions = [_pos(direction=1, position_pct=1.0, ts=ts)]
        prices = [100.0, 101.0]
        history = builder.build(positions, prices)
        assert len(history.snapshots) == 0

    def test_flat_position_no_pnl(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=0, position_pct=0.0, ts=ts),
            _pos(direction=0, position_pct=0.0, ts=ts),
        ]
        prices = [100.0, 101.0]
        history = builder.build(positions, prices)
        assert len(history.snapshots) == 2
        assert history.snapshots[0].nav == 100000.0
        assert history.snapshots[1].nav == 100000.0

    def test_long_position_profitable(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=1, position_pct=1.0, ts=ts),
        ]
        prices = [100.0, 101.0, 102.0]
        history = builder.build(positions, prices)

        assert len(history.snapshots) == 3
        assert history.snapshots[0].nav == 100000.0
        assert history.snapshots[0].daily_return == 0.0
        expected_nav_day2 = 100000.0 * (1.0 + 1.0 * 0.01)
        assert history.snapshots[1].nav == pytest.approx(expected_nav_day2, rel=1e-4)
        expected_nav_day3 = expected_nav_day2 * (1.0 + 1.0 * (102.0 - 101.0) / 101.0)
        assert history.snapshots[2].nav == pytest.approx(expected_nav_day3, rel=1e-4)
        assert history.snapshots[2].cumulative_return > 0

    def test_short_position_profitable_on_decline(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=-1, position_pct=-1.0, ts=ts),
            _pos(direction=-1, position_pct=-1.0, ts=ts),
            _pos(direction=-1, position_pct=-1.0, ts=ts),
        ]
        prices = [100.0, 99.0, 98.0]
        history = builder.build(positions, prices)

        assert history.snapshots[0].nav == 100000.0
        expected_nav_day2 = 100000.0 * (1.0 + (-1.0) * (-0.01))
        assert history.snapshots[1].nav == pytest.approx(expected_nav_day2, rel=1e-4)
        assert history.snapshots[2].cumulative_return > 0

    def test_daily_return_calculation(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=0.5, ts=ts),
        ]
        prices = [100.0]
        history = builder.build(positions, prices)
        assert history.snapshots[0].daily_return == 0.0

    def test_cumulative_return_calculation(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=1, position_pct=1.0, ts=ts),
        ]
        prices = [100.0, 110.0]
        history = builder.build(positions, prices)
        assert history.snapshots[0].cumulative_return == 0.0
        assert history.snapshots[1].cumulative_return == pytest.approx(0.10, rel=1e-4)

    def test_leverage_tracks_position_size(self):
        builder = PortfolioBuilder()
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=0.75, ts=ts),
            _pos(direction=-1, position_pct=-0.5, ts=ts),
        ]
        prices = [100.0, 101.0]
        history = builder.build(positions, prices)
        assert history.snapshots[0].leverage == 0.75
        assert history.snapshots[1].leverage == 0.5

    def test_portfolio_history_properties(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=1, position_pct=1.0, ts=ts),
        ]
        prices = [100.0, 101.0, 102.0]
        history = builder.build(positions, prices)

        assert len(history.nav_series) == 3
        assert len(history.daily_returns) == 3
        assert history.final_nav > history.nav_series[0]
        assert history.total_return > 0

    def test_zero_price_returns_zero_return(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=1, position_pct=1.0, ts=ts),
        ]
        prices = [0.0, 100.0]
        history = builder.build(positions, prices)
        assert history.snapshots[0].nav == 100000.0
        assert history.snapshots[1].nav == 100000.0

    def test_switching_direction(self):
        builder = PortfolioBuilder(initial_nav=100000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=1.0, ts=ts),
            _pos(direction=-1, position_pct=-1.0, ts=ts),
            _pos(direction=-1, position_pct=-1.0, ts=ts),
        ]
        prices = [100.0, 101.0, 99.0]
        history = builder.build(positions, prices)

        nav_after_long = 100000.0 * 1.01
        assert history.snapshots[1].nav == pytest.approx(nav_after_long, rel=1e-4)
        nav_after_short = nav_after_long * (1.0 + (-1.0) * (99.0 - 101.0) / 101.0)
        assert history.snapshots[2].nav == pytest.approx(nav_after_short, rel=1e-4)
        assert history.snapshots[2].cumulative_return > 0

    def test_custom_initial_nav(self):
        builder = PortfolioBuilder(initial_nav=50000.0)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(direction=1, position_pct=1.0, ts=ts),
        ]
        prices = [100.0]
        history = builder.build(positions, prices)
        assert history.snapshots[0].nav == 50000.0
