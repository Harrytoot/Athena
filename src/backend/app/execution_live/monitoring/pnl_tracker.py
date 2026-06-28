from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class PnLSnapshot:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_equity: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    position_value: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")
    commissions: Decimal = Decimal("0")
    slippage_cost: Decimal = Decimal("0")

    @property
    def total_return_pct(self) -> Decimal:
        initial = self.total_equity - self.total_pnl
        if initial <= 0:
            return Decimal("0")
        return (self.total_pnl / initial) * Decimal("100")


class PnLTracker:

    def __init__(self, initial_equity: Decimal = Decimal("0")):
        self._initial_equity = initial_equity
        self._snapshots: list[PnLSnapshot] = []
        self._current: PnLSnapshot = PnLSnapshot(total_equity=initial_equity, cash=initial_equity)
        self._realized_pnl_total: Decimal = Decimal("0")
        self._commission_total: Decimal = Decimal("0")
        self._slippage_total: Decimal = Decimal("0")
        self._trade_count: int = 0
        self._win_count: int = 0
        self._loss_count: int = 0

    def record_trade(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        exit_price: Decimal,
        commission: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
    ):
        pnl = Decimal("0")
        if side == "sell":
            pnl = quantity * (exit_price - entry_price)
        else:
            pnl = quantity * (entry_price - exit_price)

        pnl -= commission
        pnl -= slippage

        self._realized_pnl_total += pnl
        self._commission_total += commission
        self._slippage_total += slippage
        self._trade_count += 1

        if pnl > 0:
            self._win_count += 1
        elif pnl < 0:
            self._loss_count += 1

    def record_realized_pnl(self, pnl: Decimal):
        self._realized_pnl_total += pnl
        self._trade_count += 1
        if pnl > 0:
            self._win_count += 1
        elif pnl < 0:
            self._loss_count += 1

    def snapshot(
        self,
        equity: Decimal | None = None,
        cash: Decimal | None = None,
        position_value: Decimal | None = None,
        unrealized_pnl: Decimal | None = None,
    ) -> PnLSnapshot:
        if equity is not None:
            self._current.total_equity = equity
        if cash is not None:
            self._current.cash = cash
        if position_value is not None:
            self._current.position_value = position_value
        if unrealized_pnl is not None:
            self._current.unrealized_pnl = unrealized_pnl

        self._current.realized_pnl = self._realized_pnl_total
        self._current.commissions = self._commission_total
        self._current.slippage_cost = self._slippage_total
        self._current.total_pnl = self._realized_pnl_total + (unrealized_pnl or Decimal("0"))

        if self._snapshots:
            prev = self._snapshots[-1]
            self._current.daily_pnl = self._current.total_equity - prev.total_equity
        else:
            self._current.daily_pnl = Decimal("0")

        self._current.timestamp = datetime.now(timezone.utc)
        self._snapshots.append(self._current)

        self._current = PnLSnapshot(
            total_equity=self._current.total_equity,
            cash=self._current.cash,
            position_value=self._current.position_value,
            realized_pnl=self._realized_pnl_total,
            unrealized_pnl=self._current.unrealized_pnl,
            total_pnl=self._current.total_pnl,
            daily_pnl=self._current.daily_pnl,
            commissions=self._commission_total,
            slippage_cost=self._slippage_total,
        )

        if len(self._snapshots) > 10000:
            self._snapshots = self._snapshots[-5000:]

        return self._snapshots[-1]

    def get_latest(self) -> PnLSnapshot | None:
        if self._snapshots:
            return self._snapshots[-1]
        return self._current

    def get_snapshots(self, limit: int | None = None) -> list[PnLSnapshot]:
        if limit is None:
            return list(self._snapshots)
        return self._snapshots[-limit:]

    def get_stats(self) -> dict:
        total_return = Decimal("0")
        peak = self._initial_equity or Decimal("0")
        latest_eq = self._initial_equity or Decimal("0")
        if self._snapshots:
            latest = self._snapshots[-1]
            total_return = latest.total_return_pct
            peak = max((s.total_equity for s in self._snapshots), default=Decimal("0"))
            latest_eq = latest.total_equity

        return {
            "total_return_pct": str(total_return),
            "total_realized_pnl": str(self._realized_pnl_total),
            "total_commission": str(self._commission_total),
            "total_slippage": str(self._slippage_total),
            "trade_count": self._trade_count,
            "win_count": self._win_count,
            "loss_count": self._loss_count,
            "win_rate": round(self._win_count / self._trade_count, 4) if self._trade_count > 0 else 0.0,
            "peak_equity": str(peak),
            "latest_equity": str(latest_eq),
        }

    def reset(self):
        self._snapshots.clear()
        self._current = PnLSnapshot(total_equity=self._initial_equity, cash=self._initial_equity)
        self._realized_pnl_total = Decimal("0")
        self._commission_total = Decimal("0")
        self._slippage_total = Decimal("0")
        self._trade_count = 0
        self._win_count = 0
        self._loss_count = 0
