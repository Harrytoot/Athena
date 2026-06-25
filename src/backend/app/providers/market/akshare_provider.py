import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.providers.market.base import (
    HotItem,
    IndexData,
    Indices,
    MarketOverview,
    MarketProvider,
    MarketRegime,
)

logger = logging.getLogger(__name__)

CSI300_WEIGHT = 0.30
TURNOVER_WEIGHT = 0.20
BREADTH_WEIGHT = 0.25
NORTHBOUND_WEIGHT = 0.25


def _fetch_indices_sync() -> dict:
    import akshare as ak

    index_specs = {
        "shanghai": ("000001", "上证指数"),
        "shenzhen": ("399001", "深证成指"),
        "chi_next": ("399006", "创业板指"),
        "csi300": ("000300", "沪深300"),
    }
    result = {}
    try:
        df = ak.stock_zh_index_spot_em()
        for key, (code, name) in index_specs.items():
            row = df[df["代码"] == code]
            if not row.empty:
                r = row.iloc[0]
                result[key] = IndexData(
                    code=code,
                    name=name,
                    price=round(float(r["最新价"]), 2),
                    change_pct=round(float(r["涨跌幅"]), 2),
                )
            else:
                result[key] = IndexData(code=code, name=name, price=0, change_pct=0)
    except Exception as e:
        logger.error("Failed to fetch index data: %s", e)
        for key, (code, name) in index_specs.items():
            result[key] = IndexData(code=code, name=name, price=0, change_pct=0)
    return result


def _fetch_breadth_sync() -> dict:
    import akshare as ak

    try:
        df = ak.stock_zh_a_spot_em()
        up_count = int((df["涨跌幅"] > 0).sum())
        down_count = int((df["涨跌幅"] < 0).sum())
        total_turnover = float(df["成交额"].sum())
        turnover_yi = round(total_turnover / 1e8, 2)
        return {"up_count": up_count, "down_count": down_count, "turnover": turnover_yi}
    except Exception as e:
        logger.error("Failed to fetch market breadth: %s", e)
        return {"up_count": 0, "down_count": 0, "turnover": 0}


def _fetch_northbound_sync() -> float:
    import akshare as ak

    try:
        df = ak.stock_hsgt_north_net_flow_in_em()
        if df.empty:
            return 0
        latest = df.iloc[-1]
        net_flow = float(latest.get("当日成交净买额", 0) or 0)
        return round(net_flow, 2)
    except Exception as e:
        logger.error("Failed to fetch northbound flow: %s", e)
        return 0


def _fetch_hot_industries_sync() -> list[HotItem]:
    import akshare as ak

    try:
        df = ak.stock_board_industry_name_em()
        items = []
        for _, row in df.head(10).iterrows():
            items.append(HotItem(
                name=str(row["板块名称"]),
                change_pct=round(float(row["涨跌幅"]), 2),
            ))
        return items
    except Exception as e:
        logger.error("Failed to fetch hot industries: %s", e)
        return []


def _compute_temperature(
    csi300_change: float,
    turnover: float,
    up_count: int,
    down_count: int,
    northbound: float,
) -> int:
    csi_score = max(0.0, min(100.0, (csi300_change + 5) * 10))

    if turnover <= 3000:
        turnover_score = (turnover / 3000) * 50
    elif turnover <= 10000:
        turnover_score = 50 + ((turnover - 3000) / 7000) * 50
    else:
        turnover_score = 100.0

    total_count = up_count + down_count
    if total_count > 0:
        breadth_ratio = up_count / total_count
    else:
        breadth_ratio = 0.5
    breadth_score = breadth_ratio * 100

    nb_score = max(0.0, min(100.0, (northbound + 30) / 60 * 100))

    score = (
        CSI300_WEIGHT * csi_score
        + TURNOVER_WEIGHT * turnover_score
        + BREADTH_WEIGHT * breadth_score
        + NORTHBOUND_WEIGHT * nb_score
    )
    return round(score)


def _determine_regime(temperature: int) -> MarketRegime:
    if temperature >= 60:
        return MarketRegime.BULL
    elif temperature >= 40:
        return MarketRegime.RANGE
    return MarketRegime.BEAR


def _generate_summary(
    temperature: int,
    regime: MarketRegime,
    csi300: IndexData,
    up_count: int,
    down_count: int,
    turnover: float,
    northbound: float,
) -> str:
    change_sign = "+" if csi300.change_pct >= 0 else ""
    northbound_sign = "净流入" if northbound >= 0 else "净流出"
    if regime == MarketRegime.BULL:
        vibe = "市场情绪偏暖"
    elif regime == MarketRegime.BEAR:
        vibe = "市场情绪偏冷"
    else:
        vibe = "市场情绪中性"
    return (
        f"沪深300 {change_sign}{csi300.change_pct:.2f}%，"
        f"成交额 {turnover:.0f}亿，"
        f"上涨 {up_count} 家 / 下跌 {down_count} 家，"
        f"北向资金{northbound_sign} {abs(northbound):.1f}亿。"
        f"{vibe}，综合评分 {temperature}。"
    )


class AkShareMarketProvider(MarketProvider):

    async def get_overview(self) -> MarketOverview:
        try:
            import akshare  # noqa: F401
        except ImportError:
            logger.error("akshare is not installed; cannot fetch real market data")
            raise

        now = datetime.now(timezone(timedelta(hours=8)))

        indices, breadth, northbound, hot_industries = await asyncio.gather(
            asyncio.to_thread(_fetch_indices_sync),
            asyncio.to_thread(_fetch_breadth_sync),
            asyncio.to_thread(_fetch_northbound_sync),
            asyncio.to_thread(_fetch_hot_industries_sync),
        )

        csi300 = indices.get("csi300", IndexData(code="000300", name="沪深300", price=0, change_pct=0))
        csi300_change = csi300.change_pct if isinstance(csi300, IndexData) else 0

        temperature = _compute_temperature(
            csi300_change=csi300_change,
            turnover=breadth["turnover"],
            up_count=breadth["up_count"],
            down_count=breadth["down_count"],
            northbound=northbound,
        )
        regime = _determine_regime(temperature)
        summary = _generate_summary(
            temperature=temperature,
            regime=regime,
            csi300=csi300,
            up_count=breadth["up_count"],
            down_count=breadth["down_count"],
            turnover=breadth["turnover"],
            northbound=northbound,
        )

        return MarketOverview(
            marketRegime=regime,
            temperature=temperature,
            indices=Indices(
                shanghai=indices.get("shanghai", IndexData(code="000001", name="上证指数", price=0, change_pct=0)),
                shenzhen=indices.get("shenzhen", IndexData(code="399001", name="深证成指", price=0, change_pct=0)),
                chi_next=indices.get("chi_next", IndexData(code="399006", name="创业板指", price=0, change_pct=0)),
            ),
            turnover=breadth["turnover"],
            upCount=breadth["up_count"],
            downCount=breadth["down_count"],
            northbound=northbound,
            hotIndustries=hot_industries,
            hotConcepts=[],
            summary=summary,
            updatedAt=now,
        )
