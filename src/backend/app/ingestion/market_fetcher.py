import asyncio
import logging

from app.providers.market.akshare_provider import AkShareMarketProvider
from app.providers.market.base import MarketProvider

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 30


class MarketDataFetcher:
    def __init__(self, provider: MarketProvider | None = None):
        self._provider = provider or AkShareMarketProvider()

    async def fetch_raw(self) -> dict[str, float]:
        try:
            trend, liquidity, breadth, volatility, sentiment = await asyncio.wait_for(
                asyncio.gather(
                    self._provider.get_trend(),
                    self._provider.get_liquidity(),
                    self._provider.get_breadth(),
                    self._provider.get_volatility(),
                    self._provider.get_sentiment(),
                ),
                timeout=FETCH_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning("fetch_raw timed out after %ds, returning zeros", FETCH_TIMEOUT)
            trend = liquidity = breadth = volatility = sentiment = 0.0

        raw = {
            "trend_strength": trend,
            "market_turnover": liquidity,
            "advancers_ratio": breadth,
            "volatility_index": volatility,
            "northbound_flow": sentiment,
        }

        logger.info(
            "Fetched raw features: %s",
            {k: round(v, 2) for k, v in raw.items()},
        )
        return raw
