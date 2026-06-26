from dataclasses import dataclass, field

from app.backtest_engine.dataset_builder import BacktestDataset
from app.backtest_engine.metrics import information_coefficient, rank_information_coefficient
from app.strategy_validation.ic_analyzer import ICAnalyzer, RollingICReport
from app.strategy_validation.regime_detector import RegimeDetector, RegimeReport, _map_regime
from app.strategy_validation.signal_decay import DecayReport, SignalDecayAnalyzer


@dataclass
class RegimePerformance:
    regime: str
    ic_5d: float
    ic_10d: float
    ic_20d: float
    rank_ic_5d: float
    rank_ic_10d: float
    rank_ic_20d: float
    n_observations: int


@dataclass
class StrategyValidationReport:
    ic_rolling: list[RollingICReport] = field(default_factory=list)
    decay: DecayReport = field(default_factory=DecayReport)
    regime: RegimeReport = field(default_factory=RegimeReport)
    regime_performance: list[RegimePerformance] = field(default_factory=list)
    stability_score: float = 0.0
    overall_assessment: str = ""


class PerformanceReportGenerator:

    def __init__(
        self,
        ic_window_size: int = 20,
        regime_min_segment: int = 5,
    ):
        self.ic_analyzer = ICAnalyzer(window_size=ic_window_size)
        self.regime_detector = RegimeDetector(min_segment_days=regime_min_segment)
        self.decay_analyzer = SignalDecayAnalyzer()

    def generate(self, dataset: BacktestDataset) -> StrategyValidationReport:
        ic_reports = self.ic_analyzer.analyze(dataset)
        decay_report = self.decay_analyzer.analyze(dataset)
        regime_report = self.regime_detector.detect(dataset)
        regime_perf = self._compute_regime_performance(dataset)

        stability = self._compute_stability(ic_reports)
        assessment = self._assess(stability, ic_reports, decay_report)

        return StrategyValidationReport(
            ic_rolling=ic_reports,
            decay=decay_report,
            regime=regime_report,
            regime_performance=regime_perf,
            stability_score=stability,
            overall_assessment=assessment,
        )

    def _compute_regime_performance(
        self, dataset: BacktestDataset
    ) -> list[RegimePerformance]:
        if not dataset.rows:
            return []

        rows = dataset.rows
        regimes = [_map_regime(r.state) for r in rows]
        unique_regimes = sorted(set(regimes))

        result = []
        for regime in unique_regimes:
            indices = [i for i, r in enumerate(regimes) if r == regime]
            if len(indices) < 3:
                continue

            idx_scores = [rows[i].score for i in indices]
            idx_ret5 = [rows[i].forward_return_5d for i in indices]
            idx_ret10 = [rows[i].forward_return_10d for i in indices]
            idx_ret20 = [rows[i].forward_return_20d for i in indices]

            result.append(
                RegimePerformance(
                    regime=regime,
                    ic_5d=information_coefficient(idx_scores, idx_ret5),
                    ic_10d=information_coefficient(idx_scores, idx_ret10),
                    ic_20d=information_coefficient(idx_scores, idx_ret20),
                    rank_ic_5d=rank_information_coefficient(idx_scores, idx_ret5),
                    rank_ic_10d=rank_information_coefficient(idx_scores, idx_ret10),
                    rank_ic_20d=rank_information_coefficient(idx_scores, idx_ret20),
                    n_observations=len(indices),
                )
            )
        return result

    def _compute_stability(self, ic_reports: list[RollingICReport]) -> float:
        all_ics = []
        for report in ic_reports:
            for result in report.results:
                all_ics.append(result.ic)

        if len(all_ics) < 2:
            return 0.0

        mean_ic = sum(all_ics) / len(all_ics)
        if mean_ic == 0:
            return 0.0

        variance = sum((ic - mean_ic) ** 2 for ic in all_ics) / len(all_ics)
        std_ic = variance ** 0.5
        cv = std_ic / abs(mean_ic)
        stability = max(0.0, min(1.0, 1.0 - cv))
        return round(stability, 4)

    def _assess(
        self,
        stability: float,
        ic_reports: list[RollingICReport],
        decay_report: DecayReport,
    ) -> str:
        parts = []

        for report in ic_reports:
            mean_ic = report.mean_ic
            if mean_ic > 0.05:
                parts.append(f"{report.horizon} IC positive ({mean_ic:.4f})")
            elif mean_ic > 0:
                parts.append(f"{report.horizon} IC weakly positive ({mean_ic:.4f})")
            else:
                parts.append(f"{report.horizon} IC negative ({mean_ic:.4f})")

        if stability >= 0.7:
            parts.append(f"High stability ({stability:.2f})")
        elif stability >= 0.4:
            parts.append(f"Moderate stability ({stability:.2f})")
        else:
            parts.append(f"Low stability ({stability:.2f})")

        if decay_report.points:
            parts.append(f"Optimal horizon: {decay_report.optimal_horizon}")

        return " | ".join(parts)
