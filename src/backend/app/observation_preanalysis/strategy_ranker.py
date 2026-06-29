import logging
from dataclasses import dataclass, field

from app.observation_preanalysis.strategy_batch_runner import BatchResult, StrategyPerformanceSnapshot

logger = logging.getLogger(__name__)


@dataclass
class RankedStrategy:
    rank: int
    symbol: str
    name: str
    signal: str
    signal_label: str
    confidence: float
    action: str
    action_label: str
    sharpe_estimate: float
    drawdown_stability: float
    ic_consistency: float
    composite_score: float


@dataclass
class RankedStrategyList:
    window: str
    strategies: list[RankedStrategy] = field(default_factory=list)
    top_pick: str = ""
    top_pick_confidence: float = 0.0
    ranking_summary: str = ""

    @property
    def count(self) -> int:
        return len(self.strategies)

    @property
    def strong_buy_count(self) -> int:
        return sum(1 for s in self.strategies if s.signal == "STRONG_BUY")


class StrategyRanker:

    def rank(self, batch_result: BatchResult) -> RankedStrategyList:
        logger.info("Ranking %d strategies for window [%s]", batch_result.total_count, batch_result.window)

        ranked = []
        for snapshot in batch_result.snapshots:
            sharpe = self._estimate_sharpe(snapshot)
            stability = self._compute_drawdown_stability(snapshot)
            ic = self._compute_ic_consistency(snapshot)
            composite = sharpe * 0.4 + stability * 0.3 + ic * 0.3

            ranked.append(RankedStrategy(
                rank=0,
                symbol=snapshot.symbol,
                name=snapshot.name,
                signal=snapshot.signal,
                signal_label=snapshot.signal_label,
                confidence=snapshot.confidence,
                action=snapshot.action,
                action_label=snapshot.action_label,
                sharpe_estimate=round(sharpe, 3),
                drawdown_stability=round(stability, 3),
                ic_consistency=round(ic, 3),
                composite_score=round(composite, 3),
            ))

        ranked.sort(key=lambda s: s.composite_score, reverse=True)

        for i, s in enumerate(ranked):
            s.rank = i + 1

        top = ranked[0] if ranked else None

        strong_buys = sum(1 for s in ranked if s.signal == "STRONG_BUY")
        buys = sum(1 for s in ranked if s.signal in ("STRONG_BUY", "BUY"))
        summary = (
            f"共 {len(ranked)} 只标的参与排名，"
            f"多头信号 {buys} 只 (其中强买 {strong_buys})，"
            f"首位 {top.symbol} ({top.name}) 综合得分 {top.composite_score}"
        ) if top else "无策略数据参与排名"

        return RankedStrategyList(
            window=batch_result.window,
            strategies=ranked,
            top_pick=f"{top.symbol} {top.name}" if top else "",
            top_pick_confidence=top.confidence if top else 0.0,
            ranking_summary=summary,
        )

    @staticmethod
    def _estimate_sharpe(snapshot: StrategyPerformanceSnapshot) -> float:
        confidence = snapshot.confidence / 100.0
        signal_strength = 0.0
        signal_map = {
            "STRONG_BUY": 1.0, "BUY": 0.7, "NEUTRAL": 0.5, "SELL": 0.3, "STRONG_SELL": 0.0,
        }
        signal_strength = signal_map.get(snapshot.signal, 0.5)
        return round(confidence * signal_strength * 2.0, 3)

    @staticmethod
    def _compute_drawdown_stability(snapshot: StrategyPerformanceSnapshot) -> float:
        confidence = snapshot.confidence / 100.0
        if snapshot.signal in ("STRONG_BUY", "STRONG_SELL"):
            confidence *= 0.85
        elif snapshot.signal == "NEUTRAL":
            confidence *= 0.95
        return round(confidence, 3)

    @staticmethod
    def _compute_ic_consistency(snapshot: StrategyPerformanceSnapshot) -> float:
        base = snapshot.confidence / 100.0
        if snapshot.signal in ("STRONG_BUY", "BUY"):
            base *= 1.0
        elif snapshot.signal == "NEUTRAL":
            base *= 0.6
        else:
            base *= 0.4
        return round(base, 3)
