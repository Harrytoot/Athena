import json
import logging
from typing import Optional

from app.infrastructure.cache.redis import get_redis
from app.providers.stock.base import StockSearchProvider, StockSearchResult
from app.providers.stock.detail_base import (
    AiAnalysis,
    MacdIndicator,
    MoneyFlow,
    StockDetail,
    StockDetailProvider,
    TechnicalIndicators,
)

logger = logging.getLogger(__name__)

REDIS_KEY_STOCK_SEARCH_INDEX = "athena:stock:search_index"
REDIS_KEY_STOCK_DETAIL = "athena:stock:detail"


class RedisStockSearchProvider(StockSearchProvider):

    async def search(self, query: str, limit: int = 20) -> list[StockSearchResult]:
        r = await get_redis()
        q = query.strip().lower()
        results: list[StockSearchResult] = []

        try:
            members = await r.smembers(REDIS_KEY_STOCK_SEARCH_INDEX)
        except Exception as e:
            logger.error("Failed to read stock search index: %s", e)
            return results

        for raw in members:
            try:
                item = json.loads(raw)
                symbol = str(item.get("symbol", ""))
                name = str(item.get("name", ""))
                if q in symbol or q in name.lower():
                    market = "SH" if symbol.startswith(("6", "5", "9")) else "SZ"
                    results.append(StockSearchResult(symbol=symbol, name=name, market=market))
                    if len(results) >= limit:
                        break
            except json.JSONDecodeError:
                continue

        return results


class RedisStockDetailProvider(StockDetailProvider):

    async def get_detail(self, symbol: str) -> Optional[StockDetail]:
        r = await get_redis()
        key = f"{REDIS_KEY_STOCK_DETAIL}:{symbol}"
        raw = await r.hgetall(key)

        if not raw:
            logger.info("No Redis detail for %s", symbol)
            return None

        try:
            price = float(raw.get("price", 0))
            return StockDetail(
                symbol=symbol,
                name=str(raw.get("name", symbol)),
                price=price,
                change_pct=float(raw.get("change_pct", 0)),
                open=float(raw.get("open", price)),
                high=float(raw.get("high", price)),
                low=float(raw.get("low", price)),
                volume=int(raw.get("volume", 0)),
                turnover=float(raw.get("turnover", 0)),
                pe_ratio=None,
                pb_ratio=None,
                market_cap=None,
                technical_indicators=TechnicalIndicators(
                    ma5=0, ma20=0, rsi=50,
                    macd=MacdIndicator(diff=0, dea=0, histogram=0),
                ),
                money_flow=MoneyFlow(main_force_inflow=0, retail_inflow=0, northbound_inflow=0),
                ai_analysis=AiAnalysis(summary="", risk_level="medium", sentiment="neutral"),
            )
        except Exception as e:
            logger.error("Failed to parse stock detail for %s: %s", symbol, e)
            return None
