from fastapi import APIRouter, Depends

from app.api.deps import get_execution_service
from app.application.dtos.execution_dtos import (
    ExecutionPreviewRequest,
    ExecutionPreviewResponse,
    PaperTradeRequest,
    PaperTradeResponse,
)
from app.application.services.execution_service import ExecutionService

router = APIRouter(prefix="/execution", tags=["Execution"])


@router.post("/preview", response_model=ExecutionPreviewResponse)
async def preview_execution(
    req: ExecutionPreviewRequest,
    service: ExecutionService = Depends(get_execution_service),
):
    return await service.preview(req)


@router.post("/paper-trade", response_model=PaperTradeResponse)
async def submit_paper_trade(
    req: PaperTradeRequest,
    service: ExecutionService = Depends(get_execution_service),
):
    return await service.submit_paper_trade(req)
