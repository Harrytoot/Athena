import logging
from datetime import datetime, timezone

from app.ingestion.realtime.realtime_tick_provider import RealtimeTickProvider
from app.ingestion.realtime.schemas import BarData, MarketTick

logger = logging.getLogger(__name__)


class ReplayFeed(RealtimeTickProvider):

    def __init__(self, recorded_ticks: list[dict] | None = None):
        self._recorded_ticks: list[dict] = recorded_ticks or []
        self._cursor: int = 0
        self._bar_cache: dict[str, list[BarData]] = {}

    def load_ticks(self, ticks_data: list[dict]) -> None:
        self._recorded_ticks = ticks_data
        self._cursor = 0

    def append_tick(self, tick: MarketTick) -> None:
        self._recorded_ticks.append({
            "symbol": tick.symbol,
            "name": tick.name,
            "price": tick.price,
            "change_pct": tick.change_pct,
            "volume": tick.volume,
            "turnover": tick.turnover,
            "high": tick.high,
            "low": tick.low,
            "open": tick.open,
            "pre_close": tick.pre_close,
            "bid_price": tick.bid_price,
            "ask_price": tick.ask_price,
            "bid_volume": tick.bid_volume,
            "ask_volume": tick.ask_volume,
            "timestamp": tick.timestamp,
        })

    async def get_realtime_ticks(self, symbols: list[str]) -> list[MarketTick]:
        ticks: list[MarketTick] = []
        step = len(symbols) if symbols else 1

        for i in range(step):
            idx = self._cursor + i
            if idx >= len(self._recorded_ticks):
                break
            data = self._recorded_ticks[idx]
            if not symbols or data.get("symbol") in symbols:
                ticks.append(MarketTick(
                    symbol=data.get("symbol", ""),
                    name=data.get("name", ""),
                    price=data.get("price", 0.0),
                    change_pct=data.get("change_pct", 0.0),
                    volume=data.get("volume", 0.0),
                    turnover=data.get("turnover", 0.0),
                    high=data.get("high", 0.0),
                    low=data.get("low", 0.0),
                    open=data.get("open", 0.0),
                    pre_close=data.get("pre_close", 0.0),
                    bid_price=data.get("bid_price", 0.0),
                    ask_price=data.get("ask_price", 0.0),
                    bid_volume=data.get("bid_volume", 0.0),
                    ask_volume=data.get("ask_volume", 0.0),
                    timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                ))

        self._cursor += step
        return ticks

    def reset_cursor(self) -> None:
        self._cursor = 0

    async def get_historical_bars(self, symbol: str, period: str) -> list[BarData]:
        cache_key = f"{symbol}:{period}"
        if cache_key in self._bar_cache:
            return self._bar_cache[cache_key]

        bars: list[BarData] = []
        symbol_ticks = [t for t in self._recorded_ticks if t.get("symbol") == symbol]

        for data in symbol_ticks:
            price = data.get("price", 0.0)
            bars.append(BarData(
                symbol=symbol,
                name=data.get("name", ""),
                open=data.get("open", data.get("pre_close", price)),
                high=data.get("high", price),
                low=data.get("low", price),
                close=price,
                volume=data.get("volume", 0.0),
                turnover=data.get("turnover", 0.0),
                timestamp=data.get("timestamp", ""),
            ))

        self._bar_cache[cache_key] = bars
        return bars

    @property
    def recorded_ticks(self) -> list[dict]:
        return list(self._recorded_ticks)

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def remaining(self) -> int:
        return max(0, len(self._recorded_ticks) - self._cursor)
