import json
import logging
from datetime import datetime, timezone, timedelta

from app.infrastructure.cache.redis import get_redis
from app.providers.market.base import (
    HotItem,
    IndexData,
    Indices,
    MarketOverview,
    MarketProvider,
    MarketRegime,
)

logger = logging.getLogger(__name__)

REDIS_KEY_MARKET_OVERVIEW = "athena:market:overview"
REDIS_KEY_HOT_SECTORS = "athena:market:hot_sectors"


class RedisMarketProvider(MarketProvider):

    async def get_trend(self) -> float:
        return 50.0

    async def get_liquidity(self) -> float:
        return 50.0

    async def get_breadth(self) -> float:
        return 50.0

    async def get_volatility(self) -> float:
        return 50.0

    async def get_sentiment(self) -> float:
        return 50.0

    async def get_overview(self) -> MarketOverview:
        r = await get_redis()
        raw = await r.hgetall(REDIS_KEY_MARKET_OVERVIEW)

        if not raw:
            logger.info("Redis market:overview is empty, returning default overview")
            return _default_overview()

        try:
            indices_data = json.loads(_unwrap(raw.get("indices", "{}")))
            return MarketOverview(
                market_regime=MarketRegime(_unwrap(raw.get("market_regime", "Range"))),
                temperature=int(float(_unwrap(raw.get("temperature", "50")))),
                indices=Indices(
                    shanghai=_parse_index(indices_data.get("shanghai", {})),
                    shenzhen=_parse_index(indices_data.get("shenzhen", {})),
                    chi_next=_parse_index(indices_data.get("chi_next", {})),
                ),
                turnover=float(_unwrap(raw.get("turnover", "0"))),
                up_count=int(float(_unwrap(raw.get("up_count", "0")))),
                down_count=int(float(_unwrap(raw.get("down_count", "0")))),
                northbound=float(_unwrap(raw.get("northbound", "0"))),
                hot_industries=await self._get_hot_sectors(r),
                hot_concepts=[],
                summary=_unwrap(raw.get("summary", "")),
                updated_at=datetime.now(timezone(timedelta(hours=8))),
                data_quality="cached",
            )
        except Exception as e:
            logger.error("Failed to parse market overview from Redis: %s", e)
            return _default_overview()

    async def _get_hot_sectors(self, r) -> list[HotItem]:
        try:
            items = await r.lrange(REDIS_KEY_HOT_SECTORS, 0, -1)
            return [HotItem(**json.loads(item)) for item in items]
        except Exception:
            return []


def _parse_index(data: dict) -> IndexData:
    return IndexData(
        code=str(data.get("code", "")),
        name=str(data.get("name", "")),
        price=float(data.get("price", 0)),
        change_pct=float(data.get("change_pct", 0)),
    )


def _unwrap(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _default_overview() -> MarketOverview:
    return MarketOverview(
        market_regime=MarketRegime.RANGE,
        temperature=50,
        indices=Indices(
            shanghai=IndexData(code="000001", name="上证指数", price=0, change_pct=0),
            shenzhen=IndexData(code="399001", name="深证成指", price=0, change_pct=0),
            chi_next=IndexData(code="399006", name="创业板指", price=0, change_pct=0),
        ),
        turnover=0,
        up_count=0,
        down_count=0,
        northbound=0,
        hot_industries=[],
        hot_concepts=[],
        summary="市场数据尚未就绪，请等待数据同步完成。",
        updated_at=datetime.now(timezone(timedelta(hours=8))),
        data_quality="stale",
    )
