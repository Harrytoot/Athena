from datetime import date
from decimal import Decimal

from app.domain.entities.stock import Stock, StockPrice


class TestStock:
    def test_create_stock(self):
        stock = Stock(code="600519", name="贵州茅台", exchange="SSE", sector="食品饮料")
        assert stock.code == "600519"
        assert stock.name == "贵州茅台"
        assert stock.exchange == "SSE"

    def test_stock_with_market_cap(self):
        stock = Stock(
            code="600519",
            name="贵州茅台",
            market_cap=Decimal("2500000000000"),
            pe_ratio=Decimal("30.5"),
        )
        assert stock.listing_status == "listed"
        assert stock.pe_ratio == Decimal("30.5")

    def test_stock_price_creation(self):
        price = StockPrice(
            code="600519",
            trade_date=date(2024, 1, 15),
            open_price=Decimal("1650.00"),
            high_price=Decimal("1670.00"),
            low_price=Decimal("1645.00"),
            close_price=Decimal("1665.00"),
            volume=Decimal("5000000"),
            amount=Decimal("8325000000"),
            change_pct=Decimal("0.91"),
        )
        assert price.close_price == Decimal("1665.00")
        assert price.change_pct == Decimal("0.91")
