import random
from datetime import datetime, timezone, timedelta

from app.providers.market.base import (
    HotItem,
    IndexData,
    Indices,
    MarketOverview,
    MarketProvider,
    MarketRegime,
)


class MockMarketProvider(MarketProvider):

    async def get_overview(self) -> MarketOverview:
        now = datetime.now(timezone(timedelta(hours=8)))
        return MarketOverview(
            market_regime=MarketRegime.BULL,
            temperature=78,
            indices=Indices(
                shanghai=IndexData(code="000001", name="上证指数", price=3150.42, change_pct=0.85),
                shenzhen=IndexData(code="399001", name="深证成指", price=10420.35, change_pct=1.23),
                chi_next=IndexData(code="399006", name="创业板指", price=2150.18, change_pct=1.56),
            ),
            turnover=15600.0,
            up_count=3812,
            down_count=1286,
            northbound=58.7,
            hot_industries=[
                HotItem(name="半导体", change_pct=4.2),
                HotItem(name="AI", change_pct=3.8),
                HotItem(name="新能源", change_pct=3.1),
                HotItem(name="消费电子", change_pct=2.9),
                HotItem(name="医疗", change_pct=2.6),
                HotItem(name="军工", change_pct=2.3),
                HotItem(name="通信", change_pct=2.1),
                HotItem(name="汽车", change_pct=1.9),
                HotItem(name="银行", change_pct=1.7),
                HotItem(name="地产", change_pct=1.5),
            ],
            hot_concepts=[
                HotItem(name="ChatGPT", change_pct=5.1),
                HotItem(name="光刻机", change_pct=4.7),
                HotItem(name="存储芯片", change_pct=4.3),
                HotItem(name="机器人", change_pct=3.9),
                HotItem(name="卫星导航", change_pct=3.6),
                HotItem(name="光伏", change_pct=3.2),
                HotItem(name="新能源汽车", change_pct=2.8),
                HotItem(name="AI芯片", change_pct=2.7),
                HotItem(name="液冷", change_pct=2.4),
                HotItem(name="CPO", change_pct=2.2),
            ],
            summary="市场整体震荡上行，成交量温和放大，北向资金持续流入。半导体与AI板块领涨，市场情绪偏暖。",
            updated_at=now,
        )

    async def get_trend(self) -> float:
        return round(random.uniform(30, 90), 2)

    async def get_liquidity(self) -> float:
        return round(random.uniform(40, 85), 2)

    async def get_breadth(self) -> float:
        return round(random.uniform(35, 80), 2)

    async def get_volatility(self) -> float:
        return round(random.uniform(20, 70), 2)

    async def get_sentiment(self) -> float:
        return round(random.uniform(30, 75), 2)
