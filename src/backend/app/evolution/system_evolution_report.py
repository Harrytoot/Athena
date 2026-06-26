from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.evolution.feature_drift_detector import (
    FeatureDriftDetector,
    FeatureDriftReport,
)
from app.evolution.strategy_decay_analyzer import (
    StrategyDecayAnalyzer,
    StrategyDecayReport,
)
from app.evolution.portfolio_topology import (
    PortfolioTopologyAnalyzer,
    PortfolioTopologyReport,
)
from app.evolution.strategy_lifecycle_manager import (
    LifecycleReport,
    StrategyLifecycleManager,
)
from app.execution.execution_report import ExecutionReport
from app.feature_store.repository import FeatureItem
from app.fund_evaluation.fund_report import FundEvaluationReport
from app.portfolio.portfolio_engine import StrategyInput
from app.realism_validation.real_vs_sim_report import RealVsSimReport


@dataclass
class EvolutionRecommendation:
    category: str
    priority: str
    action: str
    rationale: str
    expected_impact: str

    @property
    def priority_order(self) -> int:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return order.get(self.priority, 99)


@dataclass
class SystemEvolutionReport:
    feature_drift: FeatureDriftReport = field(default_factory=FeatureDriftReport)
    strategy_decay: StrategyDecayReport = field(default_factory=StrategyDecayReport)
    topology: PortfolioTopologyReport = field(default_factory=PortfolioTopologyReport)
    lifecycle: LifecycleReport = field(default_factory=LifecycleReport)
    evolution_score: float = 0.0
    recommendations: list[EvolutionRecommendation] = field(default_factory=list)
    overall_assessment: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def evolution_grade(self) -> str:
        if self.evolution_score >= 0.8:
            return "A"
        if self.evolution_score >= 0.6:
            return "B"
        if self.evolution_score >= 0.4:
            return "C"
        if self.evolution_score >= 0.2:
            return "D"
        return "F"

    @property
    def critical_recommendations(self) -> list[EvolutionRecommendation]:
        return [r for r in self.recommendations if r.priority == "critical"]

    @property
    def high_priority_recommendations(self) -> list[EvolutionRecommendation]:
        return [r for r in self.recommendations if r.priority in ("critical", "high")]


class SystemEvolutionReportGenerator:

    def __init__(
        self,
        drift_window_ratio: float = 0.4,
        drift_threshold: float = 0.5,
        decay_window_size: int = 30,
        decay_threshold: float = 0.5,
        corr_threshold_high: float = 0.7,
        lifecycle_maturity_sharpe: float = 0.5,
        lifecycle_terminal_decay: float = 0.7,
    ):
        self.drift_detector = FeatureDriftDetector(
            window_ratio=drift_window_ratio,
            drift_threshold=drift_threshold,
        )
        self.decay_analyzer = StrategyDecayAnalyzer(
            window_size=decay_window_size,
            decay_threshold=decay_threshold,
        )
        self.topology_analyzer = PortfolioTopologyAnalyzer(
            correlation_threshold_high=corr_threshold_high,
        )
        self.lifecycle_manager = StrategyLifecycleManager(
            maturity_min_sharpe=lifecycle_maturity_sharpe,
            terminal_decay_threshold=lifecycle_terminal_decay,
        )

    def generate(
        self,
        feature_history: list[FeatureItem],
        strategies: list[StrategyInput],
        fund_report: FundEvaluationReport | None = None,
        execution_reports: list[ExecutionReport] | None = None,
        realism_reports: list[RealVsSimReport] | None = None,
        correlation_matrix: dict[str, dict[str, float]] | None = None,
    ) -> SystemEvolutionReport:
        drift_report = self.drift_detector.detect(feature_history)

        decay_report = self.decay_analyzer.analyze(strategies)

        weights = self._extract_weights(fund_report, strategies)
        topology_report = self.topology_analyzer.analyze(
            strategies, weights, correlation_matrix
        )

        lifecycle_report = self.lifecycle_manager.classify(
            strategies, decay_report
        )

        recommendations = self._generate_recommendations(
            drift_report,
            decay_report,
            topology_report,
            lifecycle_report,
            fund_report,
            execution_reports,
            realism_reports,
        )

        evolution_score = self._compute_evolution_score(
            drift_report,
            decay_report,
            topology_report,
            lifecycle_report,
            fund_report,
            execution_reports,
            realism_reports,
        )

        assessment = self._overall_assessment(
            evolution_score,
            drift_report,
            decay_report,
            topology_report,
            lifecycle_report,
        )

        return SystemEvolutionReport(
            feature_drift=drift_report,
            strategy_decay=decay_report,
            topology=topology_report,
            lifecycle=lifecycle_report,
            evolution_score=round(evolution_score, 4),
            recommendations=recommendations,
            overall_assessment=assessment,
        )

    def _extract_weights(
        self,
        fund_report: FundEvaluationReport | None,
        strategies: list[StrategyInput],
    ) -> list[float] | None:
        if not fund_report or not strategies:
            return None
        return [1.0 / len(strategies)] * len(strategies) if strategies else None

    def _generate_recommendations(
        self,
        drift: FeatureDriftReport,
        decay: StrategyDecayReport,
        topology: PortfolioTopologyReport,
        lifecycle: LifecycleReport,
        fund_report: FundEvaluationReport | None,
        execution_reports: list[ExecutionReport] | None,
        realism_reports: list[RealVsSimReport] | None,
    ) -> list[EvolutionRecommendation]:
        recommendations: list[EvolutionRecommendation] = []

        recommendations.extend(self._feature_recommendations(drift))
        recommendations.extend(self._strategy_recommendations(decay, lifecycle))
        recommendations.extend(self._topology_recommendations(topology))
        recommendations.extend(self._fund_recommendations(fund_report))
        recommendations.extend(self._execution_recommendations(execution_reports))
        recommendations.extend(self._realism_recommendations(realism_reports))

        recommendations.sort(key=lambda r: r.priority_order)
        return recommendations

    def _feature_recommendations(
        self, drift: FeatureDriftReport
    ) -> list[EvolutionRecommendation]:
        recommendations: list[EvolutionRecommendation] = []

        for feature_name in drift.critical_decay_features:
            point = next(
                (p for p in drift.drift_points if p.feature_name == feature_name), None
            )
            detail = ""
            if point:
                detail = f" (漂移评分: {point.drift_score:.2f}, 均值偏移: {point.mean_shift:.2f})"
            recommendations.append(
                EvolutionRecommendation(
                    category="feature",
                    priority="critical",
                    action=f"重新评估特征 {feature_name} 的有效性{detail}",
                    rationale=f"特征 {feature_name} 发生严重漂移，可能已失去预测能力",
                    expected_impact="恢复特征预测能力，避免基于失效特征的错误决策",
                )
            )

        for feature_name in drift.most_drifted_features:
            if feature_name in drift.critical_decay_features:
                continue
            recommendations.append(
                EvolutionRecommendation(
                    category="feature",
                    priority="high",
                    action=f"监控特征 {feature_name} 的漂移趋势",
                    rationale=f"特征 {feature_name} 出现显著漂移，需持续观察",
                    expected_impact="提前发现特征失效风险",
                )
            )

        if not drift.most_drifted_features and not drift.critical_decay_features:
            recommendations.append(
                EvolutionRecommendation(
                    category="feature",
                    priority="low",
                    action="特征状态良好，保持当前监控频率",
                    rationale="所有特征均处于稳定状态",
                    expected_impact="维持现有特征工程质量",
                )
            )

        return recommendations

    def _strategy_recommendations(
        self,
        decay: StrategyDecayReport,
        lifecycle: LifecycleReport,
    ) -> list[EvolutionRecommendation]:
        recommendations: list[EvolutionRecommendation] = []

        for signal in decay.decay_signals:
            if signal.decay_score >= 0.7:
                recommendations.append(
                    EvolutionRecommendation(
                        category="strategy",
                        priority="critical",
                        action=f"立即审查策略 {signal.strategy_id}",
                        rationale=f"策略 {signal.strategy_id} 衰减评分达到 {signal.decay_score:.2f}",
                        expected_impact="避免继续使用严重衰减策略造成损失",
                    )
                )
            elif signal.decay_score >= 0.5:
                recommendations.append(
                    EvolutionRecommendation(
                        category="strategy",
                        priority="high",
                        action=f"准备策略 {signal.strategy_id} 的降权或替换方案",
                        rationale=f"策略 {signal.strategy_id} 出现显著衰减 (评分: {signal.decay_score:.2f})",
                        expected_impact="减少衰减策略对组合的负面影响",
                    )
                )

        terminal_strategies = [
            c for c in lifecycle.classifications if c.stage == "terminal"
        ]
        for cls in terminal_strategies:
            recommendations.append(
                EvolutionRecommendation(
                    category="strategy",
                    priority="critical",
                    action=f"终止策略 {cls.strategy_id} 并替换",
                    rationale=f"策略 {cls.strategy_id} 已进入终止期",
                    expected_impact="移除无效策略，释放资本用于有效策略",
                )
            )

        decaying_strategies = [
            c for c in lifecycle.classifications if c.stage == "decaying"
        ]
        for cls in decaying_strategies:
            recommendations.append(
                EvolutionRecommendation(
                    category="strategy",
                    priority="high",
                    action=f"逐步降低策略 {cls.strategy_id} 的权重",
                    rationale=f"策略 {cls.strategy_id} 处于衰退期，预计剩余寿命 {cls.expected_remaining_life_days:.0f}天",
                    expected_impact="有序退出衰退策略，平滑组合过渡",
                )
            )

        if lifecycle.early_count > 0:
            recommendations.append(
                EvolutionRecommendation(
                    category="strategy",
                    priority="low",
                    action=f"监控 {lifecycle.early_count} 个早期策略的发展",
                    rationale="早期策略需要更多数据验证其有效性",
                    expected_impact="培育潜在的核心策略",
                )
            )

        return recommendations

    def _topology_recommendations(
        self, topology: PortfolioTopologyReport
    ) -> list[EvolutionRecommendation]:
        recommendations: list[EvolutionRecommendation] = []

        if topology.metrics.structural_efficiency < 0.3:
            recommendations.append(
                EvolutionRecommendation(
                    category="portfolio",
                    priority="critical",
                    action="重构投资组合结构",
                    rationale=f"组合结构效率极低 ({topology.metrics.structural_efficiency:.2f})",
                    expected_impact="大幅提升组合风险收益特征",
                )
            )

        if topology.metrics.fragility_score > 0.7:
            recommendations.append(
                EvolutionRecommendation(
                    category="portfolio",
                    priority="critical",
                    action="降低组合脆弱性，增加防御性配置",
                    rationale=f"组合脆弱性过高 ({topology.metrics.fragility_score:.2f})",
                    expected_impact="提高组合抗风险能力",
                )
            )

        if topology.metrics.redundancy_score > 0.5:
            recommendations.append(
                EvolutionRecommendation(
                    category="portfolio",
                    priority="high",
                    action="精简高度相关的冗余策略",
                    rationale=f"策略冗余度 {topology.metrics.redundancy_score:.2f}",
                    expected_impact="降低管理复杂度，提升资本效率",
                )
            )

        for suggestion in topology.improvement_suggestions:
            recommendations.append(
                EvolutionRecommendation(
                    category="portfolio",
                    priority="medium",
                    action=suggestion,
                    rationale="基于组合拓扑分析的结构优化建议",
                    expected_impact="改善组合结构效率",
                )
            )

        return recommendations

    def _fund_recommendations(
        self, fund_report: FundEvaluationReport | None
    ) -> list[EvolutionRecommendation]:
        if not fund_report:
            return []

        recommendations: list[EvolutionRecommendation] = []

        if fund_report.overall_score < 0.4:
            recommendations.append(
                EvolutionRecommendation(
                    category="portfolio",
                    priority="high",
                    action=f"全面审查基金配置 (当前评分: {fund_report.overall_score:.2f})",
                    rationale="基金综合评分过低",
                    expected_impact="提升基金整体表现",
                )
            )

        for flag in fund_report.risk_flags:
            recommendations.append(
                EvolutionRecommendation(
                    category="portfolio",
                    priority="medium",
                    action=f"处理风险警示: {flag}",
                    rationale="基金风险评估发现问题",
                    expected_impact="降低基金风险敞口",
                )
            )

        return recommendations

    def _execution_recommendations(
        self, execution_reports: list[ExecutionReport] | None
    ) -> list[EvolutionRecommendation]:
        if not execution_reports:
            return []

        recommendations: list[EvolutionRecommendation] = []

        recent = execution_reports[-1] if execution_reports else None
        if not recent:
            return []

        if recent.fill_rate < 0.7:
            recommendations.append(
                EvolutionRecommendation(
                    category="execution",
                    priority="high",
                    action=f"优化执行策略以提升成交率 (当前: {recent.fill_rate:.1%})",
                    rationale="成交率过低影响策略实现效果",
                    expected_impact="提升策略执行的保真度",
                )
            )

        if recent.quality.avg_slippage_bps > 30:
            recommendations.append(
                EvolutionRecommendation(
                    category="execution",
                    priority="high",
                    action=f"降低交易滑点 (当前均值: {recent.quality.avg_slippage_bps:.0f}bps)",
                    rationale="交易滑点侵蚀策略收益",
                    expected_impact="减少交易成本，提升净收益",
                )
            )

        for warning in recent.warnings:
            recommendations.append(
                EvolutionRecommendation(
                    category="execution",
                    priority="medium",
                    action=f"处理执行警告: {warning}",
                    rationale="执行质量监控发现问题",
                    expected_impact="提升执行质量和可靠性",
                )
            )

        return recommendations

    def _realism_recommendations(
        self, realism_reports: list[RealVsSimReport] | None
    ) -> list[EvolutionRecommendation]:
        if not realism_reports:
            return []

        recommendations: list[EvolutionRecommendation] = []

        recent = realism_reports[-1] if realism_reports else None
        if not recent:
            return []

        if recent.realism_consistency_score < 0.4:
            recommendations.append(
                EvolutionRecommendation(
                    category="realism",
                    priority="high",
                    action=f"修复仿真与现实偏差 (一致性评分: {recent.realism_consistency_score:.2f})",
                    rationale="仿真模型与现实存在较大偏差",
                    expected_impact="提升策略回测和仿真的可信度",
                )
            )

        for finding in recent.critical_findings:
            recommendations.append(
                EvolutionRecommendation(
                    category="realism",
                    priority="high",
                    action=f"解决关键仿真问题: {finding}",
                    rationale="关键仿真缺陷影响策略评估准确性",
                    expected_impact="提高策略验证的可靠性",
                )
            )

        return recommendations

    def _compute_evolution_score(
        self,
        drift: FeatureDriftReport,
        decay: StrategyDecayReport,
        topology: PortfolioTopologyReport,
        lifecycle: LifecycleReport,
        fund_report: FundEvaluationReport | None,
        execution_reports: list[ExecutionReport] | None,
        realism_reports: list[RealVsSimReport] | None,
    ) -> float:
        scores: list[float] = []

        drift_component = (1.0 - drift.overall_drift_score) * 0.20
        scores.append(max(0.0, drift_component))

        decay_component = (1.0 - decay.overall_decay_score) * 0.25
        scores.append(max(0.0, decay_component))

        topology_component = topology.metrics.structural_efficiency * 0.20
        scores.append(topology_component)

        lifecycle_component = (1.0 - lifecycle.renewal_urgency) * 0.15
        scores.append(max(0.0, lifecycle_component))

        fund_component = 0.10
        if fund_report:
            fund_component = fund_report.overall_score * 0.10
        scores.append(fund_component)

        execution_component = 0.05
        if execution_reports:
            recent = execution_reports[-1]
            execution_component = recent.quality.overall_quality_score * 0.05
        scores.append(max(0.0, execution_component))

        realism_component = 0.05
        if realism_reports:
            recent = realism_reports[-1]
            realism_component = recent.realism_consistency_score * 0.05
        scores.append(max(0.0, realism_component))

        total = sum(scores)
        return min(1.0, max(0.0, total))

    def _overall_assessment(
        self,
        evolution_score: float,
        drift: FeatureDriftReport,
        decay: StrategyDecayReport,
        topology: PortfolioTopologyReport,
        lifecycle: LifecycleReport,
    ) -> str:
        parts: list[str] = []

        if evolution_score >= 0.8:
            parts.append("系统进化评估: 优秀")
        elif evolution_score >= 0.6:
            parts.append("系统进化评估: 良好")
        elif evolution_score >= 0.4:
            parts.append("系统进化评估: 一般")
        else:
            parts.append("系统进化评估: 需改进")

        parts.append(f"进化评分: {evolution_score:.2f}")

        parts.append(f"特征漂移: {drift.overall_drift_score:.2f}")
        parts.append(f"策略衰减: {decay.overall_decay_score:.2f}")
        parts.append(f"组合结构: {topology.metrics.structural_efficiency:.2f}")
        parts.append(f"生命周期: {lifecycle.portfolio_lifecycle_phase}")

        if drift.has_critical_drift:
            parts.append(f"严重特征漂移: {len(drift.critical_decay_features)}个")

        if lifecycle.needs_renewal:
            parts.append("需要策略更新")

        return " | ".join(parts)
