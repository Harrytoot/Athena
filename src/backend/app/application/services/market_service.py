from app.application.dtos.market_dtos import DashboardSummary
from app.providers.market.base import MarketOverview, MarketProvider


class MarketService:

    def __init__(self, provider: MarketProvider):
        self._provider = provider

    async def get_market_overview(self) -> MarketOverview:
        return await self._provider.get_overview()

    async def get_dashboard(self) -> DashboardSummary:
        overview = await self._provider.get_overview()
        return DashboardSummary.from_market_overview(overview)
