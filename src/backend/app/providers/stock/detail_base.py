from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field


class MacdIndicator(BaseModel):
    diff: float
    dea: float
    histogram: float


class TechnicalIndicators(BaseModel):
    ma5: float = 0.0
    ma20: float = 0.0
    rsi: float = 50.0
    macd: MacdIndicator = Field(default_factory=lambda: MacdIndicator(diff=0, dea=0, histogram=0))


class MoneyFlow(BaseModel):
    main_force_inflow: float = Field(default=0.0, alias="mainForceInflow")
    retail_inflow: float = Field(default=0.0, alias="retailInflow")
    northbound_inflow: float = Field(default=0.0, alias="northboundInflow")

    model_config = {"populate_by_name": True}


class AiAnalysis(BaseModel):
    summary: str = ""
    risk_level: str = Field(default="medium", alias="riskLevel")
    sentiment: str = "neutral"

    model_config = {"populate_by_name": True}


class StockDetail(BaseModel):
    symbol: str
    name: str
    price: float
    change_pct: float = Field(alias="changePct")
    open: float
    high: float
    low: float
    volume: int
    turnover: float
    pe_ratio: Optional[float] = Field(default=None, alias="peRatio")
    pb_ratio: Optional[float] = Field(default=None, alias="pbRatio")
    market_cap: Optional[float] = Field(default=None, alias="marketCap")
    technical_indicators: TechnicalIndicators = Field(default_factory=TechnicalIndicators, alias="technicalIndicators")
    money_flow: MoneyFlow = Field(default_factory=MoneyFlow, alias="moneyFlow")
    ai_analysis: AiAnalysis = Field(default_factory=AiAnalysis, alias="aiAnalysis")

    model_config = {"populate_by_name": True}


class StockDetailProvider(ABC):

    @abstractmethod
    async def get_detail(self, symbol: str) -> Optional[StockDetail]:
        ...
