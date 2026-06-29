import random
from datetime import datetime, timezone

from app.ingestion.realtime.realtime_tick_provider import RealtimeTickProvider
from app.ingestion.realtime.schemas import BarData, MarketTick

_DEFAULT_SYMBOLS = [
    "000001", "000002", "600000", "600036", "601318",
    "000858", "002415", "300750", "688981", "601012",
]


class MockRealtimeTickProvider(RealtimeTickProvider):

    def __init__(self, seed: int = 42, base_prices: dict[str, float] | None = None):
        self._rng = random.Random(seed)
        self._base_prices = base_prices or {s: self._rng.uniform(10, 200) for s in _DEFAULT_SYMBOLS}
        self._sequence: dict[str, int] = {s: 0 for s in self._base_prices}

    async def get_realtime_ticks(self, symbols: list[str]) -> list[MarketTick]:
        ticks: list[MarketTick] = []
        now = datetime.now(timezone.utc).isoformat()

        for sym in symbols:
            if sym not in self._base_prices:
                self._base_prices[sym] = self._rng.uniform(10, 200)

            base = self._base_prices[sym]
            self._sequence[sym] = self._sequence.get(sym, 0) + 1
            seq = self._sequence[sym]

            drift = self._rng.uniform(-0.02, 0.02)
            price = round(base * (1 + drift * (1 + seq * 0.001)), 2)
            change_pct = round((price - base) / base * 100, 2)

            pre_close = round(base * (1 + self._rng.uniform(-0.01, 0.01)), 2)
            high = round(max(price, pre_close) * (1 + self._rng.uniform(0, 0.005)), 2)
            low = round(min(price, pre_close) * (1 - self._rng.uniform(0, 0.005)), 2)
            volume = round(self._rng.uniform(1e6, 5e7), 0)
            turnover = round(volume * price, 0)
            bid_price = round(price * (1 - self._rng.uniform(0.0001, 0.001)), 2)
            ask_price = round(price * (1 + self._rng.uniform(0.0001, 0.001)), 2)
            bid_volume = round(self._rng.uniform(1000, 100000), 0)
            ask_volume = round(self._rng.uniform(1000, 100000), 0)

            ticks.append(MarketTick(
                symbol=sym,
                name=f"Mock_{sym}",
                price=price,
                change_pct=change_pct,
                volume=volume,
                turnover=turnover,
                high=high,
                low=low,
                open=pre_close,
                pre_close=pre_close,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_volume=bid_volume,
                ask_volume=ask_volume,
                timestamp=now,
            ))

        return ticks

    async def get_historical_bars(self, symbol: str, period: str) -> list[BarData]:
        if symbol not in self._base_prices:
            self._base_prices[symbol] = self._rng.uniform(10, 200)

        base = self._base_prices[symbol]
        bars: list[BarData] = []
        periods_map = {"1d": 20, "1h": 48, "5m": 96}
        count = periods_map.get(period, 10)

        price = base
        for i in range(count):
            change = self._rng.uniform(-0.03, 0.03)
            close = round(price * (1 + change), 2)
            high = round(max(price, close) * (1 + self._rng.uniform(0, 0.01)), 2)
            low = round(min(price, close) * (1 - self._rng.uniform(0, 0.01)), 2)
            open_price = round(price * (1 + self._rng.uniform(-0.005, 0.005)), 2)
            volume = round(self._rng.uniform(5e5, 3e7), 0)

            bars.append(BarData(
                symbol=symbol,
                name=f"Mock_{symbol}",
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                turnover=round(volume * close, 0),
            ))
            price = close

        return bars
