import asyncio
from datetime import datetime

CSI300_CODE = "000300"
CSI300_WEIGHT = 0.30
TURNOVER_WEIGHT = 0.20
BREADTH_WEIGHT = 0.25
NORTHBOUND_WEIGHT = 0.25


def _fetch_csi300_sync() -> dict:
    import akshare as ak

    df = ak.stock_zh_index_spot_em()
    row = df[df["代码"] == CSI300_CODE]
    if not row.empty:
        r = row.iloc[0]
        return {
            "code": CSI300_CODE,
            "name": "沪深300",
            "price": round(float(r["最新价"]), 2),
            "change_pct": round(float(r["涨跌幅"]), 2),
        }
    return {"code": CSI300_CODE, "name": "沪深300", "price": 0, "change_pct": 0}


def _fetch_breadth_sync() -> dict:
    import akshare as ak

    df = ak.stock_zh_a_spot_em()
    up_count = int((df["涨跌幅"] > 0).sum())
    down_count = int((df["涨跌幅"] < 0).sum())
    total_turnover = float(df["成交额"].sum())
    turnover_yi = round(total_turnover / 1e8, 2)
    return {"up_count": up_count, "down_count": down_count, "turnover": turnover_yi}


def _fetch_northbound_sync() -> float:
    import akshare as ak

    df = ak.stock_hsgt_north_net_flow_in_em()
    if df.empty:
        return 0
    latest = df.iloc[-1]
    return round(float(latest.get("当日成交净买额", 0) or 0), 2)


def _normalize_csi300(change_pct: float) -> float:
    return max(0.0, min(100.0, (change_pct + 5) * 10))


def _normalize_turnover(turnover: float) -> float:
    if turnover <= 3000:
        return (turnover / 3000) * 50
    elif turnover <= 10000:
        return 50 + ((turnover - 3000) / 7000) * 50
    return 100.0


def _normalize_breadth(up_count: int, down_count: int) -> float:
    total = up_count + down_count
    if total > 0:
        return (up_count / total) * 100
    return 50.0


def _normalize_northbound(net_flow: float) -> float:
    return max(0.0, min(100.0, (net_flow + 30) / 60 * 100))


def _determine_regime(score: int) -> str:
    if score >= 60:
        return "Bull"
    elif score >= 40:
        return "Range"
    return "Bear"


class MarketScoreService:

    def __init__(self):
        self._source = "real_data_v1"

    async def get_score(self) -> dict:
        import akshare  # noqa: F401

        now = datetime.now()

        csi300, breadth, northbound = await asyncio.gather(
            asyncio.to_thread(_fetch_csi300_sync),
            asyncio.to_thread(_fetch_breadth_sync),
            asyncio.to_thread(_fetch_northbound_sync),
        )

        csi_score = _normalize_csi300(csi300["change_pct"])
        turnover_score = _normalize_turnover(breadth["turnover"])
        breadth_score = _normalize_breadth(breadth["up_count"], breadth["down_count"])
        nb_score = _normalize_northbound(northbound)

        total = (
            CSI300_WEIGHT * csi_score
            + TURNOVER_WEIGHT * turnover_score
            + BREADTH_WEIGHT * breadth_score
            + NORTHBOUND_WEIGHT * nb_score
        )
        total = round(total)

        return {
            "score": total,
            "regime": _determine_regime(total),
            "components": {
                "csi300": {
                    "value": csi300["change_pct"],
                    "score": round(csi_score, 2),
                    "weight": CSI300_WEIGHT,
                },
                "turnover": {
                    "value": breadth["turnover"],
                    "score": round(turnover_score, 2),
                    "weight": TURNOVER_WEIGHT,
                },
                "breadth": {
                    "value": breadth["up_count"],
                    "decliners": breadth["down_count"],
                    "score": round(breadth_score, 2),
                    "weight": BREADTH_WEIGHT,
                },
                "northbound": {
                    "value": northbound,
                    "score": round(nb_score, 2),
                    "weight": NORTHBOUND_WEIGHT,
                },
            },
            "source": self._source,
            "updatedAt": now.isoformat(),
        }
