from fastapi import APIRouter, Depends

from app.application.services.market_service import MarketService
from app.api.deps import get_market_service
from app.providers.market.base import MarketOverview

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(service: MarketService = Depends(get_market_service)):
    return await service.get_market_overview()
