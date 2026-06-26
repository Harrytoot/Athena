from datetime import datetime, timezone

import pytest

from app.strategy.position_sizer import StrategyPosition
from app.strategy.risk_manager import RiskConstraints, RiskManager, RiskAdjustedPosition, RiskResult


def _pos(
    direction: int = 1,
    position_pct: float = 0.5,
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


class TestRiskConstraints:

    def test_default_constraints(self):
        c = RiskConstraints()
        assert c.max_single_exposure == 1.0
        assert c.max_total_exposure == 2.0
        assert c.max_turnover == 1.0

    def test_custom_constraints(self):
        c = RiskConstraints(
            max_single_exposure=0.5,
            max_total_exposure=1.0,
            max_turnover=0.3,
        )
        assert c.max_single_exposure == 0.5
        assert c.max_total_exposure == 1.0
        assert c.max_turnover == 0.3


class TestRiskManager:

    def test_empty_positions(self):
        mgr = RiskManager()
        result = mgr.apply([])
        assert len(result.positions) == 0

    def test_passes_through_within_limits(self):
        c = RiskConstraints(max_single_exposure=1.0, max_total_exposure=2.0)
        mgr = RiskManager(constraints=c)
        positions = [_pos(position_pct=0.5)]
        result = mgr.apply(positions)
        assert len(result.positions) == 1
        assert result.positions[0].adjusted_position_pct == 0.5
        assert not result.positions[0].capped_by_exposure

    def test_caps_single_exposure(self):
        c = RiskConstraints(max_single_exposure=0.5)
        mgr = RiskManager(constraints=c)
        positions = [_pos(position_pct=0.8)]
        result = mgr.apply(positions)
        assert result.positions[0].adjusted_position_pct == 0.5
        assert result.positions[0].capped_by_exposure

    def test_caps_single_exposure_short(self):
        c = RiskConstraints(max_single_exposure=0.5)
        mgr = RiskManager(constraints=c)
        positions = [_pos(direction=-1, position_pct=-0.8)]
        result = mgr.apply(positions)
        assert result.positions[0].adjusted_position_pct == -0.5
        assert result.positions[0].capped_by_exposure

    def test_caps_total_exposure(self):
        c = RiskConstraints(max_single_exposure=2.0, max_total_exposure=1.5)
        mgr = RiskManager(constraints=c)
        positions = [_pos(position_pct=2.0)]
        result = mgr.apply(positions)
        assert result.positions[0].adjusted_position_pct == 1.5
        assert result.positions[0].capped_by_exposure

    def test_total_exposure_tighter_than_single(self):
        c = RiskConstraints(max_single_exposure=2.0, max_total_exposure=0.6)
        mgr = RiskManager(constraints=c)
        positions = [_pos(position_pct=1.5)]
        result = mgr.apply(positions)
        assert result.positions[0].adjusted_position_pct == 0.6

    def test_no_turnover_capping_when_max_turnover_is_1(self):
        c = RiskConstraints(max_turnover=1.0)
        mgr = RiskManager(constraints=c)
        positions = [
            _pos(position_pct=0.0, ts=datetime.now(timezone.utc)),
            _pos(position_pct=1.0, ts=datetime.now(timezone.utc)),
        ]
        result = mgr.apply(positions)
        assert result.positions[1].adjusted_position_pct == 1.0
        assert not result.positions[1].capped_by_turnover

    def test_turnover_capped(self):
        c = RiskConstraints(max_turnover=0.3)
        mgr = RiskManager(constraints=c)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(position_pct=0.0, ts=ts),
            _pos(position_pct=0.8, ts=ts),
        ]
        result = mgr.apply(positions)
        assert result.positions[1].adjusted_position_pct == pytest.approx(0.3, rel=1e-4)
        assert result.positions[1].capped_by_turnover

    def test_turnover_capped_downward(self):
        c = RiskConstraints(max_turnover=0.2)
        mgr = RiskManager(constraints=c)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(position_pct=0.5, ts=ts),
            _pos(position_pct=-0.5, ts=ts),
        ]
        result = mgr.apply(positions)
        expected = 0.5 - 0.2
        assert result.positions[1].adjusted_position_pct == pytest.approx(expected, rel=1e-4)
        assert result.positions[1].capped_by_turnover

    def test_cash_buffer_constraint(self):
        c = RiskConstraints(min_cash_buffer=0.2)
        mgr = RiskManager(constraints=c)
        positions = [_pos(position_pct=1.0)]
        result = mgr.apply(positions)
        assert result.positions[0].adjusted_position_pct == 0.8
        assert result.positions[0].capped_by_exposure

    def test_cash_buffer_short_position(self):
        c = RiskConstraints(min_cash_buffer=0.1)
        mgr = RiskManager(constraints=c)
        positions = [_pos(direction=-1, position_pct=-1.0)]
        result = mgr.apply(positions)
        assert result.positions[0].adjusted_position_pct == -0.9

    def test_adjustment_reason_populated(self):
        c = RiskConstraints(max_single_exposure=0.3)
        mgr = RiskManager(constraints=c)
        positions = [_pos(position_pct=0.8)]
        result = mgr.apply(positions)
        assert "single_exposure" in result.positions[0].adjustment_reason

    def test_multiple_positions(self):
        c = RiskConstraints(max_single_exposure=0.6, max_turnover=0.5)
        mgr = RiskManager(constraints=c)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(position_pct=0.0, ts=ts),
            _pos(position_pct=0.5, ts=ts),
            _pos(position_pct=1.0, ts=ts),
        ]
        result = mgr.apply(positions)
        assert len(result.positions) == 3
        assert result.positions[0].adjusted_position_pct == 0.0
        assert result.positions[1].adjusted_position_pct == 0.5
        assert result.positions[2].adjusted_position_pct < 1.0

    def test_avg_turnover_computation(self):
        c = RiskConstraints(max_turnover=0.5)
        mgr = RiskManager(constraints=c)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(position_pct=0.0, ts=ts),
            _pos(position_pct=0.4, ts=ts),
            _pos(position_pct=0.1, ts=ts),
        ]
        result = mgr.apply(positions)
        assert result.avg_turnover == pytest.approx((0.4 + 0.3) / 2, rel=1e-4)

    def test_risk_result_total_exposure(self):
        c = RiskConstraints()
        mgr = RiskManager(constraints=c)
        ts = datetime.now(timezone.utc)
        positions = [
            _pos(position_pct=0.5, ts=ts),
            _pos(position_pct=-0.3, ts=ts),
        ]
        result = mgr.apply(positions)
        assert result.total_exposure == pytest.approx(0.8, rel=1e-4)
