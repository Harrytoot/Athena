from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class PnLDataPoint:
    timestamp: datetime
    strategy_id: str
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    benchmark_pnl: Decimal = Decimal("0")


@dataclass(frozen=True)
class PnLDriftResult:
    strategy_id: str
    timestamp: datetime
    rolling_mean_pnl: Decimal
    rolling_std_pnl: Decimal
    latest_pnl: Decimal
    z_score: Decimal
    drawdown_pct: Decimal
    max_drawdown_pct: Decimal
    sharpe_estimate: Decimal
    is_degraded: bool
    degradation_reason: str

    Z_DEGRADE_THRESHOLD = Decimal("2.0")
    DRAWDOWN_DEGRADE_THRESHOLD = Decimal("15")


@dataclass
class PnLDriftAnalyzer:
    window_size: int = 50
    z_score_threshold: Decimal = Decimal("2.0")
    drawdown_threshold_pct: Decimal = Decimal("15")
    sharpe_warn_threshold: Decimal = Decimal("0.5")

    history: List[PnLDataPoint] = field(default_factory=list)

    def record_pnl(
        self,
        strategy_id: str,
        realized_pnl: Decimal,
        unrealized_pnl: Decimal,
        benchmark_pnl: Decimal = Decimal("0"),
    ) -> PnLDataPoint:
        point = PnLDataPoint(
            timestamp=datetime.now(timezone.utc),
            strategy_id=strategy_id,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=realized_pnl + unrealized_pnl,
            benchmark_pnl=benchmark_pnl,
        )
        self.history.append(point)
        if len(self.history) > self.window_size * 4:
            self.history = self.history[-self.window_size * 2:]
        return point

    def analyze(self, strategy_id: str) -> PnLDriftResult:
        strategy_points = [p for p in self.history if p.strategy_id == strategy_id]
        if len(strategy_points) < 5:
            return PnLDriftResult(
                strategy_id=strategy_id,
                timestamp=datetime.now(timezone.utc),
                rolling_mean_pnl=Decimal("0"),
                rolling_std_pnl=Decimal("0"),
                latest_pnl=Decimal("0"),
                z_score=Decimal("0"),
                drawdown_pct=Decimal("0"),
                max_drawdown_pct=Decimal("0"),
                sharpe_estimate=Decimal("0"),
                is_degraded=False,
                degradation_reason="insufficient_data",
            )

        window = strategy_points[-min(self.window_size, len(strategy_points)):]
        pnl_values = [p.total_pnl for p in window]
        latest_pnl = pnl_values[-1]

        mean_pnl = sum(pnl_values, Decimal("0")) / Decimal(len(pnl_values))
        var = sum(((v - mean_pnl) ** 2 for v in pnl_values), Decimal("0")) / Decimal(len(pnl_values))
        std_pnl = var.sqrt() if var > Decimal("0") else Decimal("1")

        z_score = (latest_pnl - mean_pnl) / std_pnl if std_pnl > Decimal("0") else Decimal("0")

        peak = pnl_values[0]
        max_dd = Decimal("0")
        for v in pnl_values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak * Decimal("100") if peak > Decimal("0") else Decimal("0")
            if dd > max_dd:
                max_dd = dd

        current_peak = max(pnl_values)
        current_dd = (
            (current_peak - latest_pnl) / current_peak * Decimal("100")
            if current_peak > Decimal("0")
            else Decimal("0")
        )

        sharpe = Decimal("0")
        if std_pnl > Decimal("0"):
            sharpe = mean_pnl / std_pnl

        degradation_reasons = []
        if abs(z_score) > self.z_score_threshold:
            direction = "drop" if z_score < 0 else "spike"
            degradation_reasons.append(f"z_score_{direction}({round(z_score, 2)})")
        if current_dd > self.drawdown_threshold_pct:
            degradation_reasons.append(f"drawdown({round(current_dd, 1)}%)")
        if sharpe < self.sharpe_warn_threshold and mean_pnl < Decimal("0"):
            degradation_reasons.append(f"negative_sharpe({round(sharpe, 2)})")

        is_degraded = len(degradation_reasons) > 0

        return PnLDriftResult(
            strategy_id=strategy_id,
            timestamp=datetime.now(timezone.utc),
            rolling_mean_pnl=mean_pnl,
            rolling_std_pnl=std_pnl,
            latest_pnl=latest_pnl,
            z_score=z_score,
            drawdown_pct=current_dd,
            max_drawdown_pct=max_dd,
            sharpe_estimate=sharpe,
            is_degraded=is_degraded,
            degradation_reason="; ".join(degradation_reasons) if degradation_reasons else "none",
        )

    def clear(self) -> None:
        self.history.clear()
