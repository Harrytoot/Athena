import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.broker_integration.market_feed.data_normalizer import DataNormalizer, NormalizedBar


class TestNormalizedBar:
    def test_create_bar(self):
        bar = NormalizedBar(
            symbol="000001",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=Decimal("10"),
            high=Decimal("12"),
            low=Decimal("9"),
            close=Decimal("11"),
            volume=Decimal("1000000"),
        )
        assert bar.symbol == "000001"
        assert bar.open == Decimal("10")
        assert bar.typical_price == (Decimal("12") + Decimal("9") + Decimal("11")) / Decimal("3")
        assert bar.range == Decimal("3")
        assert bar.is_up is True
        assert bar.change_pct == Decimal("10")

    def test_is_down(self):
        bar = NormalizedBar(
            symbol="TEST",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=Decimal("15"),
            high=Decimal("16"),
            low=Decimal("13"),
            close=Decimal("14"),
            volume=Decimal("5000"),
        )
        assert bar.is_up is False
        assert bar.change_pct < 0

    def test_change_pct_zero_open(self):
        bar = NormalizedBar(
            symbol="TEST",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=Decimal("0"),
            high=Decimal("0"),
            low=Decimal("0"),
            close=Decimal("0"),
            volume=Decimal("0"),
        )
        assert bar.change_pct == Decimal("0")


class TestDataNormalizer:
    def test_from_akshare_bar(self):
        raw = {"open": 10.5, "high": 11.0, "low": 10.0, "close": 10.8, "volume": 500000}
        bar = DataNormalizer.from_akshare_bar(
            symbol="000001",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            raw=raw,
        )
        assert bar.open == Decimal("10.5")
        assert bar.close == Decimal("10.8")
        assert bar.volume == Decimal("500000")
        assert bar.source == "akshare"

    def test_from_dict_short_keys(self):
        raw = {"o": 100, "h": 110, "l": 95, "c": 105, "v": 10000}
        bar = DataNormalizer.from_dict(
            symbol="SHORT",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            raw=raw,
            source="custom",
        )
        assert bar.open == Decimal("100")
        assert bar.high == Decimal("110")
        assert bar.low == Decimal("95")
        assert bar.close == Decimal("105")
        assert bar.volume == Decimal("10000")
        assert bar.source == "custom"

    def test_from_dict_long_keys(self):
        raw = {"open": 200, "high": 210, "low": 195, "close": 205, "volume": 20000}
        bar = DataNormalizer.from_dict(
            symbol="LONG",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            raw=raw,
        )
        assert bar.open == Decimal("200")
        assert bar.close == Decimal("205")

    def test_from_alpaca_bar(self):
        raw = {
            "t": "2025-01-01T00:00:00+00:00",
            "o": 150.25,
            "h": 152.00,
            "l": 149.50,
            "c": 151.75,
            "v": 35000,
        }
        bar = DataNormalizer.from_alpaca_bar(symbol="AAPL", raw=raw)
        assert bar.symbol == "AAPL"
        assert bar.open == Decimal("150.25")
        assert bar.close == Decimal("151.75")
        assert bar.source == "alpaca"
