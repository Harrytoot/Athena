import random
from typing import Optional

from app.providers.stock.detail_base import (
    AiAnalysis,
    MacdIndicator,
    MoneyFlow,
    StockDetail,
    StockDetailProvider,
    TechnicalIndicators,
)


def _mock_price(symbol: str) -> float:
    seed = sum(ord(c) for c in symbol)
    rng = random.Random(seed)
    return round(rng.uniform(10.0, 500.0), 2)


def _mock_change() -> float:
    return round(random.uniform(-5.0, 5.0), 2)


class MockStockDetailProvider(StockDetailProvider):

    async def get_detail(self, symbol: str) -> Optional[StockDetail]:
        price = _mock_price(symbol)
        change = _mock_change()

        return StockDetail(
            symbol=symbol,
            name=_get_stock_name(symbol),
            price=price,
            change_pct=change,
            open=round(price * (1 - change / 200), 2),
            high=round(price * 1.03, 2),
            low=round(price * 0.97, 2),
            volume=random.randint(1000000, 50000000),
            turnover=round(price * random.randint(1000000, 50000000) / 10000, 2),
            pe_ratio=round(random.uniform(10.0, 60.0), 2),
            pb_ratio=round(random.uniform(1.0, 10.0), 2),
            market_cap=round(random.uniform(100.0, 5000.0), 2),
            technical_indicators=TechnicalIndicators(
                ma5=round(price * 1.01, 2),
                ma20=round(price * 0.99, 2),
                rsi=round(random.uniform(30.0, 70.0), 1),
                macd=MacdIndicator(
                    diff=round(random.uniform(-2.0, 2.0), 2),
                    dea=round(random.uniform(-1.5, 1.5), 2),
                    histogram=round(random.uniform(-0.5, 0.5), 2),
                ),
            ),
            money_flow=MoneyFlow(
                main_force_inflow=round(random.uniform(-5000.0, 5000.0), 2),
                retail_inflow=round(random.uniform(-3000.0, 3000.0), 2),
                northbound_inflow=round(random.uniform(-2000.0, 2000.0), 2),
            ),
            ai_analysis=AiAnalysis(
                summary=f"{_get_stock_name(symbol)}近期走势震荡，成交量温和放大。技术面MACD金叉信号出现，RSI处于中性区间。资金面主力资金小幅流入，北向资金维持净买入。",
                risk_level=random.choice(["low", "medium", "high"]),
                sentiment=random.choice(["bullish", "neutral", "bearish"]),
            ),
        )


def _get_stock_name(symbol: str) -> str:
    names = {
        "600519": "贵州茅台",
        "000858": "五粮液",
        "601318": "中国平安",
        "000333": "美的集团",
        "600036": "招商银行",
        "002415": "海康威视",
        "600276": "恒瑞医药",
        "000651": "格力电器",
        "601166": "兴业银行",
        "002475": "立讯精密",
        "600900": "长江电力",
        "000001": "平安银行",
        "601012": "隆基绿能",
        "002714": "牧原股份",
        "600809": "山西汾酒",
        "300750": "宁德时代",
        "688981": "中芯国际",
        "002230": "科大讯飞",
        "600031": "三一重工",
        "000725": "京东方A",
    }
    return names.get(symbol, f"股票{symbol}")
