from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderTypeEnum(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    TWAP = "TWAP"
    VWAP = "VWAP"


class TradeSideEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class AlgoParams(BaseModel):
    duration_minutes: Optional[int] = Field(default=None, alias="durationMinutes")
    max_participation_rate: Optional[float] = Field(default=None, alias="maxParticipationRate")

    model_config = {"populate_by_name": True}


class ExecutionPreviewRequest(BaseModel):
    symbol: str
    side: TradeSideEnum
    size: int
    order_type: OrderTypeEnum = Field(alias="orderType")
    price: float
    limit_price: Optional[float] = Field(default=None, alias="limitPrice")
    algo_params: Optional[AlgoParams] = Field(default=None, alias="algoParams")

    model_config = {"populate_by_name": True}


class ExecutionPreviewResponse(BaseModel):
    slippage_bps: float = Field(alias="slippageBps")
    slippage_amount: float = Field(alias="slippageAmount")
    market_impact_bps: float = Field(alias="marketImpactBps")
    market_impact_amount: float = Field(alias="marketImpactAmount")
    estimated_avg_price: float = Field(alias="estimatedAvgPrice")
    estimated_total_cost: float = Field(alias="estimatedTotalCost")
    participation_rate: float = Field(alias="participationRate")
    daily_volatility: float = Field(alias="dailyVolatility")
    stress_test_loss: float = Field(alias="stressTestLoss")
    stress_test_scenario: str = Field(alias="stressTestScenario")
    note: str = ""

    model_config = {"populate_by_name": True}


class PaperTradeRequest(BaseModel):
    symbol: str
    side: TradeSideEnum
    size: int
    order_type: OrderTypeEnum = Field(alias="orderType")
    price: float
    limit_price: Optional[float] = Field(default=None, alias="limitPrice")
    algo_params: Optional[AlgoParams] = Field(default=None, alias="algoParams")

    model_config = {"populate_by_name": True}


class PaperTradeResponse(BaseModel):
    order_id: str = Field(alias="orderId")
    status: str
    symbol: str
    side: str
    size: int
    filled_price: float = Field(alias="filledPrice")
    submitted_at: str = Field(alias="submittedAt")

    model_config = {"populate_by_name": True}
