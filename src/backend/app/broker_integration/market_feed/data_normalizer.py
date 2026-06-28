from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class NormalizedBar:
    """Universal bar format independent of data source."""
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Decimal | None = None
    trades: int = 0
    source: str = ""

    @property
    def typical_price(self) -> Decimal:
        return (self.high + self.low + self.close) / Decimal("3")

    @property
    def range(self) -> Decimal:
        return self.high - self.low

    @property
    def is_up(self) -> bool:
        return self.close >= self.open

    @property
    def change_pct(self) -> Decimal:
        if self.open == 0:
            return Decimal("0")
        return (self.close - self.open) / self.open * Decimal("100")


class DataNormalizer:
    """Normalizes raw market data from different sources into NormalizedBar."""

    @staticmethod
    def from_akshare_bar(
        symbol: str,
        timestamp: datetime,
        raw: dict,
    ) -> NormalizedBar:
        return NormalizedBar(
            symbol=symbol,
            timestamp=timestamp,
            open=Decimal(str(raw.get("open", 0))),
            high=Decimal(str(raw.get("high", 0))),
            low=Decimal(str(raw.get("low", 0))),
            close=Decimal(str(raw.get("close", 0))),
            volume=Decimal(str(raw.get("volume", 0))),
            vwap=Decimal(str(raw.get("vwap", 0))) if raw.get("vwap") else None,
            trades=int(raw.get("trades", 0)),
            source="akshare",
        )

    @staticmethod
    def from_dict(
        symbol: str,
        timestamp: datetime,
        raw: dict,
        source: str = "generic",
    ) -> NormalizedBar:
        return NormalizedBar(
            symbol=symbol,
            timestamp=timestamp,
            open=Decimal(str(raw.get("open", raw.get("o", 0)))),
            high=Decimal(str(raw.get("high", raw.get("h", 0)))),
            low=Decimal(str(raw.get("low", raw.get("l", 0)))),
            close=Decimal(str(raw.get("close", raw.get("c", 0)))),
            volume=Decimal(str(raw.get("volume", raw.get("v", 0)))),
            vwap=Decimal(str(raw.get("vwap", 0))) if raw.get("vwap") else None,
            trades=int(raw.get("trades", raw.get("n", 0))),
            source=source,
        )

    @staticmethod
    def from_alpaca_bar(
        symbol: str,
        raw: dict,
    ) -> NormalizedBar:
        return NormalizedBar(
            symbol=symbol,
            timestamp=datetime.fromisoformat(raw.get("t", raw.get("timestamp", ""))),
            open=Decimal(str(raw.get("o", 0))),
            high=Decimal(str(raw.get("h", 0))),
            low=Decimal(str(raw.get("l", 0))),
            close=Decimal(str(raw.get("c", 0))),
            volume=Decimal(str(raw.get("v", 0))),
            vwap=Decimal(str(raw.get("vw", 0))) if raw.get("vw") else None,
            trades=int(raw.get("n", 0)),
            source="alpaca",
        )
