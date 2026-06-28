from datetime import datetime, timedelta
import math
import random
from typing import Optional

from pydantic import BaseModel, Field


class KlineItem(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TradeMarkDTO(BaseModel):
    time: str
    type: str
    price: float


class KlineResponse(BaseModel):
    symbol: str
    candles: list[KlineItem]
    trades: list[TradeMarkDTO] = Field(default_factory=list)


def _simple_ma(values: list[float], period: int) -> list[Optional[float]]:
    result: list[Optional[float]] = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1 : i + 1]) / period)
    return result


def generate_mock_kline(symbol: str, days: int = 200) -> KlineResponse:
    candles: list[KlineItem] = []
    close = 50.0 + random.uniform(0, 20)
    start_date = datetime.now() - timedelta(days=days)

    for i in range(days):
        date = start_date + timedelta(days=i)
        if date.weekday() >= 5:
            continue

        time_str = date.strftime("%Y-%m-%d")
        volatility = close * 0.025
        change = (random.random() - 0.48) * volatility * 2
        open_price = close
        close = close + change
        high = max(open_price, close) + random.random() * volatility * 0.5
        low = min(open_price, close) - random.random() * volatility * 0.5
        volume = 1_000_000 + random.random() * 9_000_000

        candles.append(KlineItem(
            time=time_str,
            open=round(open_price, 2),
            high=round(high, 2),
            low=round(low, 2),
            close=round(close, 2),
            volume=round(volume, 0),
        ))

    closes = [c.close for c in candles]
    ma5 = _simple_ma(closes, 5)
    ma20 = _simple_ma(closes, 20)

    trades: list[TradeMarkDTO] = []
    for i in range(1, len(candles)):
        p5 = ma5[i]
        p20 = ma20[i]
        pp5 = ma5[i - 1]
        pp20 = ma20[i - 1]
        if None not in (p5, p20, pp5, pp20):
            if pp5 <= pp20 and p5 > p20:
                trades.append(TradeMarkDTO(time=candles[i].time, type="BUY", price=candles[i].close))
            elif pp5 >= pp20 and p5 < p20:
                trades.append(TradeMarkDTO(time=candles[i].time, type="SELL", price=candles[i].close))

    return KlineResponse(symbol=symbol, candles=candles, trades=trades)
