from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AlertRule(ABC):
    name: str
    severity: str
    cooldown_seconds: int = 60
    last_fired: Optional[datetime] = None

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        ...

    def _in_cooldown(self) -> bool:
        if self.last_fired is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.last_fired).total_seconds()
        return elapsed < self.cooldown_seconds


@dataclass
class LatencySpikeRule(AlertRule):
    threshold_ms: Decimal = Decimal("500")
    severity: str = "WARN"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        current_ms = context.get("latency_ms", Decimal("0"))
        if isinstance(current_ms, (int, float)):
            current_ms = Decimal(str(current_ms))
        if current_ms > self.threshold_ms:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            return True, f"Latency spike: {current_ms}ms exceeds threshold {self.threshold_ms}ms"
        return False, ""


@dataclass
class ExecutionDriftRule(AlertRule):
    max_drift_rate: Decimal = Decimal("0.3")
    severity: str = "WARN"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        drift_rate = context.get("drift_rate", Decimal("0"))
        if isinstance(drift_rate, (int, float)):
            drift_rate = Decimal(str(drift_rate))
        if drift_rate > self.max_drift_rate:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            return True, f"Execution drift rate {drift_rate} exceeds threshold {self.max_drift_rate}"
        return False, ""


@dataclass
class PnLDegradationRule(AlertRule):
    drawdown_threshold_pct: Decimal = Decimal("15")
    severity: str = "CRITICAL"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        drawdown = context.get("drawdown_pct", Decimal("0"))
        if isinstance(drawdown, (int, float)):
            drawdown = Decimal(str(drawdown))
        if drawdown > self.drawdown_threshold_pct:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            return True, f"PnL drawdown {drawdown}% exceeds threshold {self.drawdown_threshold_pct}%"
        return False, ""


@dataclass
class RiskModelDivergenceRule(AlertRule):
    max_divergence_score: Decimal = Decimal("0.5")
    severity: str = "WARN"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        score = context.get("divergence_score", Decimal("0"))
        if isinstance(score, (int, float)):
            score = Decimal(str(score))
        if score >= self.max_divergence_score:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            reason = context.get("divergence_reason", "unknown")
            return True, f"Risk model divergence score {score} >= {self.max_divergence_score}: {reason}"
        return False, ""


@dataclass
class HealthCheckFailureRule(AlertRule):
    max_consecutive_failures: int = 3
    severity: str = "CRITICAL"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        failures = context.get("consecutive_failures", 0)
        component = context.get("component", "unknown")
        if failures >= self.max_consecutive_failures:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            return True, f"Component {component}: {failures} consecutive health check failures"
        return False, ""


@dataclass
class FillRateDropRule(AlertRule):
    min_fill_rate_pct: Decimal = Decimal("80")
    severity: str = "WARN"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        fill_rate = context.get("fill_rate_pct", Decimal("100"))
        if isinstance(fill_rate, (int, float)):
            fill_rate = Decimal(str(fill_rate))
        if fill_rate < self.min_fill_rate_pct:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            return True, f"Fill rate {fill_rate}% below threshold {self.min_fill_rate_pct}%"
        return False, ""


@dataclass
class ExposureLimitRule(AlertRule):
    max_exposure_ratio: Decimal = Decimal("0.95")
    severity: str = "CRITICAL"

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        ratio = context.get("exposure_ratio", Decimal("0"))
        if isinstance(ratio, (int, float)):
            ratio = Decimal(str(ratio))
        if ratio > self.max_exposure_ratio:
            if self._in_cooldown():
                return False, ""
            self.last_fired = datetime.now(timezone.utc)
            return True, f"Exposure ratio {ratio} exceeds limit {self.max_exposure_ratio}"
        return False, ""


DEFAULT_RULES: List[AlertRule] = [
    LatencySpikeRule(name="latency_spike"),
    ExecutionDriftRule(name="execution_drift"),
    PnLDegradationRule(name="pnl_degradation"),
    RiskModelDivergenceRule(name="risk_model_divergence"),
    HealthCheckFailureRule(name="health_check_failure"),
    FillRateDropRule(name="fill_rate_drop"),
    ExposureLimitRule(name="exposure_limit"),
]
