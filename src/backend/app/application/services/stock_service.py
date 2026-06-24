from app.providers.stock.detail_base import StockDetail, StockDetailProvider


class StockService:

    def __init__(self, provider: StockDetailProvider):
        self._provider = provider

    async def get_stock_detail(self, symbol: str) -> StockDetail | None:
        return await self._provider.get_detail(symbol)
