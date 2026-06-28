from fastapi import APIRouter, Depends

from app.api.deps import get_backtest_service
from app.application.dtos.backtest_dtos import BacktestRequest, BacktestResponse
from app.application.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtest", tags=["Backtest"])


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    req: BacktestRequest = BacktestRequest(),
    service: BacktestService = Depends(get_backtest_service),
):
    report = await service.run_backtest(symbol=req.symbol, days=req.days)
    return BacktestResponse.from_report(report)
