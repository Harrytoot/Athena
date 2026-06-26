import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.realism_validation.assumption_audit import AssumptionAuditReport
from app.realism_validation.execution_gap_analyzer import ExecutionGapReport
from app.realism_validation.slippage_reality_check import SlippageRealityReport
from app.realism_validation.liquidity_crisis_simulator import LiquidityCrisisReport

DIMENSION_WEIGHTS = {
    "assumptions": 0.25,
    "execution_gap": 0.25,
    "slippage_reality": 0.20,
    "liquidity_crisis": 0.20,
    "stress_survival": 0.10,
}


@dataclass
class RealismDimensionScore:
    dimension: str
    score: float
    weight: float
    details: str


@dataclass
class RealVsSimReport:
    dimensions: list[RealismDimensionScore] = field(default_factory=list)
    realism_consistency_score: float = 0.0
    execution_gap_ratio: float = 0.0
    slippage_stress_normal_ratio: float = 0.0
    liquidity_breakdown_threshold: float = 0.0
    strategy_survival_probability: float = 0.0
    overall_assessment: str = ""
    critical_findings: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def realism_grade(self) -> str:
        if self.realism_consistency_score >= 0.8:
            return "A"
        if self.realism_consistency_score >= 0.6:
            return "B"
        if self.realism_consistency_score >= 0.4:
            return "C"
        if self.realism_consistency_score >= 0.2:
            return "D"
        return "F"

    @property
    def is_acceptable(self) -> bool:
        return self.realism_consistency_score >= 0.4


class RealVsSimReportGenerator:

    def __init__(self, seed: int | None = None):
        self.seed = seed

    def generate(
        self,
        assumption_audit: AssumptionAuditReport,
        execution_gap: ExecutionGapReport,
        slippage_reality: SlippageRealityReport,
        liquidity_crisis: LiquidityCrisisReport,
    ) -> RealVsSimReport:
        dimensions: list[RealismDimensionScore] = []

        d = self._score_assumptions(assumption_audit)
        dimensions.append(d)

        d = self._score_execution_gap(execution_gap)
        dimensions.append(d)

        d = self._score_slippage_reality(slippage_reality)
        dimensions.append(d)

        d = self._score_liquidity_crisis(liquidity_crisis)
        dimensions.append(d)

        d = self._score_stress_survival(assumption_audit, execution_gap)
        dimensions.append(d)

        weighted_sum = sum(
            dim.score * dim.weight for dim in dimensions
        )
        total_weight = sum(dim.weight for dim in dimensions)
        consistency_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

        execution_gap_ratio: float = execution_gap.overall_gap_ratio
        slippage_ratio: float = slippage_reality.amplification_ratio
        breakdown_threshold: float = liquidity_crisis.breakdown_threshold_pct
        survival_prob: float = liquidity_crisis.survival_probability

        critical_findings = self._collect_critical_findings(
            assumption_audit,
            execution_gap,
            slippage_reality,
            liquidity_crisis,
        )

        assessment = self._overall_assessment(
            consistency_score, critical_findings
        )

        return RealVsSimReport(
            dimensions=dimensions,
            realism_consistency_score=consistency_score,
            execution_gap_ratio=round(execution_gap_ratio, 4),
            slippage_stress_normal_ratio=round(slippage_ratio, 4),
            liquidity_breakdown_threshold=round(breakdown_threshold, 4),
            strategy_survival_probability=round(survival_prob, 4),
            overall_assessment=assessment,
            critical_findings=critical_findings,
        )

    def _score_assumptions(
        self, audit: AssumptionAuditReport
    ) -> RealismDimensionScore:
        score = audit.overall_realism
        details = (
            f"假设审计: {len(audit.assumptions)}项检查, "
            f"{audit.unrealistic_count}项不实, "
            f"总体真实度 {score:.2f}"
        )
        return RealismDimensionScore(
            dimension="系统假设真实性",
            score=score,
            weight=DIMENSION_WEIGHTS["assumptions"],
            details=details,
        )

    def _score_execution_gap(
        self, gap: ExecutionGapReport
    ) -> RealismDimensionScore:
        score = max(0.0, 1.0 - gap.overall_gap_ratio)
        details = (
            f"执行偏差: 总偏差率 {gap.overall_gap_ratio:.2f}, "
            f"{gap.critical_gaps}个严重偏差"
        )
        return RealismDimensionScore(
            dimension="执行偏差分析",
            score=score,
            weight=DIMENSION_WEIGHTS["execution_gap"],
            details=details,
        )

    def _score_slippage_reality(
        self, reality: SlippageRealityReport
    ) -> RealismDimensionScore:
        baseline_ok = 1.0 if reality.baseline.is_realistic else 0.3
        stress_ok = 1.0 if reality.stress.is_realistic else 0.3
        amplification = reality.amplification_ratio

        amp_score = 0.5
        if amplification >= 2.0 and amplification <= 6.0:
            amp_score = 1.0
        elif amplification >= 1.5 or amplification <= 8.0:
            amp_score = 0.7

        score = round((baseline_ok * 0.3 + stress_ok * 0.4 + amp_score * 0.3), 4)

        details = (
            f"滑点: 基准{'真实' if reality.baseline.is_realistic else '不实'}, "
            f"压力{'真实' if reality.stress.is_realistic else '不实'}, "
            f"放大 {amplification:.1f}x"
        )
        return RealismDimensionScore(
            dimension="滑点真实性",
            score=score,
            weight=DIMENSION_WEIGHTS["slippage_reality"],
            details=details,
        )

    def _score_liquidity_crisis(
        self, crisis: LiquidityCrisisReport
    ) -> RealismDimensionScore:
        survival = crisis.survival_probability
        viable_ratio = crisis.viable_stages / max(1, crisis.total_stages)

        score = round((survival * 0.6 + viable_ratio * 0.4), 4)

        details = (
            f"流动性危机: 存活率 {survival:.2f}, "
            f"可交易阶段 {crisis.viable_stages}/{crisis.total_stages}, "
            f"崩潰阈值 {crisis.breakdown_threshold_pct:.0%}"
        )
        return RealismDimensionScore(
            dimension="流动性危机",
            score=score,
            weight=DIMENSION_WEIGHTS["liquidity_crisis"],
            details=details,
        )

    def _score_stress_survival(
        self,
        audit: AssumptionAuditReport,
        gap: ExecutionGapReport,
    ) -> RealismDimensionScore:
        stress_assumptions = [
            a for a in audit.assumptions
            if "压力" in a.name or "stress" in a.name.lower()
        ]

        if stress_assumptions:
            score = sum(a.score for a in stress_assumptions) / len(stress_assumptions)
        else:
            score = 0.5

        score = round(max(0.0, min(1.0, score)), 4)

        details = f"压力生存评估: 综合评分 {score:.2f}"
        return RealismDimensionScore(
            dimension="压力生存能力",
            score=score,
            weight=DIMENSION_WEIGHTS["stress_survival"],
            details=details,
        )

    def _collect_critical_findings(
        self,
        audit: AssumptionAuditReport,
        gap: ExecutionGapReport,
        reality: SlippageRealityReport,
        crisis: LiquidityCrisisReport,
    ) -> list[str]:
        findings: list[str] = []

        if audit.critical_issues:
            findings.append(f"假设层严重问题 ({len(audit.critical_issues)}项): {'; '.join(audit.critical_issues[:3])}")

        if gap.critical_gaps > 0:
            criticals = [g for g in gap.gaps if g.severity in ("high", "critical")]
            for g in criticals[:3]:
                findings.append(f"执行偏差: [{g.category}] {g.description}")

        if not reality.baseline.is_realistic:
            findings.append(f"滑点基准不实: {reality.baseline.details}")

        if not reality.stress.is_realistic:
            findings.append(f"压力滑点不实: {reality.stress.details}")

        if crisis.survival_probability < 0.4:
            findings.append(
                f"流动性脆弱: 存活率 {crisis.survival_probability:.0%}, "
                f"崩潰阈值 {crisis.breakdown_threshold_pct:.0%}"
            )

        return findings

    def _overall_assessment(
        self, score: float, findings: list[str]
    ) -> str:
        parts: list[str] = []

        if score >= 0.8:
            parts.append("仿真一致性: 优秀")
        elif score >= 0.6:
            parts.append("仿真一致性: 良好")
        elif score >= 0.4:
            parts.append("仿真一致性: 一般")
        else:
            parts.append("仿真一致性: 较差")

        parts.append(f"综合评分: {score:.2f}")

        if findings:
            parts.append(f"关键发现: {len(findings)}条")
        else:
            parts.append("无严重问题")

        return " | ".join(parts)
