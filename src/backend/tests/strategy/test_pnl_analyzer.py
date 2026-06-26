from datetime import datetime, timezone

import pytest

from app.strategy.portfolio_builder import PortfolioBuilder, PortfolioHistory, PortfolioSnapshot
from app.strategy.pnl_analyzer import PnLAnalyzer, StrategyPerformanceReport, DrawdownEvent
from app.strategy.position_sizer import StrategyPosition


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
    ts = datetime.now(timezone.utc)
    positions = [_pos(position_pct=pct, ts=ts) for pct in position_pcts]
    builder = PortfolioBuilder(initial_nav=initial_nav)
    return builder.build(positions, prices)


class TestPnLAnalyzer:

    def test_empty_history(self):
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(PortfolioHistory())
        assert report.total_days == 0
        assert report.total_return == 0.0
        assert report.sharpe_ratio == 0.0
        assert report.max_drawdown == 0.0

    def test_flat_performance(self):
        history = _build_history(
            position_pcts=[0.0, 0.0, 0.0],
            prices=[100.0, 101.0, 102.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.total_return == 0.0
        assert report.sharpe_ratio == 0.0
        assert report.max_drawdown == 0.0
        assert report.total_days == 3

    def test_positive_performance(self):
        history = _build_history(
            position_pcts=[1.0, 1.0, 1.0, 1.0, 1.0],
            prices=[100.0, 101.0, 102.0, 103.0, 104.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.total_return > 0
        assert report.avg_daily_return > 0
        assert report.win_rate > 0
        assert report.positive_days > 0

    def test_negative_performance(self):
        history = _build_history(
            position_pcts=[1.0, 1.0, 1.0, 1.0, 1.0],
            prices=[100.0, 99.0, 98.0, 97.0, 96.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.total_return < 0
        assert report.avg_daily_return < 0
        assert report.negative_days > 0

    def test_sharpe_ratio_positive_strategy(self):
        history = _build_history(
            position_pcts=[1.0] * 20,
            prices=[100.0 + i * 0.5 for i in range(20)],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.sharpe_ratio > 0

    def test_sharpe_ratio_zero_variance(self):
        history = _build_history(
            position_pcts=[0.0, 0.0, 0.0],
            prices=[100.0, 100.0, 100.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.sharpe_ratio == 0.0

    def test_max_drawdown_tracks_peak_to_trough(self):
        history = _build_history(
            position_pcts=[1.0, 1.0, 1.0, 1.0, 1.0],
            prices=[100.0, 101.0, 95.0, 96.0, 97.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.max_drawdown < 0

    def test_no_drawdown_when_uptrend(self):
        history = _build_history(
            position_pcts=[1.0, 1.0, 1.0, 1.0, 1.0],
            prices=[100.0, 101.0, 102.0, 103.0, 104.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.max_drawdown == 0.0
        assert len(report.drawdown_events) == 0

    def test_drawdown_event_detection(self):
        history = _build_history(
            position_pcts=[1.0, 1.0, 1.0, 1.0, 1.0],
            prices=[100.0, 101.0, 95.0, 96.0, 102.0],
            initial_nav=100000.0,
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert len(report.drawdown_events) >= 1
        assert report.drawdown_events[0].max_drawdown < 0

    def test_drawdown_max_is_negative(self):
        history = _build_history(
            position_pcts=[1.0, 1.0, 1.0],
            prices=[100.0, 90.0, 89.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.max_drawdown <= 0

    def test_avg_leverage(self):
        history = _build_history(
            position_pcts=[0.5, 0.75, 1.0, 0.0],
            prices=[100.0, 101.0, 102.0, 103.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        expected_avg = (0.5 + 0.75 + 1.0 + 0.0) / 4
        assert report.avg_leverage == pytest.approx(expected_avg, rel=1e-4)

    def test_performance_report_fields_populated(self):
        history = _build_history(
            position_pcts=[0.5] * 10,
            prices=[100.0 + i for i in range(10)],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)

        assert isinstance(report, StrategyPerformanceReport)
        assert report.total_days == 10
        assert isinstance(report.total_return, float)
        assert isinstance(report.annualized_return, float)
        assert isinstance(report.sharpe_ratio, float)
        assert isinstance(report.max_drawdown, float)
        assert isinstance(report.max_drawdown_duration, int)
        assert isinstance(report.win_rate, float)
        assert isinstance(report.avg_daily_return, float)
        assert isinstance(report.daily_volatility, float)
        assert isinstance(report.calmar_ratio, float)
        assert isinstance(report.avg_leverage, float)
        assert report.positive_days + report.negative_days <= report.total_days

    def test_win_rate_between_zero_and_one(self):
        history = _build_history(
            position_pcts=[1.0] * 10,
            prices=[100.0 + i * (0.5 if i % 2 == 0 else -0.3) for i in range(10)],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert 0.0 <= report.win_rate <= 1.0

    def test_custom_risk_free_rate(self):
        history = _build_history(
            position_pcts=[0.5] * 20,
            prices=[100.0 + i * 0.5 for i in range(20)],
        )
        analyzer_high = PnLAnalyzer(risk_free_rate=0.10)
        analyzer_low = PnLAnalyzer(risk_free_rate=0.0)
        report_high = analyzer_high.analyze(history)
        report_low = analyzer_low.analyze(history)
        assert report_high.sharpe_ratio <= report_low.sharpe_ratio

    def test_short_strategy_drawdown_pnl(self):
        history = _build_history(
            position_pcts=[-1.0, -1.0, -1.0, -1.0],
            prices=[100.0, 102.0, 103.0, 99.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert isinstance(report.max_drawdown, float)

    def test_drawdown_duration_count(self):
        history = _build_history(
            position_pcts=[1.0] * 10,
            prices=[100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 100.0, 101.0, 102.0, 103.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert isinstance(report.max_drawdown_duration, int)

    def test_calmar_ratio_zero_when_no_drawdown(self):
        history = _build_history(
            position_pcts=[1.0] * 5,
            prices=[100.0, 101.0, 102.0, 103.0, 104.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.calmar_ratio == 0.0

    def test_single_day_history(self):
        history = _build_history(
            position_pcts=[1.0],
            prices=[100.0],
        )
        analyzer = PnLAnalyzer()
        report = analyzer.analyze(history)
        assert report.total_days == 1
        assert report.daily_volatility == 0.0
        assert report.sharpe_ratio == 0.0
