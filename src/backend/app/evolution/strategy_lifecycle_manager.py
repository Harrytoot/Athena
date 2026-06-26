import math
from dataclasses import dataclass, field

from app.evolution.strategy_decay_analyzer import StrategyDecayReport, StrategyDecaySignal
from app.portfolio.portfolio_engine import StrategyInput

LIFECYCLE_STAGES = ["early", "mature", "decaying", "terminal"]


@dataclass
class LifecycleClassification:
    strategy_id: str
    stage: str
    maturity_score: float
    trend_score: float
    stability_score: float
    expected_remaining_life_days: float
    transition_signals: list[str]
    recommendation: str


@dataclass
class LifecycleReport:
    classifications: list[LifecycleClassification] = field(default_factory=list)
    portfolio_lifecycle_phase: str = ""
    renewal_urgency: float = 0.0
    early_count: int = 0
    mature_count: int = 0
    decaying_count: int = 0
    terminal_count: int = 0
    assessment: str = ""

    @property
    def needs_renewal(self) -> bool:
        return self.renewal_urgency >= 0.5


class StrategyLifecycleManager:

    def __init__(
        self,
        maturity_min_sharpe: float = 0.5,
        decay_stability_threshold: float = 0.3,
        terminal_decay_threshold: float = 0.7,
        early_max_days: int = 90,
    ):
        self.maturity_min_sharpe = maturity_min_sharpe
        self.decay_stability_threshold = decay_stability_threshold
        self.terminal_decay_threshold = terminal_decay_threshold
        self.early_max_days = early_max_days

    def classify(
        self,
        strategies: list[StrategyInput],
        decay_report: StrategyDecayReport | None = None,
    ) -> LifecycleReport:
        if not strategies:
            return LifecycleReport(assessment="无策略数据")

        decay_map: dict[str, StrategyDecaySignal] = {}
        if decay_report:
            for ds in decay_report.decay_signals:
                decay_map[ds.strategy_id] = ds

        classifications: list[LifecycleClassification] = []
        for s in strategies:
            ds = decay_map.get(s.strategy_id)
            classification = self._classify_single(s, ds)
            classifications.append(classification)

        stages_count = {"early": 0, "mature": 0, "decaying": 0, "terminal": 0}
        for c in classifications:
            stages_count[c.stage] = stages_count.get(c.stage, 0) + 1

        portfolio_phase = self._determine_portfolio_phase(classifications)
        renewal_urgency = self._compute_renewal_urgency(classifications)
        assessment = self._assess_lifecycle(classifications, portfolio_phase, renewal_urgency)

        return LifecycleReport(
            classifications=classifications,
            portfolio_lifecycle_phase=portfolio_phase,
            renewal_urgency=round(renewal_urgency, 4),
            early_count=stages_count["early"],
            mature_count=stages_count["mature"],
            decaying_count=stages_count["decaying"],
            terminal_count=stages_count["terminal"],
            assessment=assessment,
        )

    def _classify_single(
        self,
        strategy: StrategyInput,
        decay_signal: StrategyDecaySignal | None,
    ) -> LifecycleClassification:
        perf = strategy.performance
        strategy_id = strategy.strategy_id

        maturity_score = self._compute_maturity_score(perf, strategy)

        trend_score = 0.5
        if decay_signal:
            trend_score = 1.0 - decay_signal.decay_score
        else:
            if perf.sharpe_ratio > 1.0:
                trend_score = 0.8
            elif perf.sharpe_ratio > 0.5:
                trend_score = 0.6
            elif perf.sharpe_ratio > 0.0:
                trend_score = 0.4
            else:
                trend_score = 0.2

        stability_score = 0.5
        if strategy.validation and strategy.validation.stability_score > 0:
            stability_score = strategy.validation.stability_score
        elif strategy.robustness:
            stability_score = strategy.robustness.overall_stability_score

        stage = self._determine_stage(
            perf, decay_signal, maturity_score, trend_score, stability_score
        )

        remaining_life = self._estimate_remaining_life(
            stage, decay_signal, perf
        )

        transition_signals = self._detect_transition_signals(
            stage, decay_signal, perf
        )

        recommendation = self._generate_recommendation(
            stage, strategy_id, maturity_score, transition_signals
        )

        return LifecycleClassification(
            strategy_id=strategy_id,
            stage=stage,
            maturity_score=round(maturity_score, 4),
            trend_score=round(trend_score, 4),
            stability_score=round(stability_score, 4),
            expected_remaining_life_days=round(remaining_life, 1),
            transition_signals=transition_signals,
            recommendation=recommendation,
        )

    def _compute_maturity_score(
        self,
        perf,
        strategy: StrategyInput,
    ) -> float:
        scores: list[float] = []

        if perf.sharpe_ratio >= 1.5:
            scores.append(1.0)
        elif perf.sharpe_ratio >= 0.8:
            scores.append(0.7)
        elif perf.sharpe_ratio >= 0.3:
            scores.append(0.4)
        elif perf.sharpe_ratio >= 0.0:
            scores.append(0.2)
        else:
            scores.append(0.0)

        if perf.win_rate >= 0.6:
            scores.append(1.0)
        elif perf.win_rate >= 0.5:
            scores.append(0.7)
        elif perf.win_rate >= 0.4:
            scores.append(0.4)
        else:
            scores.append(0.1)

        if perf.total_days > 0:
            days_score = min(1.0, perf.total_days / 252.0)
            scores.append(days_score)
        else:
            scores.append(0.0)

        stability = 0.5
        if strategy.robustness:
            stability = strategy.robustness.overall_stability_score
        scores.append(stability)

        return sum(scores) / len(scores) if scores else 0.0

    def _determine_stage(
        self,
        perf,
        decay_signal: StrategyDecaySignal | None,
        maturity_score: float,
        trend_score: float,
        stability_score: float,
    ) -> str:
        if decay_signal and decay_signal.decay_score >= self.terminal_decay_threshold:
            return "terminal"

        if decay_signal and decay_signal.decay_score >= 0.5:
            return "decaying"

        if perf.sharpe_ratio < 0 and trend_score < 0.3:
            return "decaying"

        if perf.total_days < self.early_max_days and maturity_score < 0.5:
            return "early"

        if maturity_score >= 0.6 and trend_score >= 0.5 and stability_score >= 0.4:
            return "mature"

        if maturity_score >= 0.4:
            if trend_score < 0.3:
                return "decaying"
            return "mature"

        if trend_score >= 0.5:
            return "early"
        else:
            return "decaying"

    def _estimate_remaining_life(
        self,
        stage: str,
        decay_signal: StrategyDecaySignal | None,
        perf,
    ) -> float:
        if stage == "terminal":
            return 0.0

        if stage == "early":
            return 365.0

        if stage == "mature":
            if decay_signal and 0 < decay_signal.alpha_half_life_days < 3650:
                return decay_signal.alpha_half_life_days * 10.0
            return 730.0

        if stage == "decaying":
            if decay_signal and 0 < decay_signal.alpha_half_life_days < 3650:
                return decay_signal.alpha_half_life_days * 3.0
            return 180.0

        return 90.0

    def _detect_transition_signals(
        self,
        stage: str,
        decay_signal: StrategyDecaySignal | None,
        perf,
    ) -> list[str]:
        signals: list[str] = []

        if stage == "early":
            if perf.sharpe_ratio > self.maturity_min_sharpe:
                signals.append("夏普比率已超过成熟阈值，即将进入成熟期")
            if perf.total_days >= self.early_max_days:
                signals.append("观测天数已满足过渡条件")

        elif stage == "mature":
            if decay_signal:
                if decay_signal.decay_score > 0.3:
                    signals.append("衰减信号出现，注意观察是否进入衰退期")
                if decay_signal.sharpe_trend < -0.001:
                    signals.append("夏普趋势转负，可能存在衰退风险")
            if perf.sharpe_ratio < 0.3:
                signals.append("夏普比率下降至低位，关注策略有效性")

        elif stage == "decaying":
            if decay_signal and decay_signal.decay_score > 0.6:
                signals.append("衰减加剧，需考虑策略替换或停止")
            if perf.sharpe_ratio < -0.2:
                signals.append("夏普比率严重为负，接近终止期")

        elif stage == "terminal":
            signals.append("策略已进入终止状态，建议立即替换或停用")

        return signals

    def _generate_recommendation(
        self,
        stage: str,
        strategy_id: str,
        maturity_score: float,
        transition_signals: list[str],
    ) -> str:
        if stage == "early":
            return f"策略 {strategy_id}: 处于早期阶段，继续监控和积累数据，适度配置"

        if stage == "mature":
            if transition_signals:
                return f"策略 {strategy_id}: 成熟但出现过渡信号，保持权重并密切监控"
            return f"策略 {strategy_id}: 处于成熟期，核心配置，维持当前权重"

        if stage == "decaying":
            return f"策略 {strategy_id}: 处于衰退期，建议逐步降低权重并准备替换方案"

        return f"策略 {strategy_id}: 处于终止期，建议立即替换或停用该策略"

    def _determine_portfolio_phase(
        self, classifications: list[LifecycleClassification]
    ) -> str:
        n = len(classifications)
        if n == 0:
            return "unknown"

        mature_ratio = sum(1 for c in classifications if c.stage == "mature") / n
        decaying_ratio = sum(1 for c in classifications if c.stage in ("decaying", "terminal")) / n
        early_ratio = sum(1 for c in classifications if c.stage == "early") / n

        if mature_ratio >= 0.6:
            return "成熟组合"
        if mature_ratio >= 0.4 and early_ratio >= 0.2:
            return "成长组合"
        if decaying_ratio >= 0.5:
            return "衰退组合"
        if early_ratio >= 0.6:
            return "早期组合"
        if mature_ratio >= 0.3 and decaying_ratio < 0.4:
            return "稳定组合"
        return "过渡组合"

    def _compute_renewal_urgency(
        self, classifications: list[LifecycleClassification]
    ) -> float:
        n = len(classifications)
        if n == 0:
            return 0.0

        urgency = 0.0
        for c in classifications:
            if c.stage == "terminal":
                urgency += 1.0
            elif c.stage == "decaying":
                urgency += 0.6
            elif c.stage == "early":
                urgency += 0.1
            else:
                urgency += 0.0

        return urgency / n

    def _assess_lifecycle(
        self,
        classifications: list[LifecycleClassification],
        portfolio_phase: str,
        renewal_urgency: float,
    ) -> str:
        parts: list[str] = []

        parts.append(f"组合阶段: {portfolio_phase}")

        early = sum(1 for c in classifications if c.stage == "early")
        mature = sum(1 for c in classifications if c.stage == "mature")
        decaying = sum(1 for c in classifications if c.stage == "decaying")
        terminal = sum(1 for c in classifications if c.stage == "terminal")

        parts.append(f"早期:{early} 成熟:{mature} 衰退:{decaying} 终止:{terminal}")

        if renewal_urgency >= 0.7:
            parts.append("更新紧迫度: 高 (需立即采取行动)")
        elif renewal_urgency >= 0.5:
            parts.append("更新紧迫度: 中 (建议近期更新)")
        elif renewal_urgency >= 0.3:
            parts.append("更新紧迫度: 低 (可计划性更新)")
        else:
            parts.append("更新紧迫度: 极低 (当前策略状态良好)")

        return " | ".join(parts)
