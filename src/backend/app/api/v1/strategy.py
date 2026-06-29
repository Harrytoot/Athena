from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DEFAULT_USER_ID, get_db
from app.application.dtos.strategy_dtos import (
    StrategyCreateRequest,
    StrategyResponse,
    StrategyUpdateRequest,
)
from app.application.services.strategy_service import StrategyService
from app.infrastructure.persistence.repositories.strategy_repository import StrategyRepositoryImpl

router = APIRouter(tags=["strategy"])


async def get_strategy_service(session: AsyncSession = Depends(get_db)) -> StrategyService:
    repo = StrategyRepositoryImpl(session)
    return StrategyService(repo)


@router.get("/strategies", response_model=list[StrategyResponse])
async def list_strategies(service: StrategyService = Depends(get_strategy_service)):
    return await service.list_strategies(DEFAULT_USER_ID)


@router.get("/strategies/templates", response_model=list[StrategyResponse])
async def list_templates(service: StrategyService = Depends(get_strategy_service)):
    return await service.list_templates()


@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    data: StrategyCreateRequest,
    service: StrategyService = Depends(get_strategy_service),
):
    return await service.create_strategy(DEFAULT_USER_ID, data)


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    service: StrategyService = Depends(get_strategy_service),
):
    result = await service.get_strategy(strategy_id, DEFAULT_USER_ID)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="策略不存在")
    return result


@router.put("/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    data: StrategyUpdateRequest,
    service: StrategyService = Depends(get_strategy_service),
):
    result = await service.update_strategy(strategy_id, DEFAULT_USER_ID, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="策略不存在")
    return result


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    service: StrategyService = Depends(get_strategy_service),
):
    deleted = await service.delete_strategy(strategy_id, DEFAULT_USER_ID)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="策略不存在")
