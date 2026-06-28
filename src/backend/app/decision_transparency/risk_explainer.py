import math
from dataclasses import dataclass, field


@dataclass
class DrawdownRiskDetail:
    max_drawdown_pct: float
    avg_drawdown_pct: float
    drawdown_count: int
    avg_duration_days: float
    ulcer_index: float
    risk_level: str
    explanation: str


@dataclass
class VolatilityRiskDetail:
    annualized_volatility: float
    daily_volatility: float
    var_95_daily: float
    cvar_95_daily: float
    worst_day_return: float
    tail_ratio: float
    risk_level: str
    explanation: str


@dataclass
class CorrelationRiskDetail:
    avg_pairwise_correlation: float
    concentration_risk: str
    diversification_score: float
    risk_level: str
    explanation: str


@dataclass
class RiskExplanation:
    drawdown: DrawdownRiskDetail
    volatility: VolatilityRiskDetail
    correlation: CorrelationRiskDetail
    overall_risk_level: str
    overall_summary: str
    warnings: list[str] = field(default_factory=list)


RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_MODERATE = "MODERATE"
RISK_LEVEL_LOW = "LOW"

DRAWDOWN_HIGH_THRESHOLD = 0.20
DRAWDOWN_MODERATE_THRESHOLD = 0.10
VOLATILITY_HIGH_THRESHOLD = 0.40
VOLATILITY_MODERATE_THRESHOLD = 0.20
VAR_HIGH_THRESHOLD = 0.03
VAR_MODERATE_THRESHOLD = 0.015
TAIL_RATIO_LOW_THRESHOLD = 1.0
TAIL_RATIO_HIGH_THRESHOLD = 3.0
CORRELATION_HIGH_THRESHOLD = 0.70
CORRELATION_MODERATE_THRESHOLD = 0.40
CONCENTRATION_HIGH_THRESHOLD = 0.50


class RiskExplainer:

    def explain_drawdown(
        self,
        max_drawdown: float,
        avg_drawdown: float,
        drawdown_count: int,
        avg_duration_days: float,
        ulcer_index: float,
    ) -> DrawdownRiskDetail:
        if max_drawdown <= -DRAWDOWN_HIGH_THRESHOLD:
            level = RISK_LEVEL_HIGH
            explanation = (
                f"最大回撤{abs(max_drawdown)*100:.1f}%，超过{int(DRAWDOWN_HIGH_THRESHOLD*100)}%阈值，"
                f"属于高回撤风险。历史共发生{drawdown_count}次回撤事件，"
                f"平均持续{avg_duration_days:.0f}个交易日。"
                f"溃疡指数{ulcer_index:.4f}，反映回撤深度和持续时间综合风险较高。"
            )
        elif max_drawdown <= -DRAWDOWN_MODERATE_THRESHOLD:
            level = RISK_LEVEL_MODERATE
            explanation = (
                f"最大回撤{abs(max_drawdown)*100:.1f}%，处于{int(DRAWDOWN_MODERATE_THRESHOLD*100)}%-"
                f"{int(DRAWDOWN_HIGH_THRESHOLD*100)}%之间，属中等回撤风险。"
                f"历史共发生{drawdown_count}次回撤事件，平均持续{avg_duration_days:.0f}个交易日。"
            )
        else:
            level = RISK_LEVEL_LOW
            explanation = (
                f"最大回撤{abs(max_drawdown)*100:.1f}%，低于{int(DRAWDOWN_MODERATE_THRESHOLD*100)}%阈值，"
                f"回撤风险可控。历史共发生{drawdown_count}次回撤事件，"
                f"平均持续{avg_duration_days:.0f}个交易日。"
            )

        return DrawdownRiskDetail(
            max_drawdown_pct=round(max_drawdown * 100, 2),
            avg_drawdown_pct=round(avg_drawdown * 100, 2),
            drawdown_count=drawdown_count,
            avg_duration_days=round(avg_duration_days, 1),
            ulcer_index=round(ulcer_index, 4),
            risk_level=level,
            explanation=explanation,
        )

    def explain_volatility(
        self,
        daily_returns: list[float],
        annualization_factor: float = 252.0,
    ) -> VolatilityRiskDetail:
        n = len(daily_returns)
        if n < 2:
            return VolatilityRiskDetail(
                annualized_volatility=0.0,
                daily_volatility=0.0,
                var_95_daily=0.0,
                cvar_95_daily=0.0,
                worst_day_return=0.0,
                tail_ratio=0.0,
                risk_level=RISK_LEVEL_LOW,
                explanation="数据不足，无法评估波动率风险",
            )

        mean_r = sum(daily_returns) / n
        variance = sum((r - mean_r) ** 2 for r in daily_returns) / (n - 1)
        daily_vol = math.sqrt(variance)
        annual_vol = daily_vol * math.sqrt(annualization_factor)

        sorted_r = sorted(daily_returns)
        var_95 = self._percentile(sorted_r, 0.05)
        cvar_95 = self._cvar(sorted_r, var_95)
        worst_day = min(daily_returns)

        positive_sum = sum(r for r in daily_returns if r > 0)
        negative_sum = abs(sum(r for r in daily_returns if r < 0))
        tail_ratio = positive_sum / negative_sum if negative_sum > 0 else 0.0

        level = self._volatility_level(annual_vol, var_95, tail_ratio)
        explanation = self._volatility_explanation(annual_vol, var_95, cvar_95, worst_day, tail_ratio, level)

        return VolatilityRiskDetail(
            annualized_volatility=round(annual_vol, 4),
            daily_volatility=round(daily_vol, 4),
            var_95_daily=round(var_95, 4),
            cvar_95_daily=round(cvar_95, 4),
            worst_day_return=round(worst_day, 4),
            tail_ratio=round(tail_ratio, 2),
            risk_level=level,
            explanation=explanation,
        )

    def explain_correlation(
        self,
        positions_count: int,
        avg_pairwise_corr: float,
        max_single_exposure: float | None = None,
    ) -> CorrelationRiskDetail:
        if avg_pairwise_corr >= CORRELATION_HIGH_THRESHOLD:
            corr_level = RISK_LEVEL_HIGH
        elif avg_pairwise_corr >= CORRELATION_MODERATE_THRESHOLD:
            corr_level = RISK_LEVEL_MODERATE
        else:
            corr_level = RISK_LEVEL_LOW

        if positions_count <= 1:
            concentration = "单一持仓，无分散化" if positions_count == 1 else "无持仓"
        elif max_single_exposure is not None and max_single_exposure >= CONCENTRATION_HIGH_THRESHOLD:
            concentration = f"持仓集中度过高(最大单仓{max_single_exposure*100:.0f}%)"
        elif positions_count < 5:
            concentration = f"持仓数量较少({positions_count}个)，分散化不足"
        else:
            concentration = f"持仓分散({positions_count}个)，集中度可控"

        if corr_level == RISK_LEVEL_HIGH:
            diversification = max(0.0, 1.0 - avg_pairwise_corr)
        elif corr_level == RISK_LEVEL_MODERATE:
            diversification = 0.5 + (1.0 - avg_pairwise_corr) * 0.5
        else:
            diversification = 0.8

        explanation = (
            f"持仓间平均相关性{avg_pairwise_corr:.2f}，{self._corr_label(avg_pairwise_corr)}。"
            f"{concentration}。分散化得分{diversification:.2f}/1.0。"
        )

        return CorrelationRiskDetail(
            avg_pairwise_correlation=round(avg_pairwise_corr, 4),
            concentration_risk=concentration,
            diversification_score=round(diversification, 2),
            risk_level=corr_level,
            explanation=explanation,
        )

    def build_overall(
        self,
        drawdown: DrawdownRiskDetail,
        volatility: VolatilityRiskDetail,
        correlation: CorrelationRiskDetail,
    ) -> tuple[str, str, list[str]]:
        levels = [drawdown.risk_level, volatility.risk_level, correlation.risk_level]
        high_count = sum(1 for level in levels if level == RISK_LEVEL_HIGH)
        moderate_count = sum(1 for level in levels if level == RISK_LEVEL_MODERATE)

        if high_count >= 2:
            overall = RISK_LEVEL_HIGH
        elif high_count >= 1 or moderate_count >= 2:
            overall = RISK_LEVEL_MODERATE
        else:
            overall = RISK_LEVEL_LOW

        level_labels = {
            RISK_LEVEL_HIGH: "高风险",
            RISK_LEVEL_MODERATE: "中等风险",
            RISK_LEVEL_LOW: "低风险",
        }

        summary = (
            f"综合风险评估: {level_labels[overall]}。"
            f"回撤风险: {level_labels[drawdown.risk_level]}，"
            f"波动风险: {level_labels[volatility.risk_level]}，"
            f"相关性风险: {level_labels[correlation.risk_level]}。"
        )

        warnings: list[str] = []
        if drawdown.risk_level == RISK_LEVEL_HIGH:
            warnings.append(f"回撤风险高企: 最大回撤{abs(drawdown.max_drawdown_pct):.1f}%")
        if volatility.annualized_volatility >= VOLATILITY_HIGH_THRESHOLD:
            warnings.append(f"波动率偏高: 年化波动率{volatility.annualized_volatility*100:.1f}%")
        if volatility.var_95_daily <= -VAR_HIGH_THRESHOLD:
            warnings.append(f"尾部风险显著: 日VaR(95%)={volatility.var_95_daily*100:.2f}%")
        if correlation.avg_pairwise_correlation >= CORRELATION_HIGH_THRESHOLD:
            warnings.append(f"持仓高度相关: 平均相关性{correlation.avg_pairwise_correlation:.2f}")
        if correlation.diversification_score <= 0.3:
            warnings.append(f"分散化严重不足: 得分{correlation.diversification_score:.2f}")

        return overall, summary, warnings

    def _volatility_level(self, annual_vol: float, var_95: float, tail_ratio: float) -> str:
        if annual_vol >= VOLATILITY_HIGH_THRESHOLD:
            return RISK_LEVEL_HIGH
        if annual_vol >= VOLATILITY_MODERATE_THRESHOLD:
            return RISK_LEVEL_MODERATE
        if var_95 <= -VAR_MODERATE_THRESHOLD:
            return RISK_LEVEL_HIGH
        if tail_ratio < TAIL_RATIO_LOW_THRESHOLD and tail_ratio > 0:
            return RISK_LEVEL_HIGH
        return RISK_LEVEL_LOW

    def _volatility_explanation(
        self,
        annual_vol: float,
        var_95: float,
        cvar_95: float,
        worst_day: float,
        tail_ratio: float,
        level: str,
    ) -> str:
        parts = [
            f"年化波动率{annual_vol*100:.1f}%",
            f"日VaR(95%)={var_95*100:.2f}%",
            f"日CVaR(95%)={cvar_95*100:.2f}%",
            f"最差单日收益{worst_day*100:.2f}%",
            f"尾端比率{tail_ratio:.2f}",
        ]

        level_labels = {
            RISK_LEVEL_HIGH: "波动风险较高，可能面临较大回撤",
            RISK_LEVEL_MODERATE: "波动风险适中",
            RISK_LEVEL_LOW: "波动风险较低，收益相对稳定",
        }
        parts.append(level_labels.get(level, ""))

        return "；".join(parts)

    def _corr_label(self, corr: float) -> str:
        if corr >= CORRELATION_HIGH_THRESHOLD:
            return "持仓间高度正相关，分散化效果差"
        if corr >= CORRELATION_MODERATE_THRESHOLD:
            return "持仓间中度相关"
        return "持仓间相关性较低，分散化良好"

    def _percentile(self, sorted_data: list[float], p: float) -> float:
        n = len(sorted_data)
        if n == 0:
            return 0.0
        idx = int(n * p)
        idx = max(0, min(n - 1, idx))
        return sorted_data[idx]

    def _cvar(self, sorted_data: list[float], var: float) -> float:
        tail = [r for r in sorted_data if r <= var]
        if not tail:
            return var
        return sum(tail) / len(tail)
