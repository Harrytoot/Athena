from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RiskModelSnapshot:
    timestamp: datetime
    var_95: Decimal
    var_99: Decimal
    cvar_95: Decimal
    max_drawdown_pct: Decimal
    beta_exposure: Decimal
    leverage: Decimal
    concentration_hhi: Decimal


@dataclass(frozen=True)
class RiskDriftResult:
    timestamp: datetime
    var_95_drift_pct: Decimal
    var_99_drift_pct: Decimal
    cvar_95_drift_pct: Decimal
    beta_drift_pct: Decimal
    leverage_drift_pct: Decimal
    concentration_drift_pct: Decimal
    overall_drift_score: Decimal
    is_diverged: bool
    divergence_reason: str

    DIVERGENCE_SCORE_THRESHOLD = Decimal("0.25")


@dataclass
class RiskDriftDetector:
    baseline: Optional[RiskModelSnapshot] = None
    drift_threshold_pct: Decimal = Decimal("20")
    var_drift_threshold_pct: Decimal = Decimal("30")

    snapshots: List[RiskModelSnapshot] = field(default_factory=list)
    max_snapshots: int = 200

    def set_baseline(self, snapshot: RiskModelSnapshot) -> None:
        self.baseline = snapshot

    def record_snapshot(
        self,
        var_95: Decimal,
        var_99: Decimal,
        cvar_95: Decimal,
        max_drawdown_pct: Decimal,
        beta_exposure: Decimal,
        leverage: Decimal,
        concentration_hhi: Decimal,
    ) -> RiskModelSnapshot:
        snap = RiskModelSnapshot(
            timestamp=datetime.now(timezone.utc),
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown_pct=max_drawdown_pct,
            beta_exposure=beta_exposure,
            leverage=leverage,
            concentration_hhi=concentration_hhi,
        )
        self.snapshots.append(snap)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
        return snap

    def detect(self, current: RiskModelSnapshot) -> RiskDriftResult:
        reference = self.baseline if self.baseline is not None else (
            self.snapshots[-2] if len(self.snapshots) >= 2 else current
        )

        var_95_drift = _drift_pct(current.var_95, reference.var_95, True)
        var_99_drift = _drift_pct(current.var_99, reference.var_99, True)
        cvar_95_drift = _drift_pct(current.cvar_95, reference.cvar_95, True)
        beta_drift = _drift_pct(current.beta_exposure, reference.beta_exposure)
        leverage_drift = _drift_pct(current.leverage, reference.leverage)
        concentration_drift = _drift_pct(current.concentration_hhi, reference.concentration_hhi)

        var_diverged = abs(var_95_drift) > self.var_drift_threshold_pct or abs(var_99_drift) > self.var_drift_threshold_pct
        beta_diverged = abs(beta_drift) > self.drift_threshold_pct
        leverage_diverged = abs(leverage_drift) > self.drift_threshold_pct
        concentration_diverged = abs(concentration_drift) > self.drift_threshold_pct

        flags = [var_diverged, beta_diverged, leverage_diverged, concentration_diverged]
        overall_score = Decimal(sum(1 for f in flags if f)) / Decimal(len(flags))
        is_diverged = overall_score >= RiskDriftResult.DIVERGENCE_SCORE_THRESHOLD

        reasons = []
        if var_diverged:
            reasons.append(f"VaR_drift(VaR95={round(var_95_drift,1)}%,VaR99={round(var_99_drift,1)}%)")
        if beta_diverged:
            reasons.append(f"beta_drift({round(beta_drift,1)}%)")
        if leverage_diverged:
            reasons.append(f"leverage_drift({round(leverage_drift,1)}%)")
        if concentration_diverged:
            reasons.append(f"concentration_drift({round(concentration_drift,1)}%)")

        return RiskDriftResult(
            timestamp=datetime.now(timezone.utc),
            var_95_drift_pct=var_95_drift,
            var_99_drift_pct=var_99_drift,
            cvar_95_drift_pct=cvar_95_drift,
            beta_drift_pct=beta_drift,
            leverage_drift_pct=leverage_drift,
            concentration_drift_pct=concentration_drift,
            overall_drift_score=overall_score,
            is_diverged=is_diverged,
            divergence_reason="; ".join(reasons) if reasons else "none",
        )

    def clear(self) -> None:
        self.snapshots.clear()
        self.baseline = None


def _drift_pct(current: Decimal, reference: Decimal, invert_sign: bool = False) -> Decimal:
    if reference == Decimal("0"):
        return Decimal("0")
    drift = ((current - reference) / abs(reference)) * Decimal("100")
    return -drift if invert_sign else drift
