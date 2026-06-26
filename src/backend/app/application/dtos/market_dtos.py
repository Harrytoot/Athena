from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.providers.market.base import MarketOverview


class DashboardSummary(BaseModel):
    total_assets: float = Field(default=0.0, alias="totalAssets")
    total_return_pct: float = Field(default=0.0, alias="totalReturnPct")
    watchlist_count: int = Field(default=0, alias="watchlistCount")
    position_count: int = Field(default=0, alias="positionCount")
    market_regime: str = Field(default="", alias="marketRegime")
    temperature: int = 0
    shanghai_change_pct: float = Field(default=0.0, alias="shanghaiChangePct")
    shenzhen_change_pct: float = Field(default=0.0, alias="shenzhenChangePct")
    turnover: float = 0.0
    up_count: int = Field(default=0, alias="upCount")
    down_count: int = Field(default=0, alias="downCount")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True}

    @classmethod
    def from_market_overview(cls, overview: MarketOverview) -> "DashboardSummary":
        return cls(
            market_regime=overview.market_regime.value,
            temperature=overview.temperature,
            shanghai_change_pct=overview.indices.shanghai.change_pct,
            shenzhen_change_pct=overview.indices.shenzhen.change_pct,
            turnover=overview.turnover,
            up_count=overview.up_count,
            down_count=overview.down_count,
            updated_at=overview.updated_at,
        )


class MarketScoreResponse(BaseModel):
    score: float = 0.0
    state: str = ""
    trend: float = 0.0
    liquidity: float = 0.0
    breadth: float = 0.0
    volatility: float = 0.0
    sentiment: float = 0.0
    source: str = ""
