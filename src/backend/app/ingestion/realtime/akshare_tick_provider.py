import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.ingestion.realtime.realtime_tick_provider import RealtimeTickProvider
from app.ingestion.realtime.schemas import BarData, MarketTick

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8))


class AkShareRealtimeTickProvider(RealtimeTickProvider):

    async def get_realtime_ticks(self, symbols: list[str]) -> list[MarketTick]:
        try:
            raw_records = await asyncio.to_thread(_fetch_spot_sync)
        except ImportError:
            logger.error("akshare is not installed; cannot fetch real-time data")
            return []
        except Exception as e:
            logger.error("Failed to fetch real-time ticks: %s", e)
            return []

        if raw_records is None:
            return []

        symbol_set = set(symbols)
        now = datetime.now(timezone.utc).isoformat()
        ticks: list[MarketTick] = []

        for row in raw_records:
            code = str(row.get("代码", ""))
            if code not in symbol_set:
                continue

            try:
                price = float(row.get("最新价", 0) or 0)
                pre_close = float(row.get("昨收", 0) or price)
                change_pct = float(row.get("涨跌幅", 0) or 0)
                volume = float(row.get("成交量", 0) or 0)
                turnover = float(row.get("成交额", 0) or 0)
                high = float(row.get("最高", price) or price)
                low = float(row.get("最低", price) or price)

                ticks.append(MarketTick(
                    symbol=code,
                    name=str(row.get("名称", code)),
                    price=price,
                    change_pct=change_pct,
                    volume=volume,
                    turnover=turnover,
                    high=high,
                    low=low,
                    open=float(row.get("今开", pre_close) or pre_close),
                    pre_close=pre_close,
                    timestamp=now,
                ))
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse tick for %s: %s", code, e)

        logger.info("Fetched %d real-time ticks for %d symbols", len(ticks), len(symbols))
        return ticks

    async def get_historical_bars(self, symbol: str, period: str) -> list[BarData]:
        try:
            raw_records = await asyncio.to_thread(_fetch_history_sync, symbol, period)
        except ImportError:
            logger.error("akshare is not installed; cannot fetch historical data")
            return []
        except Exception as e:
            logger.error("Failed to fetch historical bars for %s: %s", symbol, e)
            return []

        if raw_records is None:
            return []

        bars: list[BarData] = []
        for row in raw_records:
            try:
                bars.append(BarData(
                    symbol=symbol,
                    name=symbol,
                    open=float(row.get("开盘", 0) or 0),
                    high=float(row.get("最高", 0) or 0),
                    low=float(row.get("最低", 0) or 0),
                    close=float(row.get("收盘", 0) or 0),
                    volume=float(row.get("成交量", 0) or 0),
                    turnover=float(row.get("成交额", 0) or 0),
                    timestamp=str(row.get("日期", "")),
                ))
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse bar for %s: %s", symbol, e)

        return bars


def _fetch_spot_sync():
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    if df is None or df.empty:
        return None
    return df.to_dict("records")


def _fetch_history_sync(symbol: str, period: str):
    import akshare as ak

    period_map = {
        "1d": "daily",
        "1w": "weekly",
        "1M": "monthly",
    }
    ak_period = period_map.get(period, "daily")

    df = ak.stock_zh_a_hist(symbol=symbol, period=ak_period, adjust="qfq")
    if df is None or df.empty:
        return None
    return df.to_dict("records")
