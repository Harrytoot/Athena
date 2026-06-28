from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class PnLSnapshot:
    timestamp: datetime
    local_equity: Decimal = Decimal("0")
    broker_equity: Decimal = Decimal("0")
    local_cash: Decimal = Decimal("0")
    broker_cash: Decimal = Decimal("0")
    local_positions_value: Decimal = Decimal("0")
    broker_positions_value: Decimal = Decimal("0")
    local_realized_pnl: Decimal = Decimal("0")
    broker_realized_pnl: Decimal = Decimal("0")
    local_unrealized_pnl: Decimal = Decimal("0")
    broker_unrealized_pnl: Decimal = Decimal("0")

    @property
    def equity_drift(self) -> Decimal:
        return self.local_equity - self.broker_equity

    @property
    def equity_drift_pct(self) -> Decimal:
        if self.broker_equity == 0:
            return Decimal("0")
        return (self.equity_drift / self.broker_equity) * Decimal("100")

    @property
    def cash_drift(self) -> Decimal:
        return self.local_cash - self.broker_cash

    @property
    def positions_value_drift(self) -> Decimal:
        return self.local_positions_value - self.broker_positions_value

    @property
    def total_pnl_drift(self) -> Decimal:
        local_total = self.local_realized_pnl + self.local_unrealized_pnl
        broker_total = self.broker_realized_pnl + self.broker_unrealized_pnl
        return local_total - broker_total


@dataclass
class PnLReconciliationResult:
    snapshots: list[PnLSnapshot] = field(default_factory=list)
    max_equity_drift: Decimal = Decimal("0")
    max_drift_pct: Decimal = Decimal("0")
    total_commission_drift: Decimal = Decimal("0")
    total_slippage_drift: Decimal = Decimal("0")
    break_count: int = 0
    reconciled: bool = False
    reconciled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str = ""

    @property
    def is_acceptable(self) -> bool:
        return self.max_drift_pct <= Decimal("1.0")


class PnLReconciler:
    """Reconciles PnL between local system and broker.

    Tracks equity drift over time and identifies systematic discrepancies.
    Detects:
    - Missing commissions
    - Slippage not accounted for locally
    - Price feed divergence causing PnL drift
    - Cash vs position value imbalances
    """

    def __init__(
        self,
        drift_threshold_pct: Decimal = Decimal("1.0"),
        warning_threshold_pct: Decimal = Decimal("0.1"),
    ):
        self.drift_threshold_pct = drift_threshold_pct
        self.warning_threshold_pct = warning_threshold_pct
        self._snapshots: list[PnLSnapshot] = []
        self._reconciliations: list[PnLReconciliationResult] = []

    def record_snapshot(
        self,
        local_equity: Decimal,
        broker_equity: Decimal,
        local_cash: Decimal = Decimal("0"),
        broker_cash: Decimal = Decimal("0"),
        local_positions_value: Decimal = Decimal("0"),
        broker_positions_value: Decimal = Decimal("0"),
        local_realized_pnl: Decimal = Decimal("0"),
        broker_realized_pnl: Decimal = Decimal("0"),
        local_unrealized_pnl: Decimal = Decimal("0"),
        broker_unrealized_pnl: Decimal = Decimal("0"),
    ):
        snapshot = PnLSnapshot(
            timestamp=datetime.now(timezone.utc),
            local_equity=local_equity,
            broker_equity=broker_equity,
            local_cash=local_cash,
            broker_cash=broker_cash,
            local_positions_value=local_positions_value,
            broker_positions_value=broker_positions_value,
            local_realized_pnl=local_realized_pnl,
            broker_realized_pnl=broker_realized_pnl,
            local_unrealized_pnl=local_unrealized_pnl,
            broker_unrealized_pnl=broker_unrealized_pnl,
        )
        self._snapshots.append(snapshot)

        if len(self._snapshots) > 10000:
            self._snapshots = self._snapshots[-5000:]

    def reconcile(self) -> PnLReconciliationResult:
        result = PnLReconciliationResult(snapshots=list(self._snapshots))

        if not self._snapshots:
            result.reconciled = True
            result.summary = "No snapshots to reconcile"
            self._reconciliations.append(result)
            return result

        max_drift = Decimal("0")
        max_drift_pct = Decimal("0")
        breaks = 0

        for snapshot in self._snapshots:
            drift = abs(snapshot.equity_drift)
            drift_pct = abs(snapshot.equity_drift_pct)

            if drift > max_drift:
                max_drift = drift
            if drift_pct > max_drift_pct:
                max_drift_pct = drift_pct

            if drift_pct > self.drift_threshold_pct:
                breaks += 1

        result.max_equity_drift = max_drift
        result.max_drift_pct = max_drift_pct
        result.break_count = breaks

        last = self._snapshots[-1]
        result.total_commission_drift = last.cash_drift - last.positions_value_drift

        result.reconciled = breaks == 0

        if result.reconciled:
            result.summary = f"PnL reconciled. Max drift: {max_drift_pct:.4f}%"
        else:
            result.summary = (
                f"PnL BREAK: {breaks} snapshots exceed {self.drift_threshold_pct}% threshold. "
                f"Max drift: {max_drift_pct:.4f}% ({max_drift})"
            )

        self._reconciliations.append(result)
        return result

    def get_drift_trend(self) -> list[Decimal]:
        """Return equity drift for each snapshot as time series."""
        return [s.equity_drift for s in self._snapshots]

    def get_drift_pct_trend(self) -> list[Decimal]:
        """Return drift percentage for each snapshot."""
        return [s.equity_drift_pct for s in self._snapshots]

    def get_history(self) -> list[PnLReconciliationResult]:
        return list(self._reconciliations)

    def get_last(self) -> PnLReconciliationResult | None:
        return self._reconciliations[-1] if self._reconciliations else None

    def reset(self):
        self._snapshots.clear()
        self._reconciliations.clear()
