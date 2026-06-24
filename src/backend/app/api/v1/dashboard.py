from fastapi import APIRouter, Depends

from app.application.dtos.market_dtos import DashboardSummary
from app.application.services.market_service import MarketService
from app.api.deps import get_market_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardSummary)
async def get_dashboard(service: MarketService = Depends(get_market_service)):
    return await service.get_dashboard()
