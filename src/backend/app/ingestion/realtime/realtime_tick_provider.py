from abc import ABC, abstractmethod

from app.ingestion.realtime.schemas import BarData, MarketTick


class RealtimeTickProvider(ABC):

    @abstractmethod
    async def get_realtime_ticks(self, symbols: list[str]) -> list[MarketTick]:
        ...

    @abstractmethod
    async def get_historical_bars(self, symbol: str, period: str) -> list[BarData]:
        ...
