from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MarketRegime(str, Enum):
    BULL = "Bull"
    BEAR = "Bear"
    RANGE = "Range"
    VOLATILE = "Volatile"


class IndexData(BaseModel):
    code: str
    name: str
    price: float
    change_pct: float


class Indices(BaseModel):
    shanghai: IndexData
    shenzhen: IndexData
    chi_next: IndexData


class HotItem(BaseModel):
    name: str
    change_pct: float


class MarketOverview(BaseModel):
    market_regime: MarketRegime = Field(alias="marketRegime")
    temperature: int
    indices: Indices
    turnover: float
    up_count: int = Field(alias="upCount")
    down_count: int = Field(alias="downCount")
    northbound: float
    hot_industries: list[HotItem] = Field(default_factory=list, alias="hotIndustries")
    hot_concepts: list[HotItem] = Field(default_factory=list, alias="hotConcepts")
    summary: str = ""
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    data_quality: str = Field(default="unknown", alias="dataQuality")

    model_config = {"populate_by_name": True}


class MarketProvider(ABC):

    @abstractmethod
    async def get_overview(self) -> MarketOverview:
        ...

    @abstractmethod
    async def get_trend(self) -> float:
        ...

    @abstractmethod
    async def get_liquidity(self) -> float:
        ...

    @abstractmethod
    async def get_breadth(self) -> float:
        ...

    @abstractmethod
    async def get_volatility(self) -> float:
        ...

    @abstractmethod
    async def get_sentiment(self) -> float:
        ...
