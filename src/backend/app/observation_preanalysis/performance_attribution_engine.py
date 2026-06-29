import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_transparency.factor_attribution import FactorAttribution, FactorAttributionEngine
from app.domain.market.market_score import MarketScore
from app.feature_store.repository import FeatureRepository

logger = logging.getLogger(__name__)


@dataclass
class FactorContribution:
    factor_name: str
    factor_label: str
    raw_value: float
    weight: float
    contribution: float
    contribution_pct: float
    is_positive: bool


@dataclass
class RegimeContribution:
    regime: str
    regime_label: str
    contribution_pct: float
    avg_return: float


@dataclass
class AttributionReport:
    timestamp: datetime
    total_score: float
    market_state: str
    factor_contributions: list[FactorContribution] = field(default_factory=list)
    regime_contributions: list[RegimeContribution] = field(default_factory=list)
    dominant_factor: str = ""
    dominant_factor_pct: float = 0.0
    positive_sum: float = 0.0
    negative_sum: float = 0.0
    volatility_impact: float = 0.0
    attribution_summary: str = ""

    @property
    def is_bullish(self) -> bool:
        return self.total_score >= 60

    @property
    def is_bearish(self) -> bool:
        return self.total_score <= 40


class PerformanceAttributionEngine:

    def __init__(self):
        self._factor_engine = FactorAttributionEngine()

    async def attribute(self, feature_repo: FeatureRepository) -> AttributionReport:
        timestamp = datetime.now(timezone.utc)
        logger.info("Running performance attribution analysis")

        features: dict[str, float] = {}
        for name in ["trend_strength", "market_turnover", "advancers_ratio", "volatility_index", "northbound_flow"]:
            item = await feature_repo.get_latest(name)
            features[name] = item.value if item is not None else 50.0

        score = MarketScore(
            trend=features["trend_strength"],
            liquidity=features["market_turnover"],
            breadth=features["advancers_ratio"],
            volatility=features["volatility_index"],
            sentiment=features["northbound_flow"],
        )

        factor_attribution: FactorAttribution = self._factor_engine.attribute(score)

        factor_contributions = [
            FactorContribution(
                factor_name=item.factor_name,
                factor_label=item.factor_label,
                raw_value=item.raw_value,
                weight=item.weight,
                contribution=item.weighted_contribution,
                contribution_pct=item.contribution_percentage,
                is_positive=item.is_positive,
            )
            for item in factor_attribution.items
        ]

        regime_contributions = self._classify_regime_contribution(score)

        volatility_impact = self._compute_volatility_impact(features["volatility_index"])

        return AttributionReport(
            timestamp=timestamp,
            total_score=round(score.total, 2),
            market_state=score.state,
            factor_contributions=factor_contributions,
            regime_contributions=regime_contributions,
            dominant_factor=factor_attribution.dominant_factor,
            dominant_factor_pct=factor_attribution.dominant_contribution_pct,
            positive_sum=factor_attribution.positive_contribution_sum,
            negative_sum=factor_attribution.negative_contribution_sum,
            volatility_impact=volatility_impact,
            attribution_summary=factor_attribution.attribution_summary,
        )

    @staticmethod
    def _classify_regime_contribution(score: MarketScore) -> list[RegimeContribution]:
        contributions: list[RegimeContribution] = []

        if score.total >= 60:
            contributions.append(RegimeContribution(
                regime="bull", regime_label="上升趋势",
                contribution_pct=min(100.0, (score.total - 50) * 2),
                avg_return=round(score.trend / 100 * 5, 2),
            ))
        elif score.total >= 40:
            contributions.append(RegimeContribution(
                regime="range", regime_label="震荡区间",
                contribution_pct=50.0,
                avg_return=0.0,
            ))
        else:
            contributions.append(RegimeContribution(
                regime="bear", regime_label="下降趋势",
                contribution_pct=min(100.0, (50 - score.total) * 2),
                avg_return=round((score.trend - 100) / 100 * 5, 2),
            ))

        contributions.append(RegimeContribution(
            regime="volatility", regime_label="波动贡献",
            contribution_pct=min(100.0, score.volatility),
            avg_return=round(score.volatility / 100 * 3 - 1.5, 2),
        ))

        contributions.append(RegimeContribution(
            regime="sentiment", regime_label="情绪驱动",
            contribution_pct=min(100.0, abs(score.sentiment - 50) * 2),
            avg_return=round((score.sentiment - 50) / 100 * 4, 2),
        ))

        return contributions

    @staticmethod
    def _compute_volatility_impact(volatility: float) -> float:
        if volatility <= 30:
            return round(volatility / 30 * 0.5, 2)
        elif volatility <= 60:
            return round(0.5 + (volatility - 30) / 30 * 0.5, 2)
        else:
            return round(1.0 + (volatility - 60) / 40 * 0.5, 2)
