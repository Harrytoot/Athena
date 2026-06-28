from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable

from app.broker_integration.market_feed.data_normalizer import NormalizedBar


@dataclass(frozen=True)
class RealtimeBar:
    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: Decimal
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None

    @property
    def mid(self) -> Decimal:
        return (self.bid + self.ask) / Decimal("2")

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid

    def to_normalized(self) -> NormalizedBar:
        return NormalizedBar(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open=self.open or self.last,
            high=self.high or self.last,
            low=self.low or self.last,
            close=self.last,
            volume=self.volume,
            source="realtime",
        )


class RealtimeFeed(ABC):
    """Abstract real-time market data feed."""

    @abstractmethod
    def subscribe(self, symbols: list[str]):
        ...

    @abstractmethod
    def unsubscribe(self, symbols: list[str]):
        ...

    @abstractmethod
    def get_latest(self, symbol: str) -> RealtimeBar | None:
        ...

    @abstractmethod
    def get_all_latest(self) -> dict[str, RealtimeBar]:
        ...

    @abstractmethod
    def is_running(self) -> bool:
        ...

    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...


@dataclass
class SimulatedRealtimeFeedConfig:
    update_interval_seconds: float = 1.0
    volatility: float = 0.001
    seed: int | None = 42


class SimulatedRealtimeFeed(RealtimeFeed):
    """In-process real-time feed for testing and demonstration.

    Generates synthetic tick data with configurable volatility.
    Uses a seeded RNG for reproducibility in replay mode.
    """

    def __init__(self, config: SimulatedRealtimeFeedConfig | None = None):
        import random

        self.config = config or SimulatedRealtimeFeedConfig()
        self._rng = random.Random(self.config.seed)
        self._bars: dict[str, RealtimeBar] = {}
        self._subscribed: set[str] = set()
        self._running = False
        self._base_prices: dict[str, Decimal] = {}
        self._callbacks: list[Callable[[str, RealtimeBar], None]] = []

    def set_base_price(self, symbol: str, price: Decimal):
        self._base_prices[symbol] = price

    def subscribe(self, symbols: list[str]):
        for s in symbols:
            self._subscribed.add(s)
            if s not in self._base_prices:
                self._base_prices[s] = Decimal("100")

    def unsubscribe(self, symbols: list[str]):
        for s in symbols:
            self._subscribed.discard(s)

    def get_latest(self, symbol: str) -> RealtimeBar | None:
        return self._bars.get(symbol)

    def get_all_latest(self) -> dict[str, RealtimeBar]:
        return dict(self._bars)

    def is_running(self) -> bool:
        return self._running

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def on_tick(self, callback: Callable[[str, RealtimeBar], None]):
        self._callbacks.append(callback)

    def generate_tick(self):
        """Generate one tick cycle for all subscribed symbols."""
        if not self._running:
            return

        now = datetime.now(timezone.utc)
        for symbol in self._subscribed:
            base = self._base_prices.get(symbol, Decimal("100"))
            change = Decimal(str(self._rng.gauss(0, self.config.volatility)))
            last = base * (Decimal("1") + change)

            spread = last * Decimal("0.001")
            bid = last - spread / Decimal("2")
            ask = last + spread / Decimal("2")

            prev = self._bars.get(symbol)
            bar = RealtimeBar(
                symbol=symbol,
                timestamp=now,
                bid=bid,
                ask=ask,
                last=last,
                volume=Decimal(str(abs(self._rng.gauss(10000, 5000)))),
                open=prev.last if prev else last,
                high=max(prev.high if prev else last, last),
                low=min(prev.low if prev else last, last),
                close=last,
            )
            self._bars[symbol] = bar

            for cb in self._callbacks:
                cb(symbol, bar)
