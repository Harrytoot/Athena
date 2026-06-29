import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import DEFAULT_USER_ID
from app.application.dtos.portfolio_dtos import PortfolioCreate, PositionCreate
from app.application.dtos.watchlist_dtos import WatchlistItemCreate
from app.application.services.portfolio_service import PortfolioService
from app.application.services.watchlist_service import WatchlistService
from app.ingestion.ingestion_service import IngestionService
from app.infrastructure.persistence.repositories.portfolio_repository import PortfolioRepositoryImpl
from app.infrastructure.persistence.repositories.watchlist_repository import WatchlistRepositoryImpl
from app.providers.market.mock_provider import MockMarketProvider
from app.providers.stock.mock_detail_provider import MockStockDetailProvider
from app.providers.stock.mock_provider import MockStockSearchProvider
from app.system_bootstrap.strategy_seeder import StrategySeeder
from app.system_bootstrap.universe_loader import get_universe_loader

logger = logging.getLogger(__name__)

DEFAULT_PORTFOLIO_NAME = "初始组合"
DEFAULT_PORTFOLIO_CASH = Decimal("1000000")

BOOTSTRAP_POSITIONS = [
    {"symbol": "600519", "name": "贵州茅台", "shares": Decimal("100"), "cost_price": Decimal("1680.00")},
    {"symbol": "300750", "name": "宁德时代", "shares": Decimal("500"), "cost_price": Decimal("185.00")},
    {"symbol": "000858", "name": "五粮液", "shares": Decimal("300"), "cost_price": Decimal("142.00")},
    {"symbol": "601318", "name": "中国平安", "shares": Decimal("1000"), "cost_price": Decimal("42.50")},
    {"symbol": "002415", "name": "海康威视", "shares": Decimal("800"), "cost_price": Decimal("32.80")},
]


class BootstrapOrchestrator:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._seeded = False

    async def bootstrap(self) -> dict:
        if self._seeded:
            return {"status": "already_bootstrapped", "message": "Bootstrap already executed"}

        result: dict = {}
        user_id = DEFAULT_USER_ID
        uid = uuid.UUID(user_id)

        async with self._session_factory() as session:
            try:
                universe_loader = get_universe_loader()
                symbols = await universe_loader.load()
                result["universe_symbols"] = len(symbols)
                logger.info("[bootstrap] Universe loaded: %d symbols", len(symbols))

                seeder = StrategySeeder()
                strategy_ids = await seeder.seed(session, user_id)
                result["strategies_seeded"] = len(strategy_ids)
                logger.info("[bootstrap] Strategies seeded: %d", len(strategy_ids))

                await self._seed_watchlist(session, uid, symbols)
                result["watchlist_seeded"] = True
                logger.info("[bootstrap] Watchlist seeded with %d symbols", min(len(symbols), 10))

                await self._seed_portfolio(session, uid)
                result["portfolio_seeded"] = True
                logger.info("[bootstrap] Default portfolio created")

                await session.commit()
                self._seeded = True
                result["status"] = "ok"
                result["message"] = "System bootstrap completed successfully"
                logger.info("[bootstrap] All steps completed successfully")
            except Exception as e:
                await session.rollback()
                logger.error("[bootstrap] Failed: %s", e)
                result["status"] = "partial"
                result["error"] = str(e)
                result["message"] = "Bootstrap completed with errors"

        await self._run_ingestion_pipeline()
        return result

    async def _seed_watchlist(self, session: AsyncSession, uid: uuid.UUID, symbols: list[dict]) -> None:
        repo = WatchlistRepositoryImpl(session)
        search_provider = MockStockSearchProvider()
        service = WatchlistService(repo, search_provider)

        watchlists = await service.list_watchlists(str(uid))
        if not watchlists:
            return

        target_wl = watchlists[0]
        full_wl = await service.get_watchlist(target_wl.id, str(uid))
        if full_wl and len(full_wl.items) > 0:
            logger.info("[bootstrap] Watchlist '%s' already has %d items, skipping", target_wl.name, len(full_wl.items))
            return

        for symbol_info in symbols[:10]:
            try:
                item_data = WatchlistItemCreate(symbol=symbol_info["symbol"], name=symbol_info["name"])
                await service.add_item(target_wl.id, str(uid), item_data)
            except Exception as e:
                logger.warning("[bootstrap] Failed to add %s to watchlist: %s", symbol_info["symbol"], e)

    async def _seed_portfolio(self, session: AsyncSession, uid: uuid.UUID) -> None:
        repo = PortfolioRepositoryImpl(session)
        service = PortfolioService(repo)

        existing = await service.get_portfolio(str(uid))
        if existing and existing.position_count > 0:
            logger.info("[bootstrap] Portfolio already has %d positions, skipping", existing.position_count)
            return

        if existing is None:
            create_data = PortfolioCreate(name=DEFAULT_PORTFOLIO_NAME, cash=DEFAULT_PORTFOLIO_CASH)
            await service.create_portfolio(str(uid), create_data)
            logger.info("[bootstrap] Created default portfolio: %s", DEFAULT_PORTFOLIO_NAME)

        for pos in BOOTSTRAP_POSITIONS:
            try:
                detail_provider = MockStockDetailProvider()
                detail = await detail_provider.get_detail(pos["symbol"])
                current_price = detail.price if detail else pos["cost_price"]

                pos_data = PositionCreate(
                    symbol=pos["symbol"],
                    name=pos["name"],
                    shares=pos["shares"],
                    costPrice=pos["cost_price"],
                )
                await service.add_position(str(uid), pos_data)
                logger.info("[bootstrap] Added position: %s (%s股 @%s)", pos["symbol"], pos["shares"], pos["cost_price"])
            except Exception as e:
                logger.warning("[bootstrap] Failed to add position %s: %s", pos["symbol"], e)

    async def _run_ingestion_pipeline(self) -> None:
        try:
            provider = MockMarketProvider()
            ingestion_service = IngestionService(session_factory=self._session_factory)
            result = await ingestion_service.run_manual(provider=provider)
            logger.info("[bootstrap] Ingestion pipeline completed: %d features in %.3fs",
                        result.get("features_written", 0),
                        result.get("elapsed_seconds", 0))
        except Exception as e:
            logger.warning("[bootstrap] Ingestion pipeline failed (non-critical): %s", e)


_bootstrap: BootstrapOrchestrator | None = None


def get_bootstrap_orchestrator(session_factory: async_sessionmaker[AsyncSession] | None = None) -> BootstrapOrchestrator | None:
    global _bootstrap
    if _bootstrap is None and session_factory is not None:
        _bootstrap = BootstrapOrchestrator(session_factory)
    return _bootstrap
