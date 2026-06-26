import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.portfolio.allocator import CapitalAllocation, AllocationResult
from app.portfolio.rebalancer import RebalanceResult, RebalanceAction
from app.portfolio.portfolio_engine import PortfolioReport

from app.execution.liquidity_model import LiquidityConfig, LiquidityModel, LiquidityProfile
from app.execution.slippage_engine import SlippageConfig, SlippageEngine, SlippageEstimate
from app.execution.order_book_simulator import (
    OrderBookConfig,
    OrderBookSimulator,
    Order,
    FillResult,
)
from app.execution.trade_scheduler import (
    LatencyConfig,
    TradeScheduler,
    ScheduledTrade,
    ScheduleResult,
    ExecutionDelay,
)
from app.execution.execution_report import ExecutionReport, ExecutionReportGenerator


@dataclass
class ExecutionConfig:
    liquidity: LiquidityConfig = field(default_factory=LiquidityConfig)
    slippage: SlippageConfig = field(default_factory=SlippageConfig)
    order_book: OrderBookConfig = field(default_factory=OrderBookConfig)
    latency: LatencyConfig = field(default_factory=LatencyConfig)
    seed: int | None = None
    total_capital: float = 1_000_000.0


@dataclass
class ExecutedTrade:
    strategy_id: str
    action: str
    requested_notional: float
    executed_notional: float
    fill_result: FillResult | None = None
    slippage: SlippageEstimate | None = None
    liquidity: LiquidityProfile | None = None
    delay: ExecutionDelay | None = None

    @property
    def execution_cost(self) -> float:
        cost = 0.0
        if self.slippage:
            cost += self.slippage.slippage_amount
        return round(cost, 4)

    @property
    def is_filled(self) -> bool:
        if self.fill_result is None:
            return False
        return self.fill_result.filled_quantity > 0


@dataclass
class ExecutionResult:
    trades: list[ExecutedTrade] = field(default_factory=list)
    schedule: ScheduleResult | None = None
    report: ExecutionReport | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_executed_notional(self) -> float:
        return round(sum(t.executed_notional for t in self.trades), 2)

    @property
    def total_slippage_cost(self) -> float:
        return round(sum(t.execution_cost for t in self.trades), 4)

    @property
    def total_fills(self) -> int:
        return len([t for t in self.trades if t.is_filled])

    @property
    def total_partial_fills(self) -> int:
        return len([
            t for t in self.trades
            if t.fill_result and t.fill_result.partial_fill
        ])

    @property
    def overall_fill_rate(self) -> float:
        if not self.trades:
            return 0.0
        requested = sum(t.requested_notional for t in self.trades)
        if requested <= 0:
            return 0.0
        return round(self.total_executed_notional / requested, 6)


class ExecutionEngine:

    def __init__(self, config: ExecutionConfig | None = None):
        self.config = config or ExecutionConfig()

        liq_cfg = self.config.liquidity
        slip_cfg = self.config.slippage
        ob_cfg = self.config.order_book
        lat_cfg = self.config.latency

        if self.config.seed is not None:
            slip_cfg = SlippageConfig(
                base_slippage_bps=slip_cfg.base_slippage_bps,
                vol_sensitivity=slip_cfg.vol_sensitivity,
                size_sensitivity=slip_cfg.size_sensitivity,
                max_slippage_bps=slip_cfg.max_slippage_bps,
                seed=self.config.seed,
            )
            ob_cfg = OrderBookConfig(
                fill_probability=ob_cfg.fill_probability,
                partial_fill_threshold=ob_cfg.partial_fill_threshold,
                min_fill_ratio=ob_cfg.min_fill_ratio,
                price_improvement_chance=ob_cfg.price_improvement_chance,
                seed=self.config.seed,
            )
            lat_cfg = LatencyConfig(
                base_latency_ms=lat_cfg.base_latency_ms,
                network_jitter_ms=lat_cfg.network_jitter_ms,
                processing_delay_ms=lat_cfg.processing_delay_ms,
                max_queue_depth=lat_cfg.max_queue_depth,
                seed=self.config.seed,
            )

        self.liquidity_model = LiquidityModel(config=liq_cfg)
        self.slippage_engine = SlippageEngine(config=slip_cfg)
        self.order_book = OrderBookSimulator(config=ob_cfg)
        self.trade_scheduler = TradeScheduler(config=lat_cfg)
        self.report_generator = ExecutionReportGenerator()

    def execute(
        self,
        portfolio_report: PortfolioReport,
        rebalance_result: RebalanceResult | None = None,
        target_prices: dict[str, float] | None = None,
        volatility_map: dict[str, float] | None = None,
    ) -> ExecutionResult:
        if rebalance_result is None:
            rebalance_result = portfolio_report.rebalance

        if rebalance_result is None or not rebalance_result.actions:
            return ExecutionResult()

        if target_prices is None:
            target_prices = {}
        if volatility_map is None:
            volatility_map = {}

        actions = [a for a in rebalance_result.actions if a.action != "hold"]

        allocations = {
            a.strategy_id: a.capital
            for a in portfolio_report.composition.allocations
        }

        trades: list[ExecutedTrade] = []
        schedule_inputs: list[tuple[str, str, float, float]] = []

        for action in actions:
            notional = abs(action.delta) * self.config.total_capital
            price = target_prices.get(action.strategy_id, 100.0)
            quantity = notional / price if price > 0 else 0.0
            vol = volatility_map.get(action.strategy_id, 0.01)

            executed_trade = self._execute_single_trade(
                action=action,
                notional=notional,
                quantity=quantity,
                reference_price=price,
                volatility=vol,
            )
            trades.append(executed_trade)

            schedule_inputs.append((
                action.strategy_id,
                action.action,
                executed_trade.executed_notional,
                executed_trade.fill_result.filled_quantity if executed_trade.fill_result else 0.0,
            ))

        schedule_result = self.trade_scheduler.schedule(schedule_inputs)

        for i, trade in enumerate(trades):
            if i < len(schedule_result.trades):
                trade.delay = schedule_result.trades[i].delay

        filled_count = len([t for t in trades if t.fill_result and t.fill_result.is_complete])
        partial_count = len([t for t in trades if t.fill_result and t.fill_result.partial_fill and t.fill_result.filled_quantity > 0])
        total_requested = sum(t.requested_notional for t in trades)
        total_executed = sum(t.executed_notional for t in trades)

        slippage_estimates = [t.slippage for t in trades if t.slippage is not None]
        liquidity_profiles = [t.liquidity for t in trades if t.liquidity is not None]

        total_orders = len(trades)
        filled_only = len([t for t in trades if t.fill_result and t.fill_result.is_complete])
        partial_filled = len([t for t in trades if t.fill_result and t.fill_result.partial_fill and t.fill_result.filled_quantity > 0])

        report = self.report_generator.generate(
            total_orders=total_orders,
            filled_count=filled_only,
            partial_count=partial_filled,
            requested_notional=total_requested,
            executed_notional=total_executed,
            slippage_estimates=slippage_estimates,
            schedule_result=schedule_result,
            liquidity_profiles=liquidity_profiles,
        )

        return ExecutionResult(
            trades=trades,
            schedule=schedule_result,
            report=report,
        )

    def execute_allocations(
        self,
        current_allocations: list[CapitalAllocation],
        target_allocations: list[CapitalAllocation],
        target_prices: dict[str, float] | None = None,
        volatility_map: dict[str, float] | None = None,
    ) -> ExecutionResult:
        if target_prices is None:
            target_prices = {}
        if volatility_map is None:
            volatility_map = {}

        current_map = {a.strategy_id: a for a in current_allocations}
        target_map = {a.strategy_id: a for a in target_allocations}
        all_ids = set(current_map.keys()) | set(target_map.keys())

        actions: list[RebalanceAction] = []
        for sid in all_ids:
            current_cap = current_map.get(sid, CapitalAllocation(strategy_id=sid, weight=0, capital=0, risk_budget=0)).capital
            target_cap = target_map.get(sid, CapitalAllocation(strategy_id=sid, weight=0, capital=0, risk_budget=0)).capital
            delta = target_cap - current_cap

            if abs(delta) < 1.0:
                continue

            action = "buy" if delta > 0 else "sell"
            total_cap = self.config.total_capital
            delta_pct = abs(delta) / total_cap if total_cap > 0 else 0.0

            actions.append(
                RebalanceAction(
                    strategy_id=sid,
                    action=action,
                    from_capital=current_cap,
                    to_capital=target_cap,
                    delta=delta,
                    delta_pct=round(delta_pct, 6),
                )
            )

        rebalance_result = RebalanceResult(
            actions=actions,
            triggered=len(actions) > 0,
            trigger_reason="allocation_change" if actions else "",
        )

        empty_composition = type('obj', (object,), {'allocations': target_allocations})()
        portfolio_report = PortfolioReport()
        portfolio_report.composition = empty_composition

        return self.execute(
            portfolio_report=portfolio_report,
            rebalance_result=rebalance_result,
            target_prices=target_prices,
            volatility_map=volatility_map,
        )

    def _execute_single_trade(
        self,
        action: RebalanceAction,
        notional: float,
        quantity: float,
        reference_price: float,
        volatility: float,
    ) -> ExecutedTrade:
        liquidity = self.liquidity_model.profile(
            strategy_id=action.strategy_id,
            trade_size=notional,
            volatility=volatility,
        )

        slippage = self.slippage_engine.estimate(
            strategy_id=action.strategy_id,
            trade_notional=notional,
            daily_volatility=volatility,
            daily_volume=liquidity.daily_volume,
            direction=action.action,
        )

        executed_price = self.slippage_engine.compute_price_slippage(
            reference_price=reference_price,
            slippage_estimate=slippage,
        )

        order = Order(
            strategy_id=action.strategy_id,
            side=action.action,
            quantity=quantity,
            limit_price=None,
            order_id=str(uuid.uuid4())[:8],
        )

        fill = self.order_book.simulate_fill(
            order=order,
            reference_price=executed_price,
            available_liquidity=liquidity.available_liquidity,
            daily_volume=liquidity.daily_volume,
        )

        executed_notional = self.order_book.compute_notional(fill)

        return ExecutedTrade(
            strategy_id=action.strategy_id,
            action=action.action,
            requested_notional=round(notional, 2),
            executed_notional=executed_notional,
            fill_result=fill,
            slippage=slippage,
            liquidity=liquidity,
        )
