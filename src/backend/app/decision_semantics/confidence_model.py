from app.decision_semantics.schema import (
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ExecutionSemantic,
)


WEIGHT_SIGNAL_STRENGTH = 0.30
WEIGHT_FACTOR_CONSISTENCY = 0.25
WEIGHT_SCENARIO_STABILITY = 0.25
WEIGHT_RISK_PENALTY = 0.20
WEIGHT_EXECUTION_FEASIBILITY = 0.10


class ConfidenceModel:

    def __init__(
        self,
        w_signal: float = WEIGHT_SIGNAL_STRENGTH,
        w_factor: float = WEIGHT_FACTOR_CONSISTENCY,
        w_scenario: float = WEIGHT_SCENARIO_STABILITY,
        w_risk: float = WEIGHT_RISK_PENALTY,
        w_execution: float = WEIGHT_EXECUTION_FEASIBILITY,
    ):
        total = w_signal + w_factor + w_scenario + w_risk + w_execution
        self._w_signal = w_signal / total
        self._w_factor = w_factor / total
        self._w_scenario = w_scenario / total
        self._w_risk = w_risk / total
        self._w_execution = w_execution / total

    def compute(
        self,
        signal: SignalSemantic,
        factors: list[FactorSemantic],
        scenario: ScenarioSemantic | None = None,
        risk: RiskSemantic | None = None,
        execution: ExecutionSemantic | None = None,
    ) -> float:
        signal_score = signal.strength
        factor_score = self._factor_consistency(factors, signal.direction)
        scenario_score = scenario.stability_score if scenario else 0.5
        risk_penalty = self._risk_penalty(risk) if risk else 0.0
        execution_score = execution.feasibility if execution else 0.5

        confidence = (
            self._w_signal * signal_score
            + self._w_factor * factor_score
            + self._w_scenario * scenario_score
            + self._w_risk * (1.0 - risk_penalty)
            + self._w_execution * execution_score
        )
        return round(max(0.0, min(1.0, confidence)), 4)

    def _factor_consistency(self, factors: list[FactorSemantic], direction: str) -> float:
        if not factors:
            return 0.5
        if direction == "NEUTRAL":
            neutral_count = sum(
                1 for f in factors if 40.0 <= f.value <= 60.0
            )
            return neutral_count / len(factors)
        expected_bullish = direction == "LONG"
        agreeing = sum(
            1 for f in factors if f.is_bullish == expected_bullish
        )
        return agreeing / len(factors)

    def _risk_penalty(self, risk: RiskSemantic) -> float:
        level_scores = {"HIGH": 1.0, "MODERATE": 0.5, "LOW": 0.0}
        base_penalty = level_scores.get(risk.overall_level, 0.5)
        scenario_adj = risk.scenario_vulnerability * 0.3
        drawdown_adj = risk.drawdown_risk * 0.3
        volatility_adj = risk.volatility_risk * 0.2
        correlation_adj = risk.correlation_risk * 0.2
        return round(
            base_penalty * 0.5
            + scenario_adj
            + drawdown_adj
            + volatility_adj
            + correlation_adj,
            4,
        )
