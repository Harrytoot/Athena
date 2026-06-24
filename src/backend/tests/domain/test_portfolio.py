from decimal import Decimal

import pytest

from app.domain.entities.portfolio import Portfolio, Position


class TestPosition:

    def test_cost_value(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"))
        assert pos.cost_value == Decimal("150000")

    def test_market_value_with_current_price(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"), current_price=Decimal("1600"))
        assert pos.market_value == Decimal("160000")

    def test_market_value_falls_back_to_cost(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"))
        assert pos.market_value == Decimal("150000")

    def test_pnl_positive(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"), current_price=Decimal("1600"))
        assert pos.pnl == Decimal("10000")

    def test_pnl_negative(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"), current_price=Decimal("1400"))
        assert pos.pnl == Decimal("-10000")

    def test_pnl_pct(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"), current_price=Decimal("1800"))
        assert pos.pnl_pct == Decimal("20.00")

    def test_pnl_pct_zero_cost(self):
        pos = Position(symbol="600519", name="贵州茅台", shares=Decimal("0"), cost_price=Decimal("0"))
        assert pos.pnl_pct == Decimal("0")


class TestPortfolio:

    def _make_portfolio(self):
        return Portfolio(
            id="p1", name="我的组合", cash=Decimal("500000"),
            positions=[
                Position(id="pos1", symbol="600519", name="贵州茅台", shares=Decimal("100"), cost_price=Decimal("1500"), current_price=Decimal("1600")),
                Position(id="pos2", symbol="000858", name="五粮液", shares=Decimal("200"), cost_price=Decimal("200"), current_price=Decimal("220")),
            ],
        )

    def test_total_cost(self):
        p = self._make_portfolio()
        assert p.total_cost == Decimal("190000")

    def test_total_market_value(self):
        p = self._make_portfolio()
        assert p.total_market_value == Decimal("204000")

    def test_total_assets(self):
        p = self._make_portfolio()
        assert p.total_assets == Decimal("704000")

    def test_total_pnl(self):
        p = self._make_portfolio()
        assert p.total_pnl == Decimal("14000")

    def test_total_pnl_pct(self):
        p = self._make_portfolio()
        assert float(p.total_pnl_pct) == pytest.approx(7.37, rel=0.01)

    def test_position_count(self):
        p = self._make_portfolio()
        assert p.position_count == 2

    def test_add_position_new(self):
        p = self._make_portfolio()
        new_pos = Position(symbol="300750", name="宁德时代", shares=Decimal("50"), cost_price=Decimal("200"))
        p.add_position(new_pos)
        assert p.position_count == 3

    def test_add_position_duplicate(self):
        p = self._make_portfolio()
        dup = Position(symbol="600519", name="贵州茅台", shares=Decimal("50"), cost_price=Decimal("1600"))
        p.add_position(dup)
        assert p.position_count == 2

    def test_remove_position(self):
        p = self._make_portfolio()
        p.remove_position("pos1")
        assert p.position_count == 1
        assert p.positions[0].symbol == "000858"

    def test_get_weight(self):
        p = self._make_portfolio()
        weight = p.get_weight(p.positions[0])
        assert float(weight) == pytest.approx(22.73, rel=0.01)  # 160000 / 704000 * 100 ≈ 22.727...

    def test_get_weight_zero_assets(self):
        p = Portfolio(cash=Decimal("0"))
        weight = p.get_weight(Position(symbol="600519", name="茅台", shares=Decimal("100"), cost_price=Decimal("1500")))
        assert weight == Decimal("0")

    def test_empty_portfolio(self):
        p = Portfolio(name="空组合")
        assert p.position_count == 0
        assert p.total_assets == Decimal("0")
        assert p.total_pnl == Decimal("0")
        assert p.total_pnl_pct == Decimal("0")
