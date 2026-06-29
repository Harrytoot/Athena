import logging

from app.feature_store.repository import FeatureItem
from app.decision_semantics.schema import (
    ConsistencyReport,
    ContradictionEntry,
    DecisionSemantic,
    ExecutionSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    SignalSemantic,
)
from app.decision_semantics.runtime.semantic_runtime_engine import SemanticRuntimeEngine

logger = logging.getLogger(__name__)

SIGNAL_THRESHOLD_LONG = 65.0
SIGNAL_THRESHOLD_SHORT = 35.0


class RuntimeBridge:

    def __init__(self, runtime: SemanticRuntimeEngine | None = None):
        self._runtime = runtime or SemanticRuntimeEngine()

    async def map_and_trigger(
        self, features: list[FeatureItem], symbol: str
    ) -> DecisionSemantic | None:
        symbol_features = [f for f in features if f.name.startswith(f"{symbol}:")]
        if not symbol_features:
            return None

        factors = self._build_factors(symbol_features)
        signal = self._build_signal(factors)
        risk = self._build_risk(factors)
        scenario = self._build_scenario()
        execution = self._build_execution()
        consistency = self._build_consistency(signal, risk)
        confidence = self._compute_confidence(signal, factors, risk, execution)
        action, action_label = self._determine_action(signal, risk, confidence)

        semantic = DecisionSemantic(
            symbol=symbol,
            name=f"{symbol}_realtime",
            signal=signal,
            factors=factors,
            risk=risk,
            scenario=scenario,
            execution=execution,
            confidence_score=confidence,
            consistency=consistency,
            action=action,
            action_label=action_label,
            summary=(
                f"Real-time decision for {symbol}: "
                f"{action_label} (confidence: {confidence:.2f})"
            ),
            semantic_version="1.0.0",
        )

        try:
            self._runtime.update(symbol, semantic)
        except ValueError:
            self._runtime.initialize(symbol, semantic)

        logger.info(
            "RuntimeBridge triggered for %s: action=%s confidence=%.2f",
            symbol, action, confidence,
        )
        return semantic

    def get_runtime(self) -> SemanticRuntimeEngine:
        return self._runtime

    def _build_factors(self, features: list[FeatureItem]) -> list[FactorSemantic]:
        factors: list[FactorSemantic] = []
        labels = {
            "price_momentum": "价格动量",
            "volume_spike": "成交量异动",
            "bid_ask_spread": "买卖价差",
            "intraday_volatility": "盘中波动",
        }
        for f in features:
            short_name = f.name.split(":")[-1] if ":" in f.name else f.name
            label = labels.get(short_name, short_name)
            if short_name == "intraday_volatility":
                is_bullish = f.value < 50.0
            else:
                is_bullish = f.value > 50.0
            if is_bullish:
                assessment = "偏多"
            elif f.value < 30.0:
                assessment = "偏空"
            else:
                assessment = "中性"
            factors.append(FactorSemantic(
                name=short_name,
                label=label,
                value=f.value,
                weight=0.25,
                contribution=round(f.value * 0.25, 2),
                is_bullish=is_bullish,
                assessment=assessment,
            ))
        return factors

    def _build_signal(self, factors: list[FactorSemantic]) -> SignalSemantic:
        if not factors:
            return SignalSemantic(
                direction="NEUTRAL",
                direction_label="中性",
                strength=50.0,
                base_confidence=0.5,
            )

        bullish_count = sum(1 for f in factors if f.is_bullish)
        bearish_count = len(factors) - bullish_count

        if bullish_count > bearish_count:
            direction = "LONG"
            direction_label = "看多"
        elif bearish_count > bullish_count:
            direction = "SHORT"
            direction_label = "看空"
        else:
            direction = "NEUTRAL"
            direction_label = "中性"

        avg_value = sum(f.value for f in factors) / len(factors)
        strength = round(avg_value, 2)
        base_confidence = round(0.5 + abs(bullish_count - bearish_count) * 0.15, 2)

        return SignalSemantic(
            direction=direction,
            direction_label=direction_label,
            strength=strength,
            base_confidence=base_confidence,
        )

    @staticmethod
    def _build_risk(factors: list[FactorSemantic]) -> RiskSemantic:
        volatility_item = next((f for f in factors if f.name == "intraday_volatility"), None)
        vol_risk = volatility_item.value / 100.0 if volatility_item else 0.5

        drawdown_risk = round(vol_risk * 0.8, 2)
        correlation_risk = 0.3
        scenario_vulnerability = round(vol_risk * 0.6, 2)

        overall = "high" if vol_risk > 0.7 else "medium" if vol_risk > 0.4 else "low"
        warnings = []
        if vol_risk > 0.7:
            warnings.append("高波动警告")
        if drawdown_risk > 0.6:
            warnings.append("回撤风险较高")

        return RiskSemantic(
            overall_level=overall,
            drawdown_risk=drawdown_risk,
            volatility_risk=round(vol_risk, 2),
            correlation_risk=correlation_risk,
            scenario_vulnerability=scenario_vulnerability,
            warnings=warnings,
        )

    @staticmethod
    def _build_scenario() -> ScenarioSemantic:
        return ScenarioSemantic(
            stability_score=0.8,
            worst_case_score_change=-5.0,
            state_change_count=0,
        )

    @staticmethod
    def _build_execution() -> ExecutionSemantic:
        return ExecutionSemantic(
            feasibility=0.9,
            estimated_slippage_bps=5.0,
            estimated_fill_rate=0.95,
            quality_grade="A",
        )

    @staticmethod
    def _build_consistency(signal: SignalSemantic, risk: RiskSemantic) -> ConsistencyReport:
        contradictions: list[ContradictionEntry] = []
        if signal.direction == "LONG" and risk.overall_level == "high":
            contradictions.append(ContradictionEntry(
                contradiction_type="signal_vs_risk",
                severity="medium",
                description="看多信号与高风险水平存在矛盾",
            ))
        if signal.direction == "SHORT" and risk.overall_level == "low":
            contradictions.append(ContradictionEntry(
                contradiction_type="signal_vs_risk",
                severity="low",
                description="看空信号与低风险水平略有不一致",
            ))

        is_consistent = len(contradictions) == 0
        consistency_score = 1.0 - len(contradictions) * 0.15
        return ConsistencyReport(
            is_consistent=is_consistent,
            contradictions=contradictions,
            consistency_score=round(consistency_score, 2),
        )

    @staticmethod
    def _compute_confidence(
        signal: SignalSemantic,
        factors: list[FactorSemantic],
        risk: RiskSemantic,
        execution: ExecutionSemantic,
    ) -> float:
        signal_component = signal.base_confidence * 0.30
        factor_component = (sum(f.value for f in factors) / max(len(factors), 1)) / 100 * 0.25
        risk_component = (1.0 - risk.volatility_risk) * 0.25
        execution_component = execution.feasibility * 0.20

        return round(signal_component + factor_component + risk_component + execution_component, 2)

    @staticmethod
    def _determine_action(
        signal: SignalSemantic, risk: RiskSemantic, confidence: float
    ) -> tuple[str, str]:
        if confidence < 0.3:
            return "HOLD", "观望"
        if signal.direction == "LONG" and risk.overall_level != "high":
            return "BUY", "买入"
        if signal.direction == "SHORT" and risk.overall_level != "low":
            return "SELL", "卖出"
        return "HOLD", "持有"
