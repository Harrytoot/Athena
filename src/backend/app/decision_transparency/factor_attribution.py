from dataclasses import dataclass, field

from app.domain.market.market_score import MarketScore

FACTOR_CONFIG: dict[str, dict[str, float | str]] = {
    "trend": {"weight": 0.30, "label": "趋势强度", "max_contrib": 30.0},
    "liquidity": {"weight": 0.25, "label": "市场流动性", "max_contrib": 25.0},
    "breadth": {"weight": 0.20, "label": "市场宽度", "max_contrib": 20.0},
    "volatility": {"weight": 0.15, "label": "波动率", "max_contrib": 15.0},
    "sentiment": {"weight": 0.10, "label": "市场情绪", "max_contrib": 10.0},
}

TOTAL_MAX_SCORE = 100.0


@dataclass
class FactorAttributionItem:
    factor_name: str
    factor_label: str
    raw_value: float
    weight: float
    weighted_contribution: float
    contribution_percentage: float
    is_positive: bool
    interpretation: str


@dataclass
class FactorAttribution:
    total_score: float
    items: list[FactorAttributionItem] = field(default_factory=list)
    positive_contribution_sum: float = 0.0
    negative_contribution_sum: float = 0.0
    dominant_factor: str = ""
    dominant_contribution_pct: float = 0.0
    factor_consensus: str = ""
    attribution_summary: str = ""


class FactorAttributionEngine:

    def __init__(self, factor_config: dict | None = None):
        self._config = factor_config or FACTOR_CONFIG

    def attribute(self, score: MarketScore) -> FactorAttribution:
        total = score.total

        items: list[FactorAttributionItem] = []
        positive_sum = 0.0
        negative_sum = 0.0

        raw_values = {
            "trend": score.trend,
            "liquidity": score.liquidity,
            "breadth": score.breadth,
            "volatility": score.volatility,
            "sentiment": score.sentiment,
        }

        for name, cfg in self._config.items():
            raw = raw_values[name]
            weight = float(cfg["weight"])
            weighted = round(raw * weight, 2)
            pct = round(weighted / TOTAL_MAX_SCORE * 100, 2)
            is_positive = weighted > 0

            if is_positive:
                positive_sum += weighted
            else:
                negative_sum += weighted

            interpretation = self._interpret_factor(name, raw)

            items.append(FactorAttributionItem(
                factor_name=name,
                factor_label=str(cfg["label"]),
                raw_value=raw,
                weight=weight,
                weighted_contribution=weighted,
                contribution_percentage=pct,
                is_positive=is_positive,
                interpretation=interpretation,
            ))

        sorted_by_abs = sorted(items, key=lambda i: abs(i.weighted_contribution), reverse=True)
        dominant = sorted_by_abs[0] if sorted_by_abs else None

        positive_pct = round(positive_sum / TOTAL_MAX_SCORE * 100, 2) if positive_sum > 0 else 0.0
        negative_pct = round(abs(negative_sum) / TOTAL_MAX_SCORE * 100, 2) if negative_sum < 0 else 0.0

        consensus = self._assess_consensus(items)

        summary = self._build_summary(total, dominant, positive_pct, negative_pct, consensus)

        return FactorAttribution(
            total_score=total,
            items=items,
            positive_contribution_sum=positive_pct,
            negative_contribution_sum=negative_pct,
            dominant_factor=dominant.factor_name if dominant else "",
            dominant_contribution_pct=dominant.contribution_percentage if dominant else 0.0,
            factor_consensus=consensus,
            attribution_summary=summary,
        )

    def _interpret_factor(self, name: str, value: float) -> str:
        thresholds = {
            "trend": [(80, "强势上升趋势"), (60, "温和上升趋势"), (40, "趋势不明朗"), (20, "温和下降趋势")],
            "liquidity": [(80, "流动性充裕"), (60, "流动性正常"), (40, "流动性中性"), (20, "流动性偏紧")],
            "breadth": [(80, "市场普涨"), (60, "多数上涨"), (40, "涨跌互现"), (20, "多数下跌")],
            "volatility": [(80, "极低波动(低风险偏好)"), (60, "低波动环境"), (40, "中等波动"), (20, "高波动警报")],
            "sentiment": [(80, "情绪亢奋"), (60, "情绪乐观"), (40, "情绪中性"), (20, "情绪悲观")],
        }

        ranges = thresholds.get(name, [])
        for threshold, label in ranges:
            if value >= threshold:
                return label

        default_low = {
            "trend": "弱势下降趋势",
            "liquidity": "流动性枯竭",
            "breadth": "市场普跌",
            "volatility": "极高波动(恐慌)",
            "sentiment": "情绪恐慌",
        }
        return default_low.get(name, "极弱")

    def _assess_consensus(self, items: list[FactorAttributionItem]) -> str:
        bullish = sum(1 for i in items if i.raw_value >= 60)
        bearish = sum(1 for i in items if i.raw_value <= 40)

        if bullish >= 4:
            return "强势共识看多"
        if bullish >= 3:
            return "偏多共识"
        if bearish >= 4:
            return "强势共识看空"
        if bearish >= 3:
            return "偏空共识"
        if bullish >= 2:
            return "弱偏多"
        if bearish >= 2:
            return "弱偏空"
        return "分歧"

    def _build_summary(
        self,
        total: float,
        dominant: FactorAttributionItem | None,
        positive_pct: float,
        negative_pct: float,
        consensus: str,
    ) -> str:
        parts = [f"总分{total:.1f}分"]

        if dominant:
            parts.append(
                f"主导因子: {dominant.factor_label}({dominant.interpretation}) "
                f"贡献{dominant.contribution_percentage:.1f}%"
            )

        parts.append(f"正向贡献{positive_pct:.1f}%")
        parts.append(f"负向贡献{negative_pct:.1f}%")
        parts.append(f"共识: {consensus}")

        return "；".join(parts)
