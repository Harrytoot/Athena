from dataclasses import dataclass, field

from app.strategy.position_sizer import StrategyPosition


@dataclass
class RiskConstraints:
    max_single_exposure: float = 1.0
    max_total_exposure: float = 2.0
    min_cash_buffer: float = 0.0
    max_turnover: float = 1.0


@dataclass
class RiskAdjustedPosition:
    original: StrategyPosition
    adjusted_position_pct: float
    capped_by_exposure: bool = False
    capped_by_turnover: bool = False
    adjustment_reason: str = ""


@dataclass
class RiskResult:
    positions: list[RiskAdjustedPosition] = field(default_factory=list)

    @property
    def total_exposure(self) -> float:
        return sum(abs(p.adjusted_position_pct) for p in self.positions)

    @property
    def avg_turnover(self) -> float:
        n = len(self.positions)
        if n < 2:
            return 0.0
        turnovers = []
        for i in range(1, n):
            t = abs(self.positions[i].adjusted_position_pct - self.positions[i - 1].adjusted_position_pct)
            turnovers.append(t)
        return sum(turnovers) / len(turnovers) if turnovers else 0.0


class RiskManager:

    def __init__(self, constraints: RiskConstraints | None = None):
        self.constraints = constraints or RiskConstraints()

    def apply(self, positions: list[StrategyPosition]) -> RiskResult:
        if not positions:
            return RiskResult()

        adjusted: list[RiskAdjustedPosition] = []

        for pos in positions:
            rap = self._apply_single_constraints(pos, previous=adjusted[-1] if adjusted else None)
            adjusted.append(rap)

        return RiskResult(positions=adjusted)

    def apply_with_nav(
        self,
        positions: list[StrategyPosition],
        nav_series: list[float],
    ) -> RiskResult:
        return self.apply(positions)

    def _apply_single_constraints(
        self,
        pos: StrategyPosition,
        previous: RiskAdjustedPosition | None = None,
    ) -> RiskAdjustedPosition:
        c = self.constraints
        pct = pos.position_pct
        reasons: list[str] = []
        capped_exposure = False
        capped_turnover = False

        allowed_by_single = c.max_single_exposure
        allowed_by_total = c.max_total_exposure
        effective_limit = min(allowed_by_single, allowed_by_total)

        if abs(pct) > effective_limit:
            pct = effective_limit if pct > 0 else -effective_limit
            capped_exposure = True
            if effective_limit == allowed_by_single:
                reasons.append("single_exposure")
            if effective_limit == allowed_by_total:
                reasons.append("total_exposure")

        if previous is not None and c.max_turnover < 1.0:
            prev_pct = previous.adjusted_position_pct
            desired_turnover = abs(pct - prev_pct)
            if desired_turnover > c.max_turnover:
                direction = 1 if pct > prev_pct else -1
                pct = prev_pct + direction * c.max_turnover
                pct = round(pct, 6)
                capped_turnover = True
                reasons.append("turnover")

        if c.min_cash_buffer > 0:
            max_allowed = 1.0 - c.min_cash_buffer
            if abs(pct) > max_allowed:
                pct = max_allowed if pct > 0 else -max_allowed
                capped_exposure = True
                reasons.append("cash_buffer")

        pct = round(pct, 6)

        return RiskAdjustedPosition(
            original=pos,
            adjusted_position_pct=pct,
            capped_by_exposure=capped_exposure,
            capped_by_turnover=capped_turnover,
            adjustment_reason=",".join(reasons) if reasons else "",
        )
