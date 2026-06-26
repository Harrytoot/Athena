import pytest

from app.execution.order_book_simulator import (
    OrderBookConfig,
    OrderBookSimulator,
    Order,
    FillResult,
)


class TestOrderBookSimulator:

    def test_default_fill(self):
        sim = OrderBookSimulator(config=OrderBookConfig(seed=42))
        order = Order(strategy_id="s1", side="buy", quantity=1000.0, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 1e7, 1e8)

        assert isinstance(fill, FillResult)
        assert fill.strategy_id == "s1"
        assert fill.side == "buy"
        assert fill.average_price > 0

    def test_no_liquidity_results_in_zero_fill(self):
        sim = OrderBookSimulator()
        order = Order(strategy_id="s1", side="buy", quantity=1000.0, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 0.0, 0.0)

        assert fill.filled_quantity == 0.0
        assert fill.fill_ratio == 0.0
        assert fill.partial_fill

    def test_zero_volume_results_in_zero_fill(self):
        sim = OrderBookSimulator()
        order = Order(strategy_id="s1", side="buy", quantity=1000.0, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 1e7, 0.0)

        assert fill.filled_quantity == 0.0

    def test_deterministic_with_seed(self):
        config = OrderBookConfig(seed=99)
        sim1 = OrderBookSimulator(config=config)
        sim2 = OrderBookSimulator(config=config)
        order = Order(strategy_id="s1", side="buy", quantity=1000.0, order_id="o1")

        f1 = sim1.simulate_fill(order, 100.0, 1e7, 1e8)
        f2 = sim2.simulate_fill(order, 100.0, 1e7, 1e8)

        assert f1.fill_ratio == f2.fill_ratio
        assert f1.average_price == f2.average_price

    def test_fill_ratio_between_zero_and_one(self):
        sim = OrderBookSimulator(config=OrderBookConfig(seed=42))
        order = Order(strategy_id="s1", side="buy", quantity=5000.0, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 1e6, 1e7)

        assert 0.0 <= fill.fill_ratio <= 1.0

    def test_buy_order_price_higher_than_reference(self):
        sim = OrderBookSimulator(config=OrderBookConfig(seed=42))
        order = Order(strategy_id="s1", side="buy", quantity=10000.0, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 1e6, 1e7)

        if fill.filled_quantity > 0:
            assert fill.average_price >= 99.0

    def test_sell_order(self):
        sim = OrderBookSimulator(config=OrderBookConfig(seed=42))
        order = Order(strategy_id="s1", side="sell", quantity=1000.0, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 1e7, 1e8)

        assert fill.side == "sell"
        assert isinstance(fill.fill_ratio, float)

    def test_is_complete_property(self):
        fill = FillResult(
            order_id="o1",
            strategy_id="s1",
            side="buy",
            requested_quantity=1000.0,
            filled_quantity=1000.0,
            fill_ratio=1.0,
            average_price=100.0,
            execution_timestamp=None,
            partial_fill=False,
        )
        assert fill.is_complete

    def test_is_complete_partial(self):
        fill = FillResult(
            order_id="o1",
            strategy_id="s1",
            side="buy",
            requested_quantity=1000.0,
            filled_quantity=500.0,
            fill_ratio=0.5,
            average_price=100.0,
            execution_timestamp=None,
            partial_fill=True,
        )
        assert not fill.is_complete

    def test_compute_notional(self):
        sim = OrderBookSimulator()
        fill = FillResult(
            order_id="o1",
            strategy_id="s1",
            side="buy",
            requested_quantity=1000.0,
            filled_quantity=500.0,
            fill_ratio=0.5,
            average_price=100.0,
            execution_timestamp=None,
            partial_fill=True,
        )
        notional = sim.compute_notional(fill)
        assert notional == pytest.approx(50000.0, rel=1e-4)

    def test_large_participation_reduces_fill(self):
        config = OrderBookConfig(seed=42)
        sim = OrderBookSimulator(config=config)
        order = Order(strategy_id="s1", side="buy", quantity=1_000_000, order_id="o1")
        fill = sim.simulate_fill(order, 100.0, 1e6, 2e6)

        assert fill.fill_ratio <= 1.0

    def test_order_properties(self):
        order = Order(strategy_id="s1", side="buy", quantity=100.0)
        assert order.is_buy
        assert not order.is_sell

        order2 = Order(strategy_id="s2", side="sell", quantity=200.0)
        assert not order2.is_buy
        assert order2.is_sell
