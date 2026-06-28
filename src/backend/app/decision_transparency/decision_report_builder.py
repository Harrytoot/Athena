from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.decision_transparency.signal_explainer import SignalExplainer, SignalExplanation
from app.decision_transparency.factor_attribution import FactorAttributionEngine, FactorAttribution
from app.decision_transparency.risk_explainer import RiskExplainer, RiskExplanation
from app.decision_transparency.scenario_simulator import ScenarioSimulator, ScenarioResult
from app.decision_transparency.decision_trace import DecisionTracer, DecisionTrace
from app.domain.market.market_score import MarketScore


@dataclass
class DecisionReport:
    report_id: str
    generated_at: datetime
    title: str
    signal_explanation: SignalExplanation
    factor_attribution: FactorAttribution
    risk_explanation: RiskExplanation | None
    scenario_results: list[ScenarioResult] = field(default_factory=list)
    decision_trace: DecisionTrace | None = None
    user_action: str = "NONE"
    user_reason: str = ""
    overall_assessment: str = ""
    formatted_report: str = ""


class DecisionReportBuilder:

    def __init__(self):
        self._signal_explainer = SignalExplainer()
        self._factor_engine = FactorAttributionEngine()
        self._risk_explainer = RiskExplainer()
        self._scenario_simulator = ScenarioSimulator()
        self._tracer = DecisionTracer()

    def build(
        self,
        score: MarketScore,
        daily_returns: list[float] | None = None,
        drawdown_data: dict | None = None,
        correlation_data: dict | None = None,
        user_action: str = "NONE",
        user_reason: str = "",
        include_scenarios: bool = True,
        include_trace: bool = True,
    ) -> DecisionReport:
        signal_explanation = self._signal_explainer.explain(score)
        factor_attribution = self._factor_engine.attribute(score)

        risk_explanation: RiskExplanation | None = None
        if daily_returns is not None and len(daily_returns) >= 2:
            dd_data = drawdown_data or {}
            corr_data = correlation_data or {}

            drawdown = self._risk_explainer.explain_drawdown(
                max_drawdown=dd_data.get("max_drawdown", 0.0),
                avg_drawdown=dd_data.get("avg_drawdown", 0.0),
                drawdown_count=dd_data.get("drawdown_count", 0),
                avg_duration_days=dd_data.get("avg_duration_days", 0.0),
                ulcer_index=dd_data.get("ulcer_index", 0.0),
            )
            volatility = self._risk_explainer.explain_volatility(daily_returns)
            correlation = self._risk_explainer.explain_correlation(
                positions_count=corr_data.get("positions_count", 0),
                avg_pairwise_corr=corr_data.get("avg_pairwise_corr", 0.0),
                max_single_exposure=corr_data.get("max_single_exposure"),
            )
            overall_level, overall_summary, warnings = self._risk_explainer.build_overall(
                drawdown, volatility, correlation
            )
            risk_explanation = RiskExplanation(
                drawdown=drawdown,
                volatility=volatility,
                correlation=correlation,
                overall_risk_level=overall_level,
                overall_summary=overall_summary,
                warnings=warnings,
            )

        scenario_results: list[ScenarioResult] = []
        if include_scenarios:
            scenario_results = self._scenario_simulator.simulate(
                trend=score.trend,
                liquidity=score.liquidity,
                breadth=score.breadth,
                volatility=score.volatility,
                sentiment=score.sentiment,
            )

        decision_trace: DecisionTrace | None = None
        if include_trace:
            self._tracer.start()
            self._tracer.record_market_score(score)
            decision_trace = self._tracer.build()

        report_id = str(uuid4())
        generated_at = datetime.now(timezone.utc)

        overall = self._build_assessment(
            signal_explanation, factor_attribution, risk_explanation, scenario_results
        )

        formatted = self._format_report(
            report_id, generated_at, signal_explanation, factor_attribution,
            risk_explanation, scenario_results, decision_trace, user_action, user_reason, overall
        )

        return DecisionReport(
            report_id=report_id,
            generated_at=generated_at,
            title=f"决策透明度报告 - {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            signal_explanation=signal_explanation,
            factor_attribution=factor_attribution,
            risk_explanation=risk_explanation,
            scenario_results=scenario_results,
            decision_trace=decision_trace,
            user_action=user_action,
            user_reason=user_reason,
            overall_assessment=overall,
            formatted_report=formatted,
        )

    def _build_assessment(
        self,
        signal: SignalExplanation,
        factors: FactorAttribution,
        risk: RiskExplanation | None,
        scenarios: list[ScenarioResult],
    ) -> str:
        parts = []

        parts.append(f"评分: {signal.total_score:.1f} ({signal.market_state}), 方向: {signal.direction_label}")

        if signal.direction in ("LONG", "SHORT"):
            parts.append(
                f"置信度: {signal.confidence_score:.1f}% ({signal.confidence_level})"
            )

        parts.append(f"因子共识: {factors.factor_consensus}")

        if risk:
            parts.append(f"风险: {risk.overall_risk_level}")
            if risk.warnings:
                parts.append(f"警告: {'; '.join(risk.warnings)}")

        if scenarios:
            high_impact = [s for s in scenarios if abs(s.score_change) >= 20]
            if high_impact:
                parts.append(f"高影响情景: {len(high_impact)}个需要关注")

        return " | ".join(parts)

    def _format_report(
        self,
        report_id: str,
        generated_at: datetime,
        signal: SignalExplanation,
        factors: FactorAttribution,
        risk: RiskExplanation | None,
        scenarios: list[ScenarioResult],
        trace: DecisionTrace | None,
        user_action: str,
        user_reason: str,
        overall: str,
    ) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("  决策透明度报告")
        lines.append("=" * 60)
        lines.append(f"报告ID: {report_id}")
        lines.append(f"生成时间: {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("模型版本: 1.0.0")
        lines.append("")
        lines.append("-" * 60)
        lines.append("  1. 信号解释")
        lines.append("-" * 60)
        lines.append(f"综合评分: {signal.total_score:.1f}/100")
        lines.append(f"市场状态: {signal.market_state}")
        lines.append(f"方向判断: {signal.direction_label} ({signal.direction})")
        lines.append(f"置信度: {signal.confidence_score:.1f}% [{signal.confidence_level}]")
        lines.append(f"置信度说明: {signal.confidence_detail}")
        lines.append(f"摘要: {signal.summary}")
        lines.append("")
        lines.append("因子详情:")
        for n in signal.factor_narratives:
            lines.append(
                f"  {n.name:12s} 值={n.value:5.1f}  权重={n.weight:.2f}  "
                f"贡献={n.contribution:+5.1f}  {n.assessment}"
            )
        lines.append("")
        lines.append("-" * 60)
        lines.append("  2. 因子归因")
        lines.append("-" * 60)
        lines.append(f"总分: {factors.total_score:.1f}")
        lines.append(f"正向贡献: {factors.positive_contribution_sum:.1f}%")
        lines.append(f"负向贡献: {factors.negative_contribution_sum:.1f}%")
        lines.append(f"主导因子: {factors.dominant_factor}")
        lines.append(f"因子共识: {factors.factor_consensus}")
        lines.append(f"摘要: {factors.attribution_summary}")
        lines.append("")
        lines.append("归因明细:")
        for item in factors.items:
            lines.append(
                f"  {item.factor_label:12s}  原始值={item.raw_value:5.1f}  "
                f"加权贡献={item.weighted_contribution:+5.1f}  "
                f"占比={item.contribution_percentage:+5.1f}%  "
                f"{item.interpretation}"
            )
        lines.append("")

        if risk:
            lines.append("-" * 60)
            lines.append("  3. 风险评估")
            lines.append("-" * 60)
            lines.append(f"综合风险等级: {risk.overall_risk_level}")
            lines.append(f"总体评估: {risk.overall_summary}")
            lines.append("")
            lines.append(f"[回撤风险] 等级: {risk.drawdown.risk_level}")
            lines.append(f"  最大回撤: {risk.drawdown.max_drawdown_pct:.2f}%")
            lines.append(f"  平均回撤: {risk.drawdown.avg_drawdown_pct:.2f}%")
            lines.append(f"  回撤次数: {risk.drawdown.drawdown_count}")
            lines.append(f"  平均持续: {risk.drawdown.avg_duration_days:.1f}天")
            lines.append(f"  溃疡指数: {risk.drawdown.ulcer_index:.4f}")
            lines.append(f"  {risk.drawdown.explanation}")
            lines.append("")
            lines.append(f"[波动风险] 等级: {risk.volatility.risk_level}")
            lines.append(f"  年化波动率: {risk.volatility.annualized_volatility*100:.2f}%")
            lines.append(f"  日VaR(95%): {risk.volatility.var_95_daily*100:.2f}%")
            lines.append(f"  日CVaR(95%): {risk.volatility.cvar_95_daily*100:.2f}%")
            lines.append(f"  最差单日: {risk.volatility.worst_day_return*100:.2f}%")
            lines.append(f"  尾端比率: {risk.volatility.tail_ratio:.2f}")
            lines.append(f"  {risk.volatility.explanation}")
            lines.append("")
            lines.append(f"[相关性风险] 等级: {risk.correlation.risk_level}")
            lines.append(f"  平均相关性: {risk.correlation.avg_pairwise_correlation:.4f}")
            lines.append(f"  集中度: {risk.correlation.concentration_risk}")
            lines.append(f"  分散化得分: {risk.correlation.diversification_score:.2f}")
            lines.append(f"  {risk.correlation.explanation}")
            lines.append("")

            if risk.warnings:
                lines.append("风险警告:")
                for w in risk.warnings:
                    lines.append(f"  ! {w}")
                lines.append("")
        else:
            lines.append("-" * 60)
            lines.append("  3. 风险评估")
            lines.append("-" * 60)
            lines.append("  (无风险数据)")
            lines.append("")

        lines.append("-" * 60)
        lines.append("  4. 情景模拟")
        lines.append("-" * 60)
        if scenarios:
            for sr in scenarios:
                lines.append(f"  [{sr.scenario.name}]")
                lines.append(f"    原始评分: {sr.original_score:.1f} ({sr.original_state})")
                lines.append(f"    模拟评分: {sr.simulated_score:.1f} ({sr.simulated_state})")
                lines.append(f"    评分变化: {sr.score_change:+.1f}")
                lines.append(f"    方向变化: {sr.direction_change}")
                lines.append(f"    影响评估: {sr.impact_assessment}")
                lines.append("")
        else:
            lines.append("  (未启用情景模拟)")
            lines.append("")

        lines.append("-" * 60)
        lines.append("  5. 决策追溯")
        lines.append("-" * 60)
        if trace:
            lines.append(f"追溯ID: {trace.trace_id}")
            lines.append(f"输入哈希: {trace.input_hash}")
            lines.append(f"模型版本: {trace.model_version}")
            lines.append(f"评分引擎版本: {trace.scoring_engine_version}")
            lines.append(f"步骤数: {trace.step_count}")
            lines.append("")
            lines.append("决策链路:")
            lines.append(trace.full_lineage)
            lines.append("")
        else:
            lines.append("  (未启用决策追溯)")
            lines.append("")

        lines.append("-" * 60)
        lines.append("  6. 用户决策")
        lines.append("-" * 60)
        lines.append(f"用户操作: {user_action}")
        if user_reason:
            lines.append(f"操作原因: {user_reason}")
        lines.append("")

        lines.append("=" * 60)
        lines.append(f"总体评估: {overall}")
        lines.append("=" * 60)

        return "\n".join(lines)
