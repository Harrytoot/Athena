import json
import logging
import time
from datetime import date
from typing import Optional

import redis

from data_worker.config import (
    REDIS_KEY_HOT_SECTORS,
    REDIS_KEY_MARKET_OVERVIEW,
    REDIS_KEY_STOCK_DETAIL,
    REDIS_KEY_STOCK_SEARCH_INDEX,
    RETRY_BACKOFF_FACTOR,
    RETRY_MAX_ATTEMPTS,
)

logger = logging.getLogger(__name__)


def _with_retry(func, *args, **kwargs):
    last_exc = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            delay = RETRY_BACKOFF_FACTOR ** (attempt - 1)
            logger.warning(
                "AKShare call failed (attempt %d/%d): %s. Retrying in %ds...",
                attempt, RETRY_MAX_ATTEMPTS, exc, delay,
            )
            time.sleep(delay)
    raise last_exc


def sync_stock_list(r: redis.Redis) -> int:
    import akshare as ak

    logger.info("Fetching A-share stock list...")
    df = _with_retry(ak.stock_info_a_code_name)

    pipe = r.pipeline()
    key = REDIS_KEY_STOCK_SEARCH_INDEX
    pipe.delete(key)
    count = 0
    today = date.today().isoformat()

    for _, row in df.iterrows():
        code = str(row.get("code", "")).strip()
        name = str(row.get("name", "")).strip()
        if not code or not name:
            continue
        item = json.dumps({"symbol": code, "name": name, "updated": today})
        pipe.sadd(key, item)
        count += 1

    pipe.execute()
    logger.info("Stock list loaded: %d symbols", count)
    return count


def sync_market_overview(r: redis.Redis) -> dict:
    import akshare as ak

    logger.info("Fetching market overview...")
    now_iso = date.today().isoformat()

    overview = {
        "updated_at": now_iso,
        "indices": {},
        "turnover": 0,
        "up_count": 0,
        "down_count": 0,
        "northbound": 0,
        "market_regime": "Range",
        "temperature": 50,
        "summary": "",
    }

    index_codes = {
        "shanghai": ("000001", "上证指数"),
        "shenzhen": ("399001", "深证成指"),
        "chi_next": ("399006", "创业板指"),
    }

    try:
        df = _with_retry(ak.stock_zh_index_spot_em)
        for key, (code, name) in index_codes.items():
            row = df[df["代码"] == code]
            if not row.empty:
                overview["indices"][key] = {
                    "code": code,
                    "name": name,
                    "price": round(float(row.iloc[0]["最新价"]), 2),
                    "change_pct": round(float(row.iloc[0]["涨跌幅"]), 2),
                }
            else:
                overview["indices"][key] = {
                    "code": code, "name": name, "price": 0, "change_pct": 0,
                }
    except Exception as e:
        logger.error("Failed to fetch index data: %s", e)
        for key, (code, name) in index_codes.items():
            overview["indices"][key] = {"code": code, "name": name, "price": 0, "change_pct": 0}

    try:
        df_sector = _with_retry(ak.stock_board_industry_name_em)
        hot_industries = []
        for _, row in df_sector.head(10).iterrows():
            hot_industries.append({
                "name": row["板块名称"],
                "change_pct": round(float(row["涨跌幅"]), 2),
            })
        overview["hot_industries"] = hot_industries

        r.delete(REDIS_KEY_HOT_SECTORS)
        if hot_industries:
            r.rpush(REDIS_KEY_HOT_SECTORS, *[json.dumps(i) for i in hot_industries])
    except Exception as e:
        logger.error("Failed to fetch sector data: %s", e)
        overview["hot_industries"] = []

    r.hset(REDIS_KEY_MARKET_OVERVIEW, mapping={k: json.dumps(v) for k, v in overview.items()})
    logger.info("Market overview synced")
    return overview


def sync_stock_detail(r: redis.Redis, symbol: str) -> Optional[dict]:
    import akshare as ak

    logger.info("Fetching detail for %s...", symbol)
    try:
        df = _with_retry(ak.stock_zh_a_hist, symbol=symbol, period="daily", adjust="qfq")
    except Exception as e:
        logger.error("Failed to fetch %s: %s", symbol, e)
        return None

    if df.empty:
        return None

    latest = df.iloc[-1]
    detail = {
        "symbol": symbol,
        "name": str(latest.get("股票代码", symbol)),
        "price": round(float(latest["收盘"]), 2),
        "open": round(float(latest["开盘"]), 2),
        "high": round(float(latest["最高"]), 2),
        "low": round(float(latest["最低"]), 2),
        "change_pct": round(float(latest.get("涨跌幅", 0)), 2),
        "volume": int(latest["成交量"]) if "成交量" in latest else 0,
        "turnover": round(float(latest["成交额"]), 2) if "成交额" in latest else 0,
        "updated": date.today().isoformat(),
    }

    key = f"{REDIS_KEY_STOCK_DETAIL}:{symbol}"
    r.hset(key, mapping={k: json.dumps(v) for k, v in detail.items()})
    r.expire(key, 86400 * 7)
    return detail
