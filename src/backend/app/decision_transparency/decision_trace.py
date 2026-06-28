import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.market.market_score import MarketScore
from app.strategy.signal_mapper import SizedSignal
from app.strategy.position_sizer import StrategyPosition
from app.strategy.risk_manager import RiskAdjustedPosition

MODEL_VERSION = "1.0.0"
SCORING_ENGINE_VERSION = "1.0.0"


@dataclass
class TraceStep:
    step_order: int
    step_name: str
    input_data: dict
    output_data: dict
    timestamp: datetime
    version: str = MODEL_VERSION


@dataclass
class DecisionTrace:
    trace_id: str
    created_at: datetime
    model_version: str
    scoring_engine_version: str
    steps: list[TraceStep] = field(default_factory=list)
    input_hash: str = ""
    full_lineage: str = ""

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def total_duration_ms(self) -> float | None:
        if len(self.steps) < 2:
            return None
        first = self.steps[0].timestamp
        last = self.steps[-1].timestamp
        return (last - first).total_seconds() * 1000


class DecisionTracer:

    def __init__(
        self,
        model_version: str = MODEL_VERSION,
        scoring_engine_version: str = SCORING_ENGINE_VERSION,
    ):
        self._model_version = model_version
        self._scoring_engine_version = scoring_engine_version
        self._steps: list[TraceStep] = []
        self._order = 0

    def start(self) -> None:
        self._steps = []
        self._order = 0

    def record_step(self, name: str, inputs: dict, outputs: dict) -> None:
        self._order += 1
        self._steps.append(TraceStep(
            step_order=self._order,
            step_name=name,
            input_data=self._sanitize(inputs),
            output_data=self._sanitize(outputs),
            timestamp=datetime.now(timezone.utc),
            version=self._model_version,
        ))

    def build(self) -> DecisionTrace:
        trace_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        all_data = {
            "model_version": self._model_version,
            "scoring_engine_version": self._scoring_engine_version,
            "steps": [
                {
                    "order": s.step_order,
                    "name": s.step_name,
                    "inputs": s.input_data,
                    "outputs": s.output_data,
                }
                for s in self._steps
            ],
        }
        input_hash = hashlib.sha256(
            json.dumps(all_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        lineage_parts = []
        for s in self._steps:
            lineage_parts.append(
                f"[{s.step_order}] {s.step_name} (v{s.version}) -> {json.dumps(s.output_data, ensure_ascii=False)}"
            )
        full_lineage = "\n".join(lineage_parts)

        return DecisionTrace(
            trace_id=trace_id,
            created_at=created_at,
            model_version=self._model_version,
            scoring_engine_version=self._scoring_engine_version,
            steps=list(self._steps),
            input_hash=input_hash,
            full_lineage=full_lineage,
        )

    def record_market_score(self, score: MarketScore) -> TraceStep:
        inputs = {
            "trend": score.trend,
            "liquidity": score.liquidity,
            "breadth": score.breadth,
            "volatility": score.volatility,
            "sentiment": score.sentiment,
        }
        outputs = {
            "total_score": score.total,
            "market_state": score.state,
        }
        self.record_step("market_score_computation", inputs, outputs)
        return self._steps[-1]

    def record_signal_mapping(self, score: float, signal: SizedSignal) -> TraceStep:
        inputs = {"raw_score": score}
        outputs = {
            "direction": signal.direction,
            "weight": signal.weight,
            "direction_label": self._direction_label(signal.direction),
        }
        self.record_step("signal_mapping", inputs, outputs)
        return self._steps[-1]

    def record_position_sizing(self, signal: SizedSignal, position: StrategyPosition) -> TraceStep:
        inputs = {
            "direction": signal.direction,
            "signal_weight": signal.weight,
            "score": signal.score,
        }
        outputs = {
            "position_pct": position.position_pct,
            "notional": position.notional,
        }
        self.record_step("position_sizing", inputs, outputs)
        return self._steps[-1]

    def record_risk_adjustment(self, position: StrategyPosition, adjusted: RiskAdjustedPosition) -> TraceStep:
        inputs = {
            "original_position_pct": position.position_pct,
            "original_notional": position.notional,
        }
        outputs = {
            "adjusted_position_pct": adjusted.adjusted_position_pct,
            "capped_by_exposure": adjusted.capped_by_exposure,
            "capped_by_turnover": adjusted.capped_by_turnover,
            "adjustment_reason": adjusted.adjustment_reason,
        }
        self.record_step("risk_adjustment", inputs, outputs)
        return self._steps[-1]

    def record_user_decision(
        self,
        signal: SizedSignal,
        action: str,
        modified_signal: SizedSignal | None = None,
        reason: str = "",
    ) -> TraceStep:
        inputs = {
            "original_direction": signal.direction,
            "original_weight": signal.weight,
            "original_score": signal.score,
            "user_action": action,
            "user_reason": reason,
        }
        outputs = {
            "action_taken": action,
        }
        if modified_signal is not None:
            outputs["modified_direction"] = modified_signal.direction
            outputs["modified_weight"] = modified_signal.weight
            outputs["modified_score"] = modified_signal.score
        self.record_step("user_decision", inputs, outputs)
        return self._steps[-1]

    def _sanitize(self, data: dict) -> dict:
        result = {}
        for k, v in data.items():
            if isinstance(v, float):
                result[k] = round(v, 6)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result

    def _direction_label(self, direction: int) -> str:
        if direction == 1:
            return "LONG"
        if direction == -1:
            return "SHORT"
        return "NEUTRAL"
