from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import uuid


@dataclass(frozen=True)
class ComplianceCheck:
    id: str
    rule_name: str
    description: str
    passed: bool
    details: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        rule_name: str,
        description: str,
        passed: bool,
        details: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> "ComplianceCheck":
        return cls(
            id=str(uuid.uuid4()),
            rule_name=rule_name,
            description=description,
            passed=passed,
            details=details,
            timestamp=datetime.now(timezone.utc),
            context=context or {},
        )


@dataclass(frozen=True)
class ComplianceReport:
    timestamp: datetime
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: List[ComplianceCheck]
    compliance_score_pct: Decimal

    def is_compliant(self) -> bool:
        return len(self.failed_checks_list()) == 0

    def failed_checks_list(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if not c.passed]


@dataclass
class ComplianceAudit:
    checks: List[ComplianceCheck] = field(default_factory=list)
    max_checks: int = 5000

    thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "max_position_pct": Decimal("25"),
        "max_leverage": Decimal("3"),
        "max_daily_trades": 500,
        "min_account_balance": Decimal("10000"),
        "max_drawdown_pct": Decimal("30"),
    })

    def record_check(
        self,
        rule_name: str,
        description: str,
        passed: bool,
        details: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ComplianceCheck:
        check = ComplianceCheck.create(rule_name, description, passed, details, context)
        self.checks.append(check)
        if len(self.checks) > self.max_checks:
            self.checks = self.checks[-self.max_checks:]
        return check

    def check_position_limit(self, symbol: str, position_pct: Decimal) -> ComplianceCheck:
        limit = Decimal(str(self.thresholds.get("max_position_pct", "25")))
        passed = position_pct <= limit
        return self.record_check(
            rule_name="position_limit",
            description=f"Position limit check for {symbol}",
            passed=passed,
            details=f"{symbol}: {position_pct}% vs limit {limit}%",
            context={"symbol": symbol, "position_pct": str(position_pct), "limit": str(limit)},
        )

    def check_leverage(self, current_leverage: Decimal) -> ComplianceCheck:
        limit = Decimal(str(self.thresholds.get("max_leverage", "3")))
        passed = current_leverage <= limit
        return self.record_check(
            rule_name="leverage_limit",
            description="Leverage limit check",
            passed=passed,
            details=f"Leverage {current_leverage} vs limit {limit}",
            context={"current_leverage": str(current_leverage), "limit": str(limit)},
        )

    def check_daily_trades(self, trade_count: int) -> ComplianceCheck:
        limit = int(self.thresholds.get("max_daily_trades", "500"))
        passed = trade_count <= limit
        return self.record_check(
            rule_name="daily_trade_limit",
            description="Daily trade count check",
            passed=passed,
            details=f"Trades {trade_count} vs limit {limit}",
            context={"trade_count": trade_count, "limit": limit},
        )

    def check_drawdown(self, current_drawdown_pct: Decimal) -> ComplianceCheck:
        limit = Decimal(str(self.thresholds.get("max_drawdown_pct", "30")))
        passed = current_drawdown_pct <= limit
        return self.record_check(
            rule_name="drawdown_limit",
            description="Maximum drawdown check",
            passed=passed,
            details=f"Drawdown {current_drawdown_pct}% vs limit {limit}%",
            context={"drawdown_pct": str(current_drawdown_pct), "limit": str(limit)},
        )

    def generate_report(self, lookback: int = 100) -> ComplianceReport:
        recent = self.checks[-lookback:] if len(self.checks) > lookback else self.checks
        total = len(recent) or 1
        passed = sum(1 for c in recent if c.passed)
        failed = total - passed
        score = Decimal(passed) / Decimal(total) * Decimal("100")

        return ComplianceReport(
            timestamp=datetime.now(timezone.utc),
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            checks=list(recent),
            compliance_score_pct=score,
        )

    def clear(self) -> None:
        self.checks.clear()
