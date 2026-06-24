from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_stock_service
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
