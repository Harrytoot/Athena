from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterator

from app.broker_integration.market_feed.data_normalizer import NormalizedBar


@dataclass(frozen=True)
class ReplayBar:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def to_normalized(self) -> NormalizedBar:
        return NormalizedBar(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            source="replay",
        )


@dataclass
class ReplayFeedConfig:
    start_time: datetime | None = None
    end_time: datetime | None = None
    speed_multiplier: float = 1.0
    loop: bool = False


class ReplayFeed:
    """Deterministic historical data replay feed.

    Reads pre-loaded historical bars and replays them in chronological order.
    Completely deterministic — no randomness, no external I/O during replay.
    Supports looping, speed control, and symbol filtering.
    """

    def __init__(self, config: ReplayFeedConfig | None = None):
        self.config = config or ReplayFeedConfig()
        self._bars: dict[str, list[ReplayBar]] = {}
        self._sorted_timestamps: list[datetime] = []
        self._cursor: int = 0
        self._symbols: set[str] = set()
        self._current_time: datetime | None = None
        self._is_finished: bool = False
        self._loop_count: int = 0

    def load_bars(self, bars: list[NormalizedBar]):
        """Load normalized bars into the replay feed."""
        for bar in bars:
            rbar = ReplayBar(
                symbol=bar.symbol,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            self._symbols.add(bar.symbol)
            if bar.symbol not in self._bars:
                self._bars[bar.symbol] = []
            self._bars[bar.symbol].append(rbar)

        all_timestamps: set[datetime] = set()
        for symbol_bars in self._bars.values():
            for b in symbol_bars:
                all_timestamps.add(b.timestamp)

        self._sorted_timestamps = sorted(all_timestamps)
        self._cursor = 0
        self._is_finished = False

    def load_ohlcv(
        self,
        symbol: str,
        timestamps: list[datetime],
        opens: list[Decimal],
        highs: list[Decimal],
        lows: list[Decimal],
        closes: list[Decimal],
        volumes: list[Decimal],
    ):
        """Load OHLCV data directly for a single symbol."""
        bars: list[NormalizedBar] = []
        for i in range(len(timestamps)):
            bars.append(NormalizedBar(
                symbol=symbol,
                timestamp=timestamps[i],
                open=opens[i],
                high=highs[i],
                low=lows[i],
                close=closes[i],
                volume=volumes[i],
                source="replay",
            ))
        self.load_bars(bars)

    @property
    def symbols(self) -> set[str]:
        return set(self._symbols)

    @property
    def total_bars(self) -> int:
        return sum(len(b) for b in self._bars.values())

    @property
    def total_timestamps(self) -> int:
        return len(self._sorted_timestamps)

    @property
    def current_index(self) -> int:
        return self._cursor

    @property
    def progress(self) -> float:
        if not self._sorted_timestamps:
            return 1.0
        return self._cursor / len(self._sorted_timestamps)

    @property
    def is_finished(self) -> bool:
        return self._is_finished

    @property
    def current_time(self) -> datetime | None:
        return self._current_time

    def reset(self):
        self._cursor = 0
        self._is_finished = False
        self._loop_count = 0
        self._current_time = None

    def peek(self, lookahead: int = 1) -> dict[str, ReplayBar] | None:
        """Peek at the next bar(s) without advancing cursor."""
        idx = self._cursor + lookahead - 1
        if idx >= len(self._sorted_timestamps):
            return None
        ts = self._sorted_timestamps[idx]
        result: dict[str, ReplayBar] = {}
        for symbol, bars in self._bars.items():
            for bar in bars:
                if bar.timestamp == ts:
                    result[symbol] = bar
        return result if result else None

    def advance(self) -> dict[str, ReplayBar] | None:
        """Advance cursor and return bars for the next timestamp."""
        if self._is_finished:
            return None

        if self._cursor >= len(self._sorted_timestamps):
            if self.config.loop:
                self._cursor = 0
                self._loop_count += 1
            else:
                self._is_finished = True
                self._current_time = None
                return None

        ts = self._sorted_timestamps[self._cursor]
        self._current_time = ts
        result: dict[str, ReplayBar] = {}

        for symbol, bars in self._bars.items():
            for bar in bars:
                if bar.timestamp == ts:
                    result[symbol] = bar

        self._cursor += 1

        if not self.config.loop and self._cursor >= len(self._sorted_timestamps):
            self._is_finished = True

        if self.config.start_time and self._current_time < self.config.start_time:
            return self.advance()

        if self.config.end_time and self._current_time > self.config.end_time:
            self._is_finished = True
            return None

        return result if result else None

    def advance_to(self, target_time: datetime) -> dict[str, ReplayBar] | None:
        """Advance cursor until reaching or passing target_time."""
        while not self._is_finished:
            bars = self.advance()
            if bars is None:
                return None
            if self._current_time and self._current_time >= target_time:
                return bars
        return None

    def get_bars_for_symbol(self, symbol: str) -> list[ReplayBar]:
        return list(self._bars.get(symbol, []))

    def get_prices_for_time(self, target_time: datetime) -> dict[str, Decimal]:
        """Get all close prices at or before target_time."""
        result: dict[str, Decimal] = {}
        for symbol, bars in self._bars.items():
            best: ReplayBar | None = None
            for bar in bars:
                if bar.timestamp <= target_time:
                    if best is None or bar.timestamp > best.timestamp:
                        best = bar
            if best:
                result[symbol] = best.close
        return result

    def iterate(self) -> Iterator[dict[str, ReplayBar]]:
        """Generator that yields bars timestamp by timestamp."""
        self.reset()
        while True:
            bars = self.advance()
            if bars is None:
                break
            yield bars

    def get_window(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[ReplayBar]:
        """Get bars for a symbol within a time window."""
        bars = self._bars.get(symbol, [])
        return [b for b in bars if start <= b.timestamp <= end]

    def to_dict(self) -> dict[str, list[dict]]:
        """Serialize all bars to a dict for storage."""
        result: dict[str, list[dict]] = {}
        for symbol, bars in self._bars.items():
            result[symbol] = [
                {
                    "timestamp": b.timestamp.isoformat(),
                    "open": str(b.open),
                    "high": str(b.high),
                    "low": str(b.low),
                    "close": str(b.close),
                    "volume": str(b.volume),
                }
                for b in bars
            ]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, list[dict]], config: ReplayFeedConfig | None = None) -> "ReplayFeed":
        """Deserialize from a dict."""
        feed = cls(config)
        for symbol, bar_dicts in data.items():
            bars: list[NormalizedBar] = []
            for bd in bar_dicts:
                bars.append(NormalizedBar(
                    symbol=symbol,
                    timestamp=datetime.fromisoformat(bd["timestamp"]),
                    open=Decimal(bd["open"]),
                    high=Decimal(bd["high"]),
                    low=Decimal(bd["low"]),
                    close=Decimal(bd["close"]),
                    volume=Decimal(bd["volume"]),
                    source="replay",
                ))
            feed.load_bars(bars)
        return feed
