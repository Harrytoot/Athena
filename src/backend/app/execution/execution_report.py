from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ExecutionQuality:
    fill_rate: float = 0.0
    partial_fill_ratio: float = 0.0
    avg_slippage_bps: float = 0.0
    max_slippage_bps: float = 0.0
    total_slippage_cost: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    price_improvement_count: int = 0
    liquidity_score: float = 0.0
    overall_quality_score: float = 0.0

    @property
    def quality_grade(self) -> str:
        if self.overall_quality_score >= 0.8:
            return "A"
        if self.overall_quality_score >= 0.6:
            return "B"
        if self.overall_quality_score >= 0.4:
            return "C"
        if self.overall_quality_score >= 0.2:
            return "D"
        return "F"

    @property
    def is_acceptable(self) -> bool:
        return self.overall_quality_score >= 0.4


@dataclass
class ExecutionReport:
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_orders: int = 0
    filled_orders: int = 0
    partially_filled: int = 0
    unfilled_orders: int = 0
    total_requested_notional: float = 0.0
    total_executed_notional: float = 0.0
    fill_rate: float = 0.0
    quality: ExecutionQuality = field(default_factory=ExecutionQuality)
    warnings: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def execution_efficiency(self) -> float:
        if self.total_requested_notional <= 0:
            return 0.0
        return round(self.total_executed_notional / self.total_requested_notional, 6)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ExecutionReportGenerator:

    def generate(
        self,
        total_orders: int,
        filled_count: int,
        partial_count: int,
        requested_notional: float,
        executed_notional: float,
        slippage_estimates: list,
        schedule_result: any = None,
        liquidity_profiles: list | None = None,
    ) -> ExecutionReport:
        unfilled = total_orders - filled_count - partial_count
        fill_rate = filled_count / total_orders if total_orders > 0 else 0.0

        total_slippage = sum(s.slippage_amount for s in slippage_estimates)
        slippage_bps_list = [s.slippage_bps for s in slippage_estimates if s.slippage_bps > 0]
        avg_slippage = sum(slippage_bps_list) / len(slippage_bps_list) if slippage_bps_list else 0.0
        max_slippage = max(slippage_bps_list) if slippage_bps_list else 0.0

        partial_ratio = partial_count / total_orders if total_orders > 0 else 0.0

        avg_latency = 0.0
        max_latency = 0.0
        if schedule_result and hasattr(schedule_result, 'avg_latency_ms'):
            avg_latency = schedule_result.avg_latency_ms
        if schedule_result and hasattr(schedule_result, 'max_latency_ms'):
            max_latency = schedule_result.max_latency_ms

        liquidity_score = 0.5
        if liquidity_profiles:
            liquid_count = sum(1 for lp in liquidity_profiles if lp.is_liquid)
            liquidity_score = liquid_count / len(liquidity_profiles)

        overall = (
            fill_rate * 0.30
            + (1.0 - min(max_slippage / 100.0, 1.0)) * 0.25
            + (1.0 - partial_ratio) * 0.15
            + (1.0 - min(avg_latency / 500.0, 1.0)) * 0.10
            + liquidity_score * 0.20
        )
        overall = round(max(0.0, min(1.0, overall)), 4)

        warnings: list[str] = []
        if fill_rate < 0.7:
            warnings.append(f"Low fill rate: {fill_rate:.1%}")
        if max_slippage > 50:
            warnings.append(f"High max slippage: {max_slippage:.1f} bps")
        if avg_latency > 200:
            warnings.append(f"High average latency: {avg_latency:.0f}ms")
        if partial_ratio > 0.3:
            warnings.append(f"High partial fill ratio: {partial_ratio:.1%}")
        if liquidity_score < 0.5:
            warnings.append(f"Low liquidity score: {liquidity_score:.2f}")

        quality = ExecutionQuality(
            fill_rate=round(fill_rate, 4),
            partial_fill_ratio=round(partial_ratio, 4),
            avg_slippage_bps=round(avg_slippage, 2),
            max_slippage_bps=round(max_slippage, 2),
            total_slippage_cost=round(total_slippage, 2),
            avg_latency_ms=round(avg_latency, 2),
            max_latency_ms=round(max_latency, 2),
            liquidity_score=round(liquidity_score, 4),
            overall_quality_score=overall,
        )

        grade = quality.quality_grade
        summary = f"Execution Quality: {grade} | Fill: {fill_rate:.1%} | Avg Slippage: {avg_slippage:.1f}bps | Latency: {avg_latency:.0f}ms"

        return ExecutionReport(
            total_orders=total_orders,
            filled_orders=filled_count,
            partially_filled=partial_count,
            unfilled_orders=unfilled,
            total_requested_notional=round(requested_notional, 2),
            total_executed_notional=round(executed_notional, 2),
            fill_rate=round(fill_rate, 4),
            quality=quality,
            warnings=warnings,
            summary=summary,
        )
