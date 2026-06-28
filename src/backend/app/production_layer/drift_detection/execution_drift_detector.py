from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ExecutionExpectation:
    symbol: str
    expected_price: Decimal
    expected_quantity: Decimal
    expected_slippage_bps: Decimal
    expected_fill_percentage: Decimal


@dataclass(frozen=True)
class ExecutionActual:
    symbol: str
    actual_price: Decimal
    actual_quantity: Decimal
    actual_slippage_bps: Decimal
    actual_fill_percentage: Decimal
    timestamp: datetime


@dataclass(frozen=True)
class ExecutionDriftResult:
    symbol: str
    price_drift_bps: Decimal
    quantity_drift_pct: Decimal
    slippage_drift_bps: Decimal
    fill_rate_drift_pct: Decimal
    is_drifted: bool
    drift_score: Decimal
    timestamp: datetime

    def summary(self) -> str:
        parts = []
        if abs(self.price_drift_bps) > Decimal("0"):
            parts.append(f"price={self.price_drift_bps}bps")
        if abs(self.quantity_drift_pct) > Decimal("0"):
            parts.append(f"qty={self.quantity_drift_pct}%")
        if abs(self.slippage_drift_bps) > Decimal("0"):
            parts.append(f"slippage={self.slippage_drift_bps}bps")
        if abs(self.fill_rate_drift_pct) > Decimal("0"):
            parts.append(f"fill={self.fill_rate_drift_pct}%")
        return f"{self.symbol}: drift={self.drift_score} " + ", ".join(parts) if parts else f"{self.symbol}: no drift"


@dataclass
class ExecutionDriftDetector:
    price_drift_threshold_bps: Decimal = Decimal("50")
    quantity_drift_threshold_pct: Decimal = Decimal("10")
    slippage_drift_threshold_bps: Decimal = Decimal("20")
    fill_rate_drift_threshold_pct: Decimal = Decimal("15")
    window_size: int = 100

    history: List[ExecutionDriftResult] = field(default_factory=list)

    def detect(
        self, expected: ExecutionExpectation, actual: ExecutionActual
    ) -> ExecutionDriftResult:
        if expected.symbol != actual.symbol:
            raise ValueError(
                f"Symbol mismatch: expected {expected.symbol}, actual {actual.symbol}"
            )

        price_drift = _calc_bps_drift(actual.actual_price, expected.expected_price)
        quantity_drift = _calc_pct_drift(actual.actual_quantity, expected.expected_quantity)
        slippage_drift = actual.actual_slippage_bps - expected.expected_slippage_bps
        fill_rate_drift = actual.actual_fill_percentage - expected.expected_fill_percentage

        flags = [
            abs(price_drift) > self.price_drift_threshold_bps,
            abs(quantity_drift) > self.quantity_drift_threshold_pct,
            abs(slippage_drift) > self.slippage_drift_threshold_bps,
            abs(fill_rate_drift) > self.fill_rate_drift_threshold_pct,
        ]

        drift_score = Decimal(sum(1 for f in flags if f))
        is_drifted = drift_score >= Decimal("2")

        result = ExecutionDriftResult(
            symbol=expected.symbol,
            price_drift_bps=price_drift,
            quantity_drift_pct=quantity_drift,
            slippage_drift_bps=slippage_drift,
            fill_rate_drift_pct=fill_rate_drift,
            is_drifted=is_drifted,
            drift_score=drift_score,
            timestamp=datetime.now(timezone.utc),
        )

        self.history.append(result)
        if len(self.history) > self.window_size:
            self.history = self.history[-self.window_size:]

        return result

    def recent_drift_rate(self, lookback: int = 20) -> Decimal:
        if not self.history:
            return Decimal("0")
        recent = self.history[-min(lookback, len(self.history)):]
        drifted = sum(1 for r in recent if r.is_drifted)
        return Decimal(drifted) / Decimal(len(recent))

    def is_degrading(self, lookback: int = 20, threshold: Decimal = Decimal("0.3")) -> bool:
        return self.recent_drift_rate(lookback) > threshold

    def clear_history(self) -> None:
        self.history.clear()


def _calc_bps_drift(actual: Decimal, expected: Decimal) -> Decimal:
    if expected == Decimal("0"):
        return Decimal("0")
    return ((actual - expected) / expected) * Decimal("10000")


def _calc_pct_drift(actual: Decimal, expected: Decimal) -> Decimal:
    if expected == Decimal("0"):
        return Decimal("0")
    return ((actual - expected) / expected) * Decimal("100")
