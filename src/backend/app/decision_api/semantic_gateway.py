from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_decision_service
from app.application.services.decision_service import DecisionService
from app.decision_api.semantic_cache import SemanticCache
from app.decision_api.semantic_controller import SemanticController
from app.decision_api.semantic_serializer import BatchRequest, BatchResponse, DecisionSemanticResponse, ExplainResponse

router = APIRouter(prefix="/decision", tags=["Decision"])

_shared_cache = SemanticCache()


async def _get_controller(
    service: DecisionService = Depends(get_decision_service),
) -> SemanticController:
    return SemanticController(
        market_score_service=service._market_score_service,
        stock_service=service._stock_service,
        cache=_shared_cache,
    )


@router.get("/{symbol}", response_model=DecisionSemanticResponse)
async def get_decision(
    symbol: str,
    controller: SemanticController = Depends(_get_controller),
):
    result = await controller.decide_response(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}")
    return result


@router.post("/batch", response_model=BatchResponse)
async def batch_decision(
    body: BatchRequest,
    controller: SemanticController = Depends(_get_controller),
):
    results = await controller.decide_batch(body.symbols)
    return BatchResponse(results=results)


@router.get("/explain/{symbol}", response_model=ExplainResponse)
async def explain_decision(
    symbol: str,
    controller: SemanticController = Depends(_get_controller),
):
    result = await controller.explain(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}")
    return result
