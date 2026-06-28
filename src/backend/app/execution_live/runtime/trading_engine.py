import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.entities.portfolio import Portfolio, Position
from app.portfolio.allocator import CapitalAllocation
from app.portfolio.portfolio_engine import PortfolioReport
from app.portfolio.rebalancer import RebalanceAction, RebalanceResult

from app.execution_live.broker.base import Broker, OrderSide, OrderStatus
from app.execution_live.core.order_manager import OrderManager, OrderLifecycle
from app.execution_live.core.execution_router import ExecutionRouter, RoutingConfig
from app.execution_live.core.position_sync import PositionSync
from app.execution_live.core.risk_guard import RiskGuard, RiskGuardConfig
from app.execution_live.monitoring.execution_logger import ExecutionLogger, LogLevel
from app.execution_live.monitoring.pnl_tracker import PnLTracker
from app.execution_live.monitoring.latency_monitor import LatencyMonitor
from app.execution_live.runtime.kill_switch import KillSwitch
from app.execution_live.runtime.scheduler import ExecutionScheduler


@dataclass
class TradingEngineConfig:
    risk: RiskGuardConfig = field(default_factory=RiskGuardConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    cycle_id_prefix: str = "CYCLE"
    max_orders_per_cycle: int = 50
    dry_run: bool = False
    auto_sync_positions: bool = True


@dataclass
class EngineCycleResult:
    cycle_id: str
    status: str = "completed"
    orders_routed: int = 0
    orders_submitted: int = 0
    orders_filled: int = 0
    orders_rejected: int = 0
    orders_failed: int = 0
    risk_violations: int = 0
    position_changes: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0

    @property
    def duration_seconds(self) -> float:
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()


class TradingEngine:

    def __init__(
        self,
        broker: Broker,
        config: TradingEngineConfig | None = None,
        logger: ExecutionLogger | None = None,
    ):
        self.broker = broker
        self.config = config or TradingEngineConfig()
        self.risk_guard = RiskGuard(config=self.config.risk)
        self.order_manager = OrderManager()
        self.execution_router = ExecutionRouter(config=self.config.routing)
        self.position_sync = PositionSync()
        self.kill_switch = KillSwitch()
        self.scheduler = ExecutionScheduler()
        self.pnl_tracker = PnLTracker()
        self.latency_monitor = LatencyMonitor()
        self.logger = logger or ExecutionLogger()
        self._cycle_counter = 0
        self._cycle_history: list[EngineCycleResult] = []

    def run_cycle(
        self,
        portfolio_report: PortfolioReport | None = None,
        target_positions: dict[str, Decimal] | None = None,
        target_prices: dict[str, Decimal] | None = None,
        current_portfolio: Portfolio | None = None,
    ) -> EngineCycleResult:
        self._cycle_counter += 1
        cycle_id = f"{self.config.cycle_id_prefix}-{self._cycle_counter:04d}"
        result = EngineCycleResult(cycle_id=cycle_id)
        self.latency_monitor.start_event(cycle_id)

        self.logger.log_engine_cycle(cycle_id, "started")

        try:
            if self.kill_switch.should_block():
                result.status = "blocked_kill_switch"
                result.warnings.append("Kill switch is active — all orders blocked")
                self.logger.log_kill_switch("Engine cycle blocked by kill switch")
                return result

            self.risk_guard.update_positions(
                self._get_current_position_map()
            )

            account = self.broker.get_account()
            current_equity = account.equity

            routed_orders = self._route_orders(
                portfolio_report=portfolio_report,
                target_positions=target_positions,
                target_prices=target_prices,
            )

            result.orders_routed = len(routed_orders)

            if not routed_orders:
                result.status = "no_orders"
                self.logger.log_engine_cycle(cycle_id, "no_orders_to_execute")
                return result

            submitted = 0
            filled = 0
            rejected = 0
            failed = 0

            for routed in routed_orders[:self.config.max_orders_per_cycle]:
                price = target_prices.get(routed.symbol, Decimal("100")) if target_prices else Decimal("100")

                risk_result = self.risk_guard.pre_trade_check(
                    symbol=routed.symbol,
                    side=routed.side.value,
                    quantity=routed.quantity,
                    price=price,
                    current_equity=current_equity,
                    current_cash=account.cash,
                )

                if not risk_result.passed:
                    rejected += 1
                    result.risk_violations += len(risk_result.violations)
                    for violation in risk_result.violations:
                        self.logger.log_risk_violation(
                            violation,
                            symbol=routed.symbol,
                            order_id=routed.order_id,
                        )
                    self.order_manager.create_order(
                        order_id=routed.order_id,
                        symbol=routed.symbol,
                        side=routed.side,
                        quantity=routed.quantity,
                        strategy_id=routed.strategy_id,
                    )
                    self.order_manager.reject_order(routed.order_id, "; ".join(risk_result.violations))
                    continue

                managed_order = self.order_manager.create_order(
                    order_id=routed.order_id,
                    symbol=routed.symbol,
                    side=routed.side,
                    quantity=routed.quantity,
                    strategy_id=routed.strategy_id,
                )
                managed_order.transition(OrderLifecycle.VALIDATED)
                managed_order.transition(OrderLifecycle.RISK_CHECKED)

                self.logger.log_order_created(
                    order_id=routed.order_id,
                    symbol=routed.symbol,
                    side=routed.side.value,
                    quantity=routed.quantity,
                    strategy_id=routed.strategy_id,
                )

                if self.config.dry_run:
                    managed_order.transition(OrderLifecycle.CANCELLED)
                    self.logger.log(
                        event="order_dry_run",
                        order_id=routed.order_id,
                        message="Dry run — order not submitted",
                    )
                    continue

                request = routed.to_request()

                self.latency_monitor.start_event(f"submit_{routed.order_id}")
                broker_result = self.broker.submit_order(request)
                self.latency_monitor.end_event(
                    f"submit_{routed.order_id}",
                    event="order_submit",
                    order_id=routed.order_id,
                )

                managed_order.transition(OrderLifecycle.SUBMITTED)
                self.logger.log_order_submitted(
                    order_id=routed.order_id,
                    broker_order_id=broker_result.broker_order_id,
                    symbol=routed.symbol,
                )

                if broker_result.status == OrderStatus.FILLED:
                    filled += 1
                    submitted += 1
                    managed_order.apply_broker_result(broker_result)
                    self._record_fill(routed, broker_result)

                elif broker_result.status == OrderStatus.PARTIALLY_FILLED:
                    filled += 1
                    submitted += 1
                    managed_order.apply_broker_result(broker_result)
                    self._record_fill(routed, broker_result)
                    result.warnings.append(
                        f"Partial fill on {routed.symbol}: {broker_result.filled_quantity}/{routed.quantity}"
                    )

                elif broker_result.status == OrderStatus.REJECTED:
                    rejected += 1
                    managed_order.apply_broker_result(broker_result)
                    self.logger.log_order_rejected(
                        order_id=routed.order_id,
                        reason=broker_result.rejection_reason or "Unknown",
                        symbol=routed.symbol,
                    )

                elif broker_result.status == OrderStatus.FAILED:
                    failed += 1
                    managed_order.apply_broker_result(broker_result)
                    result.errors.append(
                        f"Order {routed.order_id} failed: {broker_result.rejection_reason}"
                    )

                else:
                    submitted += 1

                self.risk_guard.record_trade(broker_result.notional)

            result.orders_submitted = submitted
            result.orders_filled = filled
            result.orders_rejected = rejected
            result.orders_failed = failed

            if self.config.auto_sync_positions and current_portfolio:
                broker_positions = self.broker.get_positions()
                sync_result = self.position_sync.reconcile(current_portfolio, broker_positions)
                result.position_changes = sync_result.change_count
                self.logger.log_position_sync(sync_result)

            self.pnl_tracker.snapshot(
                equity=self.broker.get_account().equity,
                cash=self.broker.get_account().cash,
            )

        except Exception as e:
            result.status = "error"
            result.errors.append(str(e))
            self.logger.log(
                event="engine_error",
                level=LogLevel.ERROR,
                message=f"Cycle {cycle_id} error: {e}",
            )

        result.completed_at = datetime.now(timezone.utc)
        self.logger.log_engine_cycle(cycle_id, result.status)

        latency_ms = self.latency_monitor.end_event(
            cycle_id,
            event="engine_cycle",
            metadata={"orders": result.orders_routed},
        )

        self._cycle_history.append(result)
        if len(self._cycle_history) > 500:
            self._cycle_history = self._cycle_history[-250:]

        return result

    def execute_rebalance(
        self,
        rebalance_result: RebalanceResult,
        target_prices: dict[str, Decimal] | None = None,
        total_capital: Decimal | None = None,
    ) -> EngineCycleResult:
        if target_prices is None:
            target_prices = {}

        self._cycle_counter += 1
        cycle_id = f"{self.config.cycle_id_prefix}-{self._cycle_counter:04d}"
        result = EngineCycleResult(cycle_id=cycle_id)
        self.latency_monitor.start_event(cycle_id)

        self.logger.log_engine_cycle(cycle_id, "rebalance_started")

        try:
            if self.kill_switch.should_block():
                result.status = "blocked_kill_switch"
                result.warnings.append("Kill switch is active")
                return result

            account = self.broker.get_account()
            current_equity = account.equity

            submitted = 0
            filled = 0
            rejected = 0

            for action in rebalance_result.actions:
                if action.action == "hold":
                    continue

                notional = abs(action.delta)
                price = target_prices.get(action.strategy_id, Decimal("100"))
                quantity = Decimal(str(notional / float(price))) if price > 0 else Decimal("0")

                if quantity <= 0:
                    continue

                side = OrderSide.BUY if action.action == "buy" else OrderSide.SELL
                order_id = f"RB-{uuid.uuid4().hex[:8]}"

                risk_result = self.risk_guard.pre_trade_check(
                    symbol=action.strategy_id,
                    side=side.value,
                    quantity=quantity,
                    price=price,
                    current_equity=current_equity,
                    current_cash=account.cash,
                )

                if not risk_result.passed:
                    rejected += 1
                    result.risk_violations += len(risk_result.violations)
                    for violation in risk_result.violations:
                        self.logger.log_risk_violation(violation, symbol=action.strategy_id)
                    continue

                managed = self.order_manager.create_order(
                    order_id=order_id,
                    symbol=action.strategy_id,
                    side=side,
                    quantity=quantity,
                    strategy_id=action.strategy_id,
                )
                managed.transition(OrderLifecycle.VALIDATED)
                managed.transition(OrderLifecycle.RISK_CHECKED)

                self.logger.log_order_created(
                    order_id=order_id,
                    symbol=action.strategy_id,
                    side=side.value,
                    quantity=quantity,
                )

                if self.config.dry_run:
                    self.logger.log(event="order_dry_run", order_id=order_id)
                    continue

                request = managed.to_request()

                self.latency_monitor.start_event(f"submit_{order_id}")
                broker_result = self.broker.submit_order(request)
                self.latency_monitor.end_event(f"submit_{order_id}", event="order_submit", order_id=order_id)

                managed.apply_broker_result(broker_result)

                if broker_result.status == OrderStatus.FILLED:
                    filled += 1
                    submitted += 1
                    self._record_fill_simple(
                        symbol=action.strategy_id,
                        side=side.value,
                        broker_result=broker_result,
                    )

                elif broker_result.status == OrderStatus.REJECTED:
                    rejected += 1
                    self.logger.log_order_rejected(
                        order_id=order_id,
                        reason=broker_result.rejection_reason or "Unknown",
                    )

                elif broker_result.status == OrderStatus.FAILED:
                    result.errors.append(f"Order {order_id} failed")

                self.risk_guard.record_trade(broker_result.notional)

            result.orders_routed = len(rebalance_result.actions)
            result.orders_submitted = submitted
            result.orders_filled = filled
            result.orders_rejected = rejected

        except Exception as e:
            result.status = "error"
            result.errors.append(str(e))
            self.logger.log(event="engine_error", level=LogLevel.ERROR, message=str(e))

        result.completed_at = datetime.now(timezone.utc)
        self._cycle_history.append(result)
        return result

    def run_scheduled_cycle(
        self,
        portfolio_report: PortfolioReport | None = None,
        target_positions: dict[str, Decimal] | None = None,
        target_prices: dict[str, Decimal] | None = None,
        current_portfolio: Portfolio | None = None,
        now: datetime | None = None,
    ) -> EngineCycleResult | None:
        if not self.scheduler.should_run(now):
            return None

        result = self.run_cycle(
            portfolio_report=portfolio_report,
            target_positions=target_positions,
            target_prices=target_prices,
            current_portfolio=current_portfolio,
        )
        self.scheduler.mark_run(now)
        return result

    def get_status(self) -> dict:
        account = self.broker.get_account()
        positions = self.broker.get_positions()
        return {
            "connected": self.broker.is_connected(),
            "kill_switch": self.kill_switch.status_report(),
            "account": {
                "cash": str(account.cash),
                "equity": str(account.equity),
                "positions": len(positions),
            },
            "orders": {
                "active": len(self.order_manager.get_active_orders()),
                "total": self.order_manager.get_order_count(),
                "filled": self.order_manager.get_filled_count(),
                "rejected": self.order_manager.get_rejected_count(),
            },
            "cycles_completed": self._cycle_counter,
            "config": {
                "dry_run": self.config.dry_run,
                "auto_sync": self.config.auto_sync_positions,
            },
        }

    def get_cycle_history(self, limit: int = 20) -> list[EngineCycleResult]:
        return self._cycle_history[-limit:]

    def get_latency_stats(self) -> dict:
        stats = self.latency_monitor.get_stats(event="order_submit")
        return {
            "order_submit_mean_ms": stats.mean_ms,
            "order_submit_p95_ms": stats.p95_ms,
            "order_submit_p99_ms": stats.p99_ms,
            "order_submit_count": stats.count,
        }

    def _route_orders(
        self,
        portfolio_report: PortfolioReport | None = None,
        target_positions: dict[str, Decimal] | None = None,
        target_prices: dict[str, Decimal] | None = None,
    ) -> list:
        if target_positions:
            return self.execution_router.route_batch([
                {
                    "symbol": symbol,
                    "side": OrderSide.BUY if target > Decimal("0") else OrderSide.SELL,
                    "notional": str(abs(target)),
                    "price": str(target_prices.get(symbol, Decimal("100"))) if target_prices else "100",
                }
                for symbol, target in target_positions.items()
                if abs(target) > Decimal("0")
            ])

        if portfolio_report and portfolio_report.rebalance and portfolio_report.rebalance.actions:
            decisions = []
            for action in portfolio_report.rebalance.actions:
                if action.action == "hold":
                    continue
                notional = abs(action.delta)
                price = target_prices.get(action.strategy_id, Decimal("100")) if target_prices else Decimal("100")
                decisions.append({
                    "symbol": action.strategy_id,
                    "side": OrderSide.BUY if action.action == "buy" else OrderSide.SELL,
                    "notional": str(notional),
                    "price": str(price),
                    "strategy_id": action.strategy_id,
                })
            return self.execution_router.route_batch(decisions)

        return []

    def _record_fill(self, routed, broker_result):
        self.logger.log_order_filled(
            order_id=routed.order_id,
            quantity=broker_result.filled_quantity,
            price=broker_result.average_price,
            symbol=routed.symbol,
            side=routed.side.value,
        )

    def _record_fill_simple(self, symbol, side, broker_result):
        self.logger.log_order_filled(
            order_id=broker_result.broker_order_id,
            quantity=broker_result.filled_quantity,
            price=broker_result.average_price,
            symbol=symbol,
            side=side,
        )

    def _get_current_position_map(self) -> dict[str, Decimal]:
        positions = self.broker.get_positions()
        return {p.symbol: p.quantity * (p.current_price or p.average_price) for p in positions}
