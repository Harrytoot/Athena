from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_stock_service
from app.application.dtos.kline_dtos import KlineResponse, generate_mock_kline
from app.application.services.stock_service import StockService
from app.providers.stock.detail_base import StockDetail

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/{symbol}", response_model=StockDetail)
async def get_stock_detail(
    symbol: str,
    service: StockService = Depends(get_stock_service),
):
    result = await service.get_stock_detail(symbol)
    if not result:
        raise HTTPException(status_code=404, detail="Stock not found")
    return result


@router.get("/{symbol}/kline", response_model=KlineResponse)
async def get_stock_kline(
    symbol: str,
    period: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    limit: int = Query(default=200, ge=50, le=500),
):
    return generate_mock_kline(symbol, days=limit)
