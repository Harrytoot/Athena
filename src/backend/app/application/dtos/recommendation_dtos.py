from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.entities.recommendation import RecommendationAction, RecommendationPriority, RecommendationSource


class RecommendationItemDTO(BaseModel):
    symbol: str
    name: str
    action: RecommendationAction
    priority: RecommendationPriority
    source: RecommendationSource
    confidence: Decimal
    reason: str
    detail: Optional[str] = None


class RecommendationDTO(BaseModel):
    generated_at: Optional[datetime] = Field(default=None, alias="generatedAt")
    market_regime: str = Field(default="", alias="marketRegime")
    market_temperature: int = Field(default=0, alias="marketTemperature")
    items: list[RecommendationItemDTO] = Field(default_factory=list)
    summary: str = ""

    model_config = {"populate_by_name": True}
