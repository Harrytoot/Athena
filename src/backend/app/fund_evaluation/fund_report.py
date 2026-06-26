import math
from dataclasses import dataclass, field

from app.portfolio.portfolio_engine import (
    PortfolioReport,
    StrategyInput,
)
from app.portfolio.rebalancer import RebalanceResult

from app.fund_evaluation.portfolio_metrics import (
    PortfolioMetricsAnalyzer,
    PortfolioStabilityMetrics,
)
from app.fund_evaluation.strategy_correlation import (
    StrategyCorrelationAnalyzer,
    StrategyCorrelationResult,
)
from app.fund_evaluation.regime_fund_analysis import (
    FundRegimeAnalyzer,
    FundRegimeResult,
)
from app.fund_evaluation.drawdown_analyzer import (
    DrawdownAnalysisResult,
    DrawdownAnalyzer,
)


@dataclass
class MultiStrategyUplift:
    portfolio_sharpe: float = 0.0
    best_single_sharpe: float = 0.0
    avg_single_sharpe: float = 0.0
    sharpe_uplift_vs_best: float = 0.0
    sharpe_uplift_vs_avg: float = 0.0
    portfolio_max_dd: float = 0.0
    worst_single_max_dd: float = 0.0
    avg_single_max_dd: float = 0.0
    dd_improvement_vs_worst: float = 0.0
    dd_improvement_vs_avg: float = 0.0
    portfolio_win_rate: float = 0.0
    avg_single_win_rate: float = 0.0
    win_rate_improvement: float = 0.0
    diversification_benefit: float = 0.0


@dataclass
class FundEvaluationReport:
    stability: PortfolioStabilityMetrics = field(default_factory=PortfolioStabilityMetrics)
    correlation: StrategyCorrelationResult = field(default_factory=StrategyCorrelationResult)
    drawdown: DrawdownAnalysisResult = field(default_factory=DrawdownAnalysisResult)
    regime: FundRegimeResult = field(default_factory=FundRegimeResult)
    uplift: MultiStrategyUplift = field(default_factory=MultiStrategyUplift)
    overall_score: float = 0.0
    assessment: str = ""
    risk_flags: list[str] = field(default_factory=list)


class FundReportGenerator:

    def __init__(
        self,
        rolling_window: int = 60,
        risk_free_rate: float = 0.02,
        regime_lookback: int = 60,
        cluster_gap_threshold: int = 10,
    ):
        self.metrics_analyzer = PortfolioMetricsAnalyzer(
            window_size=rolling_window,
            risk_free_rate=risk_free_rate,
        )
        self.correlation_analyzer = StrategyCorrelationAnalyzer()
        self.regime_analyzer = FundRegimeAnalyzer(lookback=regime_lookback)
        self.drawdown_analyzer = DrawdownAnalyzer(cluster_gap_threshold=cluster_gap_threshold)
        self.risk_free_rate = risk_free_rate

    def generate(
        self,
        strategies: list[StrategyInput],
        portfolio_report: PortfolioReport,
        rebalance_logs: list[RebalanceResult] | None = None,
    ) -> FundEvaluationReport:
        if not strategies or not portfolio_report.is_ready:
            return FundEvaluationReport()

        weights = portfolio_report.composition.weight_result.normalized_weights
        if not weights or len(weights) != len(strategies):
            weights = [1.0 / len(strategies)] * len(strategies)

        stability = self.metrics_analyzer.analyze(strategies, weights)

        correlation = self.correlation_analyzer.analyze(strategies)

        drawdown = self.drawdown_analyzer.analyze(strategies, weights)

        regime = self.regime_analyzer.analyze(
            strategies, weights, self.risk_free_rate
        )

        uplift = self._compute_uplift(strategies, portfolio_report, drawdown, correlation, stability)

        overall_score = self._compute_overall_score(
            stability, correlation, drawdown, regime, uplift
        )

        risk_flags = self._check_risk_flags(
            stability, correlation, drawdown, regime, uplift
        )

        assessment = self._assess(
            overall_score, stability, correlation, drawdown, regime, uplift
        )

        return FundEvaluationReport(
            stability=stability,
            correlation=correlation,
            drawdown=drawdown,
            regime=regime,
            uplift=uplift,
            overall_score=round(overall_score, 4),
            assessment=assessment,
            risk_flags=risk_flags,
        )

    def _compute_uplift(
        self,
        strategies: list[StrategyInput],
        portfolio_report: PortfolioReport,
        drawdown: DrawdownAnalysisResult,
        correlation: StrategyCorrelationResult,
        stability: PortfolioStabilityMetrics,
    ) -> MultiStrategyUplift:
        sharpes = [s.performance.sharpe_ratio for s in strategies]
        max_dds = [s.performance.max_drawdown for s in strategies]
        win_rates = [s.performance.win_rate for s in strategies]

        best_sharpe = max(sharpes) if sharpes else 0.0
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.0
        worst_dd = min(max_dds) if max_dds else 0.0
        avg_dd = sum(max_dds) / len(max_dds) if max_dds else 0.0
        avg_wr = sum(win_rates) / len(win_rates) if win_rates else 0.0

        port_sharpe = portfolio_report.metrics.expected_sharpe
        port_dd = drawdown.max_drawdown
        port_wr = stability.positive_day_ratio

        sharpe_vs_best = (port_sharpe / best_sharpe - 1.0) if best_sharpe != 0 else 0.0
        sharpe_vs_avg = (port_sharpe / avg_sharpe - 1.0) if avg_sharpe != 0 else 0.0

        dd_vs_worst = (1.0 - abs(port_dd) / abs(worst_dd)) if worst_dd != 0 else 0.0
        dd_vs_avg = (1.0 - abs(port_dd) / abs(avg_dd)) if avg_dd != 0 else 0.0

        wr_improve = port_wr - avg_wr

        div_benefit = portfolio_report.metrics.diversification_ratio - 1.0

        return MultiStrategyUplift(
            portfolio_sharpe=round(port_sharpe, 6),
            best_single_sharpe=round(best_sharpe, 6),
            avg_single_sharpe=round(avg_sharpe, 6),
            sharpe_uplift_vs_best=round(sharpe_vs_best, 6),
            sharpe_uplift_vs_avg=round(sharpe_vs_avg, 6),
            portfolio_max_dd=round(port_dd, 6),
            worst_single_max_dd=round(worst_dd, 6),
            avg_single_max_dd=round(avg_dd, 6),
            dd_improvement_vs_worst=round(dd_vs_worst, 6),
            dd_improvement_vs_avg=round(dd_vs_avg, 6),
            portfolio_win_rate=round(port_wr, 6),
            avg_single_win_rate=round(avg_wr, 6),
            win_rate_improvement=round(wr_improve, 6),
            diversification_benefit=round(div_benefit, 6),
        )

    def _compute_overall_score(
        self,
        stability: PortfolioStabilityMetrics,
        correlation: StrategyCorrelationResult,
        drawdown: DrawdownAnalysisResult,
        regime: FundRegimeResult,
        uplift: MultiStrategyUplift,
    ) -> float:
        scores: list[float] = []

        stability_component = stability.sharpe_stability
        scores.append(stability_component * 0.25)

        corr_component = 0.0
        if correlation.correlation_matrix.strategy_ids:
            avg_corr = correlation.avg_pairwise_corr
            corr_component = max(0.0, 1.0 - abs(avg_corr)) * 0.20
        else:
            corr_component = 0.10
        scores.append(corr_component)

        tail_component = 0.0
        if drawdown.tail_risk.tail_ratio > 0:
            tail_component = min(1.0, drawdown.tail_risk.tail_ratio) * 0.20
        else:
            tail_component = 0.05
        scores.append(tail_component)

        dd_component = 0.0
        if drawdown.max_drawdown < 0:
            dd_component = max(0.0, 1.0 + drawdown.max_drawdown) * 0.20
        else:
            dd_component = 0.20
        scores.append(dd_component)

        regime_component = regime.regime_consistency * 0.15
        scores.append(regime_component)

        uplift_component = 0.0
        if uplift.sharpe_uplift_vs_avg > 0:
            uplift_component = min(0.20, uplift.sharpe_uplift_vs_avg * 0.5)
        scores.append(uplift_component)

        total = sum(scores)
        return round(min(1.0, max(0.0, total)), 4)

    def _check_risk_flags(
        self,
        stability: PortfolioStabilityMetrics,
        correlation: StrategyCorrelationResult,
        drawdown: DrawdownAnalysisResult,
        regime: FundRegimeResult,
        uplift: MultiStrategyUplift,
    ) -> list[str]:
        flags: list[str] = []

        if stability.sharpe_stability < 0.3:
            flags.append("Sharpe ratio unstable (stability < 0.3)")

        if correlation.avg_pairwise_corr > 0.7:
            flags.append("High strategy correlation (>0.7)")

        if drawdown.max_drawdown < -0.25:
            flags.append("Severe max drawdown (>25%)")

        if drawdown.clustering_score > 0.5:
            flags.append("Drawdown clustering detected")

        if drawdown.tail_risk.cvar_95 < -0.03:
            flags.append("High tail risk (CVaR 95%)")

        if regime.regime_consistency < 0.3:
            flags.append("Low regime consistency")

        if uplift.sharpe_uplift_vs_best < -0.1:
            flags.append("Negative Sharpe uplift vs best single strategy")

        if stability.annualized_sharpe < 0:
            flags.append("Negative portfolio Sharpe ratio")

        return flags

    def _assess(
        self,
        overall_score: float,
        stability: PortfolioStabilityMetrics,
        correlation: StrategyCorrelationResult,
        drawdown: DrawdownAnalysisResult,
        regime: FundRegimeResult,
        uplift: MultiStrategyUplift,
    ) -> str:
        parts: list[str] = []

        if overall_score >= 0.8:
            parts.append("基金评估: 优秀")
        elif overall_score >= 0.6:
            parts.append("基金评估: 良好")
        elif overall_score >= 0.4:
            parts.append("基金评估: 一般")
        else:
            parts.append("基金评估: 较差")

        if stability.sharpe_stability >= 0.7:
            parts.append("夏普稳定性: 高")
        elif stability.sharpe_stability >= 0.4:
            parts.append("夏普稳定性: 中")
        else:
            parts.append("夏普稳定性: 低")

        corr_level = "高" if correlation.avg_pairwise_corr > 0.5 else "中" if correlation.avg_pairwise_corr > 0.2 else "低"
        parts.append(f"策略相关性: {corr_level} ({correlation.avg_pairwise_corr:.3f})")

        if drawdown.max_drawdown > -0.10:
            parts.append("最大回撤: 轻度")
        elif drawdown.max_drawdown > -0.20:
            parts.append("最大回撤: 中度")
        else:
            parts.append("最大回撤: 严重")

        if uplift.sharpe_uplift_vs_best > 0:
            parts.append(f"多策略提升: 正 ({uplift.sharpe_uplift_vs_best:+.1%})")
        elif uplift.sharpe_uplift_vs_avg > 0:
            parts.append(f"多策略提升: 优于均值 ({uplift.sharpe_uplift_vs_avg:+.1%})")
        else:
            parts.append("多策略提升: 无")

        regime_stability = "高" if regime.regime_consistency >= 0.7 else "中" if regime.regime_consistency >= 0.4 else "低"
        parts.append(f"跨周期一致性: {regime_stability}")

        return " | ".join(parts)
