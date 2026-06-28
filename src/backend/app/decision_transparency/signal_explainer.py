from dataclasses import dataclass

from app.domain.market.market_score import MarketScore

FACTOR_WEIGHT_TREND = 0.30
FACTOR_WEIGHT_LIQUIDITY = 0.25
FACTOR_WEIGHT_BREADTH = 0.20
FACTOR_WEIGHT_VOLATILITY = 0.15
FACTOR_WEIGHT_SENTIMENT = 0.10

CONFIDENCE_VERY_HIGH_THRESHOLD = 90.0
CONFIDENCE_HIGH_THRESHOLD = 75.0
CONFIDENCE_MODERATE_THRESHOLD = 50.0
CONFIDENCE_LOW_THRESHOLD = 25.0


@dataclass
class FactorNarrative:
    name: str
    value: float
    weight: float
    contribution: float
    assessment: str


@dataclass
class SignalExplanation:
    total_score: float
    market_state: str
    direction: str
    direction_label: str
    confidence_score: float
    confidence_level: str
    confidence_detail: str
    summary: str
    factor_narratives: list[FactorNarrative]


class SignalExplainer:

    def __init__(
        self,
        trend_weight: float = FACTOR_WEIGHT_TREND,
        liquidity_weight: float = FACTOR_WEIGHT_LIQUIDITY,
        breadth_weight: float = FACTOR_WEIGHT_BREADTH,
        volatility_weight: float = FACTOR_WEIGHT_VOLATILITY,
        sentiment_weight: float = FACTOR_WEIGHT_SENTIMENT,
    ):
        self._weights = {
            "trend": trend_weight,
            "liquidity": liquidity_weight,
            "breadth": breadth_weight,
            "volatility": volatility_weight,
            "sentiment": sentiment_weight,
        }
        self._total_weight = sum(self._weights.values())

    def explain(self, score: MarketScore) -> SignalExplanation:
        total = score.total
        direction = self._classify_direction(total)
        direction_label = self._direction_label(direction)
        confidence = self._compute_confidence(score)

        narratives = [
            self._build_factor_narrative("trend", score.trend, self._weights["trend"]),
            self._build_factor_narrative("liquidity", score.liquidity, self._weights["liquidity"]),
            self._build_factor_narrative("breadth", score.breadth, self._weights["breadth"]),
            self._build_factor_narrative("volatility", score.volatility, self._weights["volatility"]),
            self._build_factor_narrative("sentiment", score.sentiment, self._weights["sentiment"]),
        ]

        summary = self._build_summary(total, direction_label, confidence, narratives)

        return SignalExplanation(
            total_score=total,
            market_state=score.state,
            direction=direction,
            direction_label=direction_label,
            confidence_score=round(confidence, 2),
            confidence_level=self._confidence_level(confidence),
            confidence_detail=self._confidence_detail(confidence),
            summary=summary,
            factor_narratives=narratives,
        )

    def _classify_direction(self, total: float) -> str:
        if total >= 60:
            return "LONG"
        if total <= 40:
            return "SHORT"
        return "NEUTRAL"

    def _direction_label(self, direction: str) -> str:
        labels = {"LONG": "看多", "SHORT": "看空", "NEUTRAL": "中性"}
        return labels.get(direction, "未知")

    def _compute_confidence(self, score: MarketScore) -> float:
        factors = [
            (score.trend, self._weights["trend"]),
            (score.liquidity, self._weights["liquidity"]),
            (score.breadth, self._weights["breadth"]),
            (score.volatility, self._weights["volatility"]),
            (score.sentiment, self._weights["sentiment"]),
        ]

        agreements = sum(1 for v, _ in factors if v >= 60)
        disagreements = sum(1 for v, _ in factors if v <= 40)

        if agreements >= 4:
            base = 90.0
        elif agreements >= 3:
            base = 75.0
        elif disagreements >= 4:
            base = 90.0
        elif disagreements >= 3:
            base = 75.0
        elif agreements >= 2:
            base = 50.0
        elif disagreements >= 2:
            base = 50.0
        else:
            base = 30.0

        strength = abs(score.total - 50.0) / 50.0
        adjusted = base * (0.7 + 0.3 * strength)
        return min(100.0, max(0.0, adjusted))

    def _confidence_level(self, confidence: float) -> str:
        if confidence >= CONFIDENCE_VERY_HIGH_THRESHOLD:
            return "VERY_HIGH"
        if confidence >= CONFIDENCE_HIGH_THRESHOLD:
            return "HIGH"
        if confidence >= CONFIDENCE_MODERATE_THRESHOLD:
            return "MODERATE"
        if confidence >= CONFIDENCE_LOW_THRESHOLD:
            return "LOW"
        return "VERY_LOW"

    def _confidence_detail(self, confidence: float) -> str:
        level = self._confidence_level(confidence)
        details = {
            "VERY_HIGH": "多因子高度一致，置信度极高",
            "HIGH": "多数因子方向一致，置信度较高",
            "MODERATE": "因子信号存在分歧，置信度一般",
            "LOW": "因子信号分歧较大，置信度较低",
            "VERY_LOW": "因子信号严重冲突，置信度极低",
        }
        return details.get(level, "")

    def _build_factor_narrative(self, name: str, value: float, weight: float) -> FactorNarrative:
        contribution = round(value * weight, 2)
        assessment = self._factor_assessment(name, value)
        return FactorNarrative(
            name=name,
            value=value,
            weight=weight,
            contribution=contribution,
            assessment=assessment,
        )

    def _factor_assessment(self, name: str, value: float) -> str:
        labels = {
            "trend": "趋势",
            "liquidity": "流动性",
            "breadth": "市场宽度",
            "volatility": "波动率",
            "sentiment": "情绪",
        }
        label = labels.get(name, name)

        if value >= 80:
            return f"{label}极强({value:.1f})"
        if value >= 60:
            return f"{label}偏强({value:.1f})"
        if value >= 40:
            return f"{label}中性({value:.1f})"
        if value >= 20:
            return f"{label}偏弱({value:.1f})"
        return f"{label}极弱({value:.1f})"

    def _build_summary(
        self,
        total: float,
        direction_label: str,
        confidence: float,
        narratives: list[FactorNarrative],
    ) -> str:
        contribs_sorted = sorted(narratives, key=lambda n: abs(n.contribution), reverse=True)
        top_positive = [n for n in contribs_sorted if n.contribution > 0][:2]
        top_negative = [n for n in contribs_sorted if n.contribution < 0][:2]

        parts = [f"综合评分{total:.1f}，方向{direction_label}"]

        if top_positive:
            pos_str = "、".join(f"{n.name}(+{n.contribution:.1f})" for n in top_positive)
            parts.append(f"正向贡献: {pos_str}")
        if top_negative:
            neg_str = "、".join(f"{n.name}({n.contribution:.1f})" for n in top_negative)
            parts.append(f"负向拖累: {neg_str}")

        parts.append(f"置信度: {confidence:.1f}% ({self._confidence_level(confidence)})")
        return "；".join(parts)
