from abc import ABC, abstractmethod

from pydantic import BaseModel


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    market: str = ""


class StockSearchProvider(ABC):

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[StockSearchResult]:
        ...
