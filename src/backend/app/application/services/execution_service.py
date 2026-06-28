import uuid
from datetime import datetime, timezone

from app.application.dtos.execution_dtos import (
    ExecutionPreviewRequest,
    ExecutionPreviewResponse,
    OrderTypeEnum,
    PaperTradeRequest,
    PaperTradeResponse,
)
from app.application.services.market_score_service import MarketScoreService
from app.application.services.stock_service import StockService

SLIPPAGE_BASE_BPS = 1.0
SLIPPAGE_VOL_SENSITIVITY = 0.15
SLIPPAGE_MAX_BPS = 50.0
IMPACT_COEFFICIENT = 0.1
IMPACT_SQRT_ALPHA = 0.5
IMPACT_MAX_BPS = 100.0
DAILY_VOLUME_ESTIMATE = 1e8
STRESS_SHOCK_PCT = -0.05
STRESS_SHOCK_SCENARIO = "闪崩 -5%"


class ExecutionService:

    def __init__(
        self,
        market_score_service: MarketScoreService,
        stock_service: StockService,
    ):
        self._market_score_service = market_score_service
        self._stock_service = stock_service

    async def preview(self, req: ExecutionPreviewRequest) -> ExecutionPreviewResponse:
        score_data = await self._market_score_service.get_score()
        volatility_index = score_data["volatility"]
        daily_vol = (100.0 - volatility_index) / 100.0 * 0.03
        daily_vol = max(0.001, daily_vol)

        notional = req.size * req.price
        participation_rate = notional / DAILY_VOLUME_ESTIMATE

        slippage_bps = SLIPPAGE_BASE_BPS
        if notional > 1e-10 and daily_vol > 0:
            trade_ratio = notional / DAILY_VOLUME_ESTIMATE
            slippage_bps += SLIPPAGE_VOL_SENSITIVITY * daily_vol * 10000 * trade_ratio
        slippage_bps = min(round(slippage_bps, 2), SLIPPAGE_MAX_BPS)

        impact_fraction = IMPACT_COEFFICIENT * (participation_rate ** IMPACT_SQRT_ALPHA)
        impact_bps = min(round(impact_fraction * 10000, 2), IMPACT_MAX_BPS)

        slippage_amount = round(notional * (slippage_bps / 10000.0), 2)
        impact_amount = round(notional * (impact_bps / 10000.0), 2)

        adverse_mult = 1 + (slippage_bps + impact_bps) / 10000.0
        if req.side.value == "BUY":
            estimated_avg_price = round(req.price * adverse_mult, 2)
        else:
            estimated_avg_price = round(req.price / adverse_mult, 2)

        total_slippage_impact = slippage_bps + impact_bps
        if req.order_type in (OrderTypeEnum.TWAP, OrderTypeEnum.VWAP):
            if req.algo_params and req.algo_params.max_participation_rate:
                cap = req.algo_params.max_participation_rate / 100.0
                if participation_rate > cap:
                    reduction = 1.0 - (participation_rate - cap) / participation_rate * 0.6
                    total_slippage_impact *= max(0.3, reduction)
                    estimated_avg_price = round(req.price * (1 + total_slippage_impact / 10000.0), 2)

        total_cost = round(notional + slippage_amount + impact_amount, 2)
        stress_loss = round(notional * abs(STRESS_SHOCK_PCT), 2)

        note = self._build_note(req.order_type, participation_rate)

        return ExecutionPreviewResponse(
            slippage_bps=slippage_bps,
            slippage_amount=slippage_amount,
            market_impact_bps=impact_bps,
            market_impact_amount=impact_amount,
            estimated_avg_price=estimated_avg_price,
            estimated_total_cost=total_cost,
            participation_rate=round(participation_rate * 100, 4),
            daily_volatility=round(daily_vol * 100, 2),
            stress_test_loss=stress_loss,
            stress_test_scenario=STRESS_SHOCK_SCENARIO,
            note=note,
        )

    async def submit_paper_trade(self, req: PaperTradeRequest) -> PaperTradeResponse:
        order_id = f"PAPER-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)

        preview = await self._preview_internal(req)
        slippage_pct = (preview.slippage_bps + preview.market_impact_bps) / 10000.0

        if req.side.value == "BUY":
            filled_price = round(req.price * (1 + slippage_pct), 2)
        else:
            filled_price = round(req.price * (1 - slippage_pct), 2)

        return PaperTradeResponse(
            order_id=order_id,
            status="FILLED",
            symbol=req.symbol,
            side=req.side.value,
            size=req.size,
            filled_price=filled_price,
            submitted_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    async def _preview_internal(self, req: PaperTradeRequest) -> ExecutionPreviewResponse:
        preview_req = ExecutionPreviewRequest(
            symbol=req.symbol,
            side=req.side,
            size=req.size,
            order_type=req.order_type,
            price=req.price,
            limit_price=req.limit_price,
            algo_params=req.algo_params,
        )
        return await self.preview(preview_req)

    def _build_note(self, order_type: OrderTypeEnum, participation_rate: float) -> str:
        pct = round(participation_rate * 100, 4)
        notes = {
            OrderTypeEnum.MARKET: f"市价单，参与率{pct:.2f}%，滑点成本已计入",
            OrderTypeEnum.LIMIT: f"限价单，参与率{pct:.2f}%，存在未成交风险",
            OrderTypeEnum.TWAP: f"TWAP算法，参与率{pct:.2f}%，时间加权降低冲击",
            OrderTypeEnum.VWAP: f"VWAP算法，参与率{pct:.2f}%，量价加权执行",
        }
        return notes.get(order_type, f"参与率{pct:.2f}%")
