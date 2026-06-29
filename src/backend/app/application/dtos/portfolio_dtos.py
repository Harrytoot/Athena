from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import Field
from app.application.dtos.base import BaseModel


class PositionDTO(BaseModel):
    id: Optional[str] = None
    symbol: str
    name: str
    shares: Decimal
    cost_price: Decimal = Field(alias="costPrice")
    current_price: Optional[Decimal] = Field(default=None, alias="currentPrice")
    market_value: Decimal = Field(default=Decimal("0"), alias="marketValue")
    pnl: Decimal = Field(default=Decimal("0"))
    pnl_pct: Decimal = Field(default=Decimal("0"), alias="pnlPct")
    weight_pct: Decimal = Field(default=Decimal("0"), alias="weightPct")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    model_config = {"populate_by_name": True}


class PortfolioDTO(BaseModel):
    id: Optional[str] = None
    name: str
    cash: Decimal
    total_assets: Decimal = Field(default=Decimal("0"), alias="totalAssets")
    total_cost: Decimal = Field(default=Decimal("0"), alias="totalCost")
    total_market_value: Decimal = Field(default=Decimal("0"), alias="totalMarketValue")
    total_pnl: Decimal = Field(default=Decimal("0"), alias="totalPnl")
    total_pnl_pct: Decimal = Field(default=Decimal("0"), alias="totalPnlPct")
    position_count: int = Field(default=0, alias="positionCount")
    positions: list[PositionDTO] = Field(default_factory=list)
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class PortfolioCreate(BaseModel):
    name: str
    cash: Decimal = Decimal("0")


class PositionCreate(BaseModel):
    symbol: str
    name: str
    shares: Decimal
    cost_price: Decimal = Field(alias="costPrice")

    model_config = {"populate_by_name": True}


class PositionUpdate(BaseModel):
    shares: Optional[Decimal] = None
    cost_price: Optional[Decimal] = Field(default=None, alias="costPrice")

    model_config = {"populate_by_name": True}
