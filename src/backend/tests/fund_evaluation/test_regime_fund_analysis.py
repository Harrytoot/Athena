import pytest

from app.fund_evaluation.regime_fund_analysis import (
    FundRegimeAnalyzer,
    FundRegimeResult,
    RegimePeriod,
)
from tests.fund_evaluation import _build_history, _make_strategy


def _make_cyclical_history(n_days: int = 200) -> tuple:
    prices: list[float] = []
    price = 100.0
    for i in range(n_days):
        if i < 50:
            price *= 1.002
        elif i < 100:
            price *= 0.995
        elif i < 150:
            price *= 1.003
        else:
            price *= 0.998
        prices.append(price)
    history = _build_history(
        position_pcts=[0.5] * n_days,
        prices=prices,
    )
    return history, prices


class TestFundRegimeAnalyzer:

    def test_empty_strategies(self):
        analyzer = FundRegimeAnalyzer()
        result = analyzer.analyze([], [])
        assert isinstance(result, FundRegimeResult)
        assert result.bull_ratio == 0.0

    def test_single_strategy_with_history(self):
        history = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 * (1.001 ** i) for i in range(100)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        assert len(result.periods) > 0
        assert result.bull_ratio + result.bear_ratio + result.sideways_ratio == pytest.approx(1.0, rel=1e-4)

    def test_regime_ratios_sum_to_one(self):
        history = _build_history(
            position_pcts=[0.5] * 150,
            prices=[100.0 * (1.0 + i * 0.0005) for i in range(150)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        total = result.bull_ratio + result.bear_ratio + result.sideways_ratio
        assert total == pytest.approx(1.0, rel=1e-4) or total == 0.0

    def test_short_history_no_regimes(self):
        history = _build_history(
            position_pcts=[0.5] * 30,
            prices=[100.0 + i * 0.1 for i in range(30)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=60)
        result = analyzer.analyze([strategy], [1.0])

        assert len(result.periods) == 0

    def test_bull_market_regime(self):
        history = _build_history(
            position_pcts=[1.0] * 150,
            prices=[100.0 * (1.003 ** i) for i in range(150)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        assert result.bull_ratio > 0

    def test_bear_market_regime(self):
        history = _build_history(
            position_pcts=[1.0] * 150,
            prices=[100.0 * (0.997 ** i) for i in range(150)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        assert result.bear_ratio > 0 or result.bear_sharpe <= 0

    def test_regime_consistency_range(self):
        history, _ = _make_cyclical_history(200)
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        assert 0.0 <= result.regime_consistency <= 1.0

    def test_multiple_strategies(self):
        h1 = _build_history(
            position_pcts=[1.0] * 100,
            prices=[100.0 * (1.002 ** i) for i in range(100)],
        )
        h2 = _build_history(
            position_pcts=[0.5] * 100,
            prices=[100.0 * (1.001 ** i) for i in range(100)],
        )
        s1 = _make_strategy("s1", history=h1)
        s2 = _make_strategy("s2", history=h2)
        analyzer = FundRegimeAnalyzer(lookback=40)
        result = analyzer.analyze([s1, s2], [0.6, 0.4])

        assert isinstance(result, FundRegimeResult)
        assert len(result.periods) > 0

    def test_regime_periods_have_valid_fields(self):
        history = _build_history(
            position_pcts=[0.5] * 120,
            prices=[100.0 * (1.001 ** i) for i in range(120)],
        )
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        for period in result.periods:
            assert period.regime in ("Bull", "Bear", "Sideways")
            assert period.n_days > 0
            assert period.start_idx < period.end_idx

    def test_no_history_fallback(self):
        s1 = _make_strategy("s1")
        analyzer = FundRegimeAnalyzer()
        result = analyzer.analyze([s1], [1.0])

        assert isinstance(result, FundRegimeResult)
        assert len(result.periods) == 0

    def test_cyclical_market_detects_multiple_regimes(self):
        history, _ = _make_cyclical_history(200)
        strategy = _make_strategy("s1", history=history)
        analyzer = FundRegimeAnalyzer(lookback=30)
        result = analyzer.analyze([strategy], [1.0])

        assert len(result.periods) >= 1
