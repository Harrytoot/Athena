import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from app.observation_preanalysis.performance_attribution_engine import AttributionReport
from app.observation_preanalysis.strategy_batch_runner import BatchResult
from app.observation_preanalysis.strategy_ranker import RankedStrategyList

logger = logging.getLogger(__name__)


class ActionRecommendation(str, Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    STOP = "STOP"


@dataclass
class MarketRegimeSummary:
    regime: str
    temperature: int
    market_state: str
    description: str


@dataclass
class RiskState:
    drawdown_risk: str
    volatility_risk: str
    exposure_risk: str
    overall_level: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class FactorAttributionSummary:
    dominant_factor: str
    dominant_pct: float
    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ActionItem:
    symbol: str
    name: str
    action: str
    confidence: float
    reason: str


@dataclass
class PreObservationReport:
    window: str
    timestamp: datetime
    market_regime_summary: MarketRegimeSummary
    strategy_ranking: RankedStrategyList
    risk_state: RiskState
    factor_attribution: FactorAttributionSummary
    action_recommendations: list[ActionItem] = field(default_factory=list)
    confidence_score: float = 0.0
    summary: str = ""

    @property
    def is_actionable(self) -> bool:
        return self.confidence_score >= 60.0


class PreObservationReportGenerator:

    async def generate(
        self,
        window: str,
        batch_result: BatchResult | None,
        ranked_list: RankedStrategyList | None,
        attribution: AttributionReport | None,
    ) -> PreObservationReport:
        timestamp = datetime.now(timezone.utc)
        logger.info("Generating pre-observation report for window [%s]", window)

        if batch_result is None:
            batch_result = BatchResult(window=window, timestamp=timestamp)
        if ranked_list is None:
            ranked_list = RankedStrategyList(window=window)
        if attribution is None:
            attribution = AttributionReport(
                timestamp=timestamp,
                total_score=50.0,
                market_state="neutral",
            )

        regime_summary = self._build_regime_summary(attribution)
        risk_state = self._build_risk_state(attribution)
        factor_summary = self._build_factor_summary(attribution)
        actions = self._build_action_recommendations(batch_result, ranked_list)
        confidence = self._compute_confidence(batch_result, attribution, ranked_list)
        summary = self._build_summary(window, regime_summary, ranked_list, risk_state, confidence)

        report = PreObservationReport(
            window=window,
            timestamp=timestamp,
            market_regime_summary=regime_summary,
            strategy_ranking=ranked_list,
            risk_state=risk_state,
            factor_attribution=factor_summary,
            action_recommendations=actions,
            confidence_score=confidence,
            summary=summary,
        )

        logger.info(
            "Pre-observation report [%s]: regime=%s confidence=%.1f actions=%d",
            window, regime_summary.regime, confidence, len(actions),
        )
        return report

    @staticmethod
    def _build_regime_summary(attribution: AttributionReport) -> MarketRegimeSummary:
        score = attribution.total_score
        if score >= 60:
            regime = "Bull"
            description = "市场处于上升趋势，多头信号占优"
        elif score >= 40:
            regime = "Range"
            description = "市场处于震荡区间，方向性不明确"
        else:
            regime = "Bear"
            description = "市场处于下降趋势，风险偏好降低"

        return MarketRegimeSummary(
            regime=regime,
            temperature=int(score),
            market_state=attribution.market_state,
            description=description,
        )

    @staticmethod
    def _build_risk_state(attribution: AttributionReport) -> RiskState:
        warnings = []
        score = attribution.total_score

        if score <= 40:
            drawdown_risk = "高"
            warnings.append("市场评分偏低，下行风险显著")
        elif score <= 60:
            drawdown_risk = "中等"
        else:
            drawdown_risk = "低"

        if attribution.volatility_impact > 1.0:
            volatility_risk = "高"
            warnings.append("波动率偏高，仓位建议降低")
        elif attribution.volatility_impact > 0.6:
            volatility_risk = "中等"
        else:
            volatility_risk = "低"

        if score >= 70:
            exposure_risk = "低"
        elif score >= 50:
            exposure_risk = "中等"
        else:
            exposure_risk = "高"
            warnings.append("建议降低总仓位暴露")

        overall = "高风险" if len(warnings) >= 2 else ("中等风险" if warnings else "低风险")

        return RiskState(
            drawdown_risk=drawdown_risk,
            volatility_risk=volatility_risk,
            exposure_risk=exposure_risk,
            overall_level=overall,
            warnings=warnings,
        )

    @staticmethod
    def _build_factor_summary(attribution: AttributionReport) -> FactorAttributionSummary:
        positive = [f.factor_label for f in attribution.factor_contributions if f.is_positive]
        negative = [f.factor_label for f in attribution.factor_contributions if not f.is_positive]

        if attribution.total_score >= 60:
            desc = f"多头因子主导: {', '.join(positive) if positive else '无显著因子'}"
        elif attribution.total_score <= 40:
            desc = f"空头因子主导: {', '.join(negative) if negative else '无显著因子'}"
        else:
            desc = "多空因子均衡"

        return FactorAttributionSummary(
            dominant_factor=attribution.dominant_factor,
            dominant_pct=attribution.dominant_factor_pct,
            positive_factors=positive,
            negative_factors=negative,
            description=desc,
        )

    @staticmethod
    def _build_action_recommendations(
        batch_result: BatchResult,
        ranked_list: RankedStrategyList,
    ) -> list[ActionItem]:
        actions = []
        for s in ranked_list.strategies[:5]:
            if s.signal == "STRONG_BUY" and s.confidence >= 70:
                action = "BUY"
                reason = f"强买入信号，置信度 {s.confidence:.0f}%"
            elif s.signal == "BUY" and s.confidence >= 60:
                action = "HOLD"
                reason = f"买入信号，但置信度中等 ({s.confidence:.0f}%)，建议持有观察"
            elif s.signal in ("SELL", "STRONG_SELL"):
                action = "REDUCE"
                reason = "卖出信号，建议减仓"
            elif s.confidence < 50:
                action = "STOP"
                reason = "信号不稳定，建议暂停操作"
            else:
                action = "HOLD"
                reason = "信号中性，维持现有仓位"

            actions.append(ActionItem(
                symbol=s.symbol,
                name=s.name,
                action=action,
                confidence=s.confidence,
                reason=reason,
            ))
        return actions

    @staticmethod
    def _compute_confidence(
        batch_result: BatchResult,
        attribution: AttributionReport,
        ranked_list: RankedStrategyList,
    ) -> float:
        if batch_result.total_count == 0:
            return 0.0

        batch_confidence = batch_result.avg_confidence

        score_confidence = 100.0 - abs(attribution.total_score - 50) * 1.2
        score_confidence = max(20.0, min(100.0, score_confidence))

        rank_confidence = 0.0
        if ranked_list.strategies:
            rank_confidence = ranked_list.strategies[0].composite_score * 50

        deterministic = batch_confidence * 0.4 + score_confidence * 0.35 + rank_confidence * 0.25
        return round(min(100.0, max(0.0, deterministic)), 1)

    @staticmethod
    def _build_summary(
        window: str,
        regime: MarketRegimeSummary,
        ranked: RankedStrategyList,
        risk: RiskState,
        confidence: float,
    ) -> str:
        parts = [
            f"[{window}] 观察窗口分析报告",
            f"市场状态: {regime.regime} (评分 {regime.temperature})",
            f"策略排名: {ranked.ranking_summary}",
            f"风险等级: {risk.overall_level}",
        ]
        if risk.warnings:
            parts.append(f"风险提示: {'; '.join(risk.warnings)}")
        parts.append(f"系统置信度: {confidence:.1f}%")
        return "\n".join(parts)
