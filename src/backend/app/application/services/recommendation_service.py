from datetime import datetime, timezone
from decimal import Decimal

from app.application.dtos.portfolio_dtos import PortfolioDTO
from app.application.dtos.recommendation_dtos import RecommendationDTO, RecommendationItemDTO
from app.application.services.market_service import MarketService
from app.application.services.portfolio_service import PortfolioService
from app.application.services.watchlist_service import WatchlistService
from app.domain.entities.recommendation import Recommendation, RecommendationAction, RecommendationItem, RecommendationPriority, RecommendationSource


def _generate_rules(portfolio: PortfolioDTO | None, watchlist_symbols: set[str], market_regime: str, temperature: int) -> Recommendation:
    now = datetime.now(timezone.utc)
    items: list[RecommendationItem] = []

    held_symbols: set[str] = set()
    if portfolio:
        held_symbols = {p.symbol for p in portfolio.positions}

    # Rule 1: Market regime
    if market_regime == "Bull":
        items.append(RecommendationItem(
            symbol="MARKET", name="大盘",
            action=RecommendationAction.BUY,
            priority=RecommendationPriority.MEDIUM,
            source=RecommendationSource.MARKET,
            confidence=Decimal("75"),
            reason="市场处于牛市环境，适合增加仓位",
            detail="上证指数上涨趋势明显，市场情绪积极",
        ))
    elif market_regime == "Bear":
        items.append(RecommendationItem(
            symbol="MARKET", name="大盘",
            action=RecommendationAction.WATCH,
            priority=RecommendationPriority.HIGH,
            source=RecommendationSource.MARKET,
            confidence=Decimal("85"),
            reason="市场处于熊市环境，建议控制仓位注意风险",
            detail="系统性风险较高，建议降低持仓比例",
        ))
    elif market_regime == "Volatile":
        items.append(RecommendationItem(
            symbol="MARKET", name="大盘",
            action=RecommendationAction.WATCH,
            priority=RecommendationPriority.HIGH,
            source=RecommendationSource.MARKET,
            confidence=Decimal("70"),
            reason="市场波动加剧，建议观望等待趋势明朗",
            detail="高波动环境不适合频繁交易",
        ))

    # Rule 2: Portfolio concentration risk
    if portfolio:
        for pos in portfolio.positions:
            if pos.weight_pct > Decimal("30"):
                items.append(RecommendationItem(
                    symbol=pos.symbol, name=pos.name,
                    action=RecommendationAction.SELL,
                    priority=RecommendationPriority.HIGH,
                    source=RecommendationSource.PORTFOLIO,
                    confidence=Decimal("80"),
                    reason=f"仓位占比 {pos.weight_pct:.1f}%，超过 30% 警戒线，建议减仓分散风险",
                    detail="单只股票仓位过高，集中度风险较大",
                ))

            if pos.pnl_pct < Decimal("-20"):
                items.append(RecommendationItem(
                    symbol=pos.symbol, name=pos.name,
                    action=RecommendationAction.SELL,
                    priority=RecommendationPriority.HIGH,
                    source=RecommendationSource.PORTFOLIO,
                    confidence=Decimal("90"),
                    reason=f"亏损 {pos.pnl_pct:.1f}%，超过 20% 止损线，建议止损",
                    detail="严格执行止损纪律",
                ))
            elif pos.pnl_pct < Decimal("-10"):
                items.append(RecommendationItem(
                    symbol=pos.symbol, name=pos.name,
                    action=RecommendationAction.WATCH,
                    priority=RecommendationPriority.MEDIUM,
                    source=RecommendationSource.PORTFOLIO,
                    confidence=Decimal("60"),
                    reason=f"亏损 {pos.pnl_pct:.1f}%，接近止损线，密切监控",
                    detail="可考虑设置止损单",
                ))

            # Rule 3: Overweight stocks with high PnL
            if pos.weight_pct > Decimal("15") and pos.pnl_pct > Decimal("30"):
                items.append(RecommendationItem(
                    symbol=pos.symbol, name=pos.name,
                    action=RecommendationAction.SELL,
                    priority=RecommendationPriority.MEDIUM,
                    source=RecommendationSource.PORTFOLIO,
                    confidence=Decimal("65"),
                    reason=f"盈利 {pos.pnl_pct:.1f}% 且仓位占比 {pos.weight_pct:.1f}%，建议部分止盈",
                    detail="落袋为安，锁定利润",
                ))

    # Rule 4: Watchlist stocks not held
    for symbol in watchlist_symbols:
        if symbol not in held_symbols:
            items.append(RecommendationItem(
                symbol=symbol, name="",
                action=RecommendationAction.BUY,
                priority=RecommendationPriority.LOW,
                source=RecommendationSource.FUNDAMENTAL,
                confidence=Decimal("50"),
                reason="该股票在自选列表中但尚未持仓，可关注买入机会",
            ))

    # Build summary
    buy_count = sum(1 for i in items if i.action == RecommendationAction.BUY)
    sell_count = sum(1 for i in items if i.action == RecommendationAction.SELL)

    summary_parts = []
    if market_regime == "Bear":
        summary_parts.append("市场环境偏弱，整体建议保守操作。")
    elif market_regime == "Bull":
        summary_parts.append("市场环境向好，可适度积极操作。")

    if sell_count > 0:
        summary_parts.append(f"有 {sell_count} 条卖出/减仓建议，请关注风险。")
    if buy_count > 0:
        summary_parts.append(f"有 {buy_count} 条买入/关注建议。")

    if not summary_parts:
        if temperature >= 70:
            summary_parts.append("市场情绪偏热，注意追高风险，建议控制仓位。")
        elif temperature <= 30:
            summary_parts.append("市场情绪偏冷，可关注超跌反弹机会。")
        else:
            summary_parts.append("市场情绪中性，建议维持现有策略。")

    summary = " ".join(summary_parts)

    items.sort(key=lambda x: (x.priority.value, -x.confidence))

    return Recommendation(
        id="recommendation-001",
        generated_at=now,
        market_regime=market_regime,
        market_temperature=temperature,
        items=items,
        summary=summary,
    )


def _to_dto(r: Recommendation) -> RecommendationDTO:
    return RecommendationDTO(
        generated_at=r.generated_at,
        market_regime=r.market_regime,
        market_temperature=r.market_temperature,
        items=[
            RecommendationItemDTO(
                symbol=i.symbol, name=i.name,
                action=i.action, priority=i.priority,
                source=i.source, confidence=i.confidence,
                reason=i.reason, detail=i.detail,
            )
            for i in r.items
        ],
        summary=r.summary,
    )


class RecommendationService:

    def __init__(
        self,
        market_service: MarketService,
        portfolio_service: PortfolioService,
        watchlist_service: WatchlistService,
    ):
        self._market_service = market_service
        self._portfolio_service = portfolio_service
        self._watchlist_service = watchlist_service

    async def get_recommendations(self, user_id: str) -> RecommendationDTO:
        overview = await self._market_service.get_market_overview()

        portfolio = await self._portfolio_service.get_portfolio(user_id)

        watchlists = await self._watchlist_service.list_watchlists(user_id)
        watchlist_symbols: set[str] = set()
        for wl in watchlists:
            full = await self._watchlist_service.get_watchlist(wl.id, user_id)
            if full:
                for item in full.items:
                    watchlist_symbols.add(item.symbol)

        recommendation = _generate_rules(
            portfolio=portfolio,
            watchlist_symbols=watchlist_symbols,
            market_regime=overview.market_regime.value,
            temperature=overview.temperature,
        )

        return _to_dto(recommendation)
