from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DEFAULT_USER_ID, get_portfolio_service
from app.application.dtos.portfolio_dtos import (
    PortfolioCreate,
    PortfolioDTO,
    PositionCreate,
    PositionUpdate,
)
from app.application.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioDTO)
async def get_portfolio(service: PortfolioService = Depends(get_portfolio_service)):
    result = await service.get_portfolio(DEFAULT_USER_ID)
    if not result:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return result


@router.post("", response_model=PortfolioDTO, status_code=201)
async def create_portfolio(data: PortfolioCreate, service: PortfolioService = Depends(get_portfolio_service)):
    return await service.create_portfolio(DEFAULT_USER_ID, data)


@router.post("/positions", response_model=PortfolioDTO, status_code=201)
async def add_position(data: PositionCreate, service: PortfolioService = Depends(get_portfolio_service)):
    result = await service.add_position(DEFAULT_USER_ID, data)
    if not result:
        raise HTTPException(status_code=404, detail="Portfolio not found, create one first")
    return result


@router.patch("/positions/{position_id}", response_model=PortfolioDTO)
async def update_position(
    position_id: str,
    data: PositionUpdate,
    service: PortfolioService = Depends(get_portfolio_service),
):
    result = await service.update_position(position_id, DEFAULT_USER_ID, data)
    if not result:
        raise HTTPException(status_code=404, detail="Position not found")
    return result


@router.delete("/positions/{position_id}", status_code=204)
async def remove_position(
    position_id: str,
    service: PortfolioService = Depends(get_portfolio_service),
):
    ok = await service.remove_position(position_id, DEFAULT_USER_ID)
    if not ok:
        raise HTTPException(status_code=404, detail="Position not found")
