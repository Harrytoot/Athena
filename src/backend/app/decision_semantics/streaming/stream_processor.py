import hashlib
import json
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from app.decision_semantics.runtime.semantic_delta_engine import (
    SemanticDelta,
    SemanticDeltaEngine,
)
from app.decision_semantics.runtime.state_transition_model import TransitionEvent
from app.decision_semantics.schema import (
    DecisionSemantic,
    FactorSemantic,
    RiskSemantic,
    SignalSemantic,
)


class StreamEventType(Enum):
    MARKET_TICK = "market_tick"
    FEATURE_UPDATE = "feature_update"
    RISK_EVENT = "risk_event"


_STREAM_TO_TRANSITION: dict[StreamEventType, TransitionEvent] = {
    StreamEventType.MARKET_TICK: TransitionEvent.MARKET_TICK,
    StreamEventType.FEATURE_UPDATE: TransitionEvent.FEATURE_UPDATE,
    StreamEventType.RISK_EVENT: TransitionEvent.RISK_RECALIBRATE,
}


@dataclass
class StreamEventRaw:
    event_type: StreamEventType
    symbol: str
    payload: dict = field(default_factory=dict)
    event_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class StreamEventRecord:
    event_type: StreamEventType
    symbol: str
    payload: dict
    event_timestamp: str
    event_id: str = ""
    global_sequence_number: int = 0
    transition_event: TransitionEvent | None = None
    computed_delta: SemanticDelta | None = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = self._compute_id()
        if not self.transition_event:
            self.transition_event = _STREAM_TO_TRANSITION.get(self.event_type)

    def _compute_id(self) -> str:
        raw = json.dumps({
            "event_type": self.event_type.value,
            "symbol": self.symbol,
            "global_sequence_number": self.global_sequence_number,
            "payload_keys": sorted(self.payload.keys()),
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def is_delta_event(self) -> bool:
        return self.computed_delta is not None and not self.computed_delta.is_empty


class StreamProcessor:

    def __init__(self, batch_window: int = 10):
        self._delta_engine = SemanticDeltaEngine()
        self._event_log: list[StreamEventRecord] = []
        self._sequence_counter: int = 0
        self._pending_raw: deque[StreamEventRaw] = deque()
        self._batch_window = batch_window
        self._last_known_semantics: dict[str, DecisionSemantic] = {}

    def ingest_raw(self, raw: StreamEventRaw) -> StreamEventRecord:
        self._pending_raw.append(raw)
        record = self._to_record(raw)
        self._event_log.append(record)
        return record

    def ingest_batch(self, raws: list[StreamEventRaw]) -> list[StreamEventRecord]:
        records: list[StreamEventRecord] = []
        for raw in raws:
            records.append(self.ingest_raw(raw))
        return records

    def process_batch(self) -> list[StreamEventRecord]:
        optimistic_limit = min(len(self._pending_raw), self._batch_window)
        batch: list[StreamEventRecord] = []

        for _ in range(optimistic_limit):
            if not self._pending_raw:
                break
            raw = self._pending_raw.popleft()
            record = self._to_record(raw)
            self._event_log.append(record)
            batch.append(record)

        for record in batch:
            self._compute_event_delta(record)

        self._optimize_batch(batch)
        return batch

    def process_one(self) -> StreamEventRecord | None:
        if not self._pending_raw:
            return None
        raw = self._pending_raw.popleft()
        record = self._to_record(raw)
        self._event_log.append(record)
        self._compute_event_delta(record)
        return record

    def process_all_pending(self) -> list[StreamEventRecord]:
        records: list[StreamEventRecord] = []
        while self._pending_raw:
            records.append(self.process_one())
        return records

    def peek_pending(self) -> list[StreamEventRaw]:
        return list(self._pending_raw)

    @property
    def pending_count(self) -> int:
        return len(self._pending_raw)

    @property
    def event_count(self) -> int:
        return len(self._event_log)

    def get_event_log(self) -> list[StreamEventRecord]:
        return list(self._event_log)

    def get_events_by_symbol(self, symbol: str) -> list[StreamEventRecord]:
        return [e for e in self._event_log if e.symbol == symbol]

    def clear_pending(self) -> None:
        self._pending_raw.clear()

    def reset(self) -> None:
        self._event_log.clear()
        self._sequence_counter = 0
        self._pending_raw.clear()
        self._last_known_semantics.clear()

    def _to_record(self, raw: StreamEventRaw) -> StreamEventRecord:
        self._sequence_counter += 1
        return StreamEventRecord(
            event_type=raw.event_type,
            symbol=raw.symbol,
            payload=deepcopy(raw.payload),
            event_timestamp=raw.event_timestamp,
            global_sequence_number=self._sequence_counter,
        )

    def _compute_event_delta(self, record: StreamEventRecord) -> None:
        previous = self._last_known_semantics.get(record.symbol)
        if previous is None:
            current = self._build_minimal_semantic(record)
            if current is not None:
                self._last_known_semantics[record.symbol] = current
            record.computed_delta = None
            return

        current = self._apply_payload_to_semantic(previous, record)
        if current is None:
            return

        record.computed_delta = self._delta_engine.compute_delta(previous, current)
        self._last_known_semantics[record.symbol] = current

    def _apply_payload_to_semantic(
        self, base: DecisionSemantic, record: StreamEventRecord
    ) -> DecisionSemantic | None:
        result = deepcopy(base)
        p = record.payload

        if record.event_type == StreamEventType.MARKET_TICK:
            if "price" in p:
                pass
            if "volatility" in p:
                result.risk.volatility_risk = float(p["volatility"])
            if "volume" in p:
                pass

        elif record.event_type == StreamEventType.FEATURE_UPDATE:
            if "signal_strength" in p:
                result.signal.strength = float(p["signal_strength"])
            if "signal_direction" in p:
                result.signal.direction = str(p["signal_direction"])
            if "confidence" in p:
                result.confidence_score = float(p["confidence"])
            if "factor_updates" in p:
                for f in result.factors:
                    f_name = f.name
                    if f_name in p["factor_updates"]:
                        f.value = float(p["factor_updates"][f_name])

        elif record.event_type == StreamEventType.RISK_EVENT:
            if "overall_level" in p:
                result.risk.overall_level = str(p["overall_level"])
            if "drawdown_risk" in p:
                result.risk.drawdown_risk = float(p["drawdown_risk"])
            if "volatility_risk" in p:
                result.risk.volatility_risk = float(p["volatility_risk"])
            if "correlation_risk" in p:
                result.risk.correlation_risk = float(p["correlation_risk"])
            if "warnings" in p:
                result.risk.warnings = list(p["warnings"])

        return result

    def _build_minimal_semantic(
        self, record: StreamEventRecord
    ) -> DecisionSemantic | None:
        return DecisionSemantic(
            symbol=record.symbol,
            name=record.symbol,
            signal=SignalSemantic(
                direction="NEUTRAL",
                direction_label="中性",
                strength=0.5,
                base_confidence=50.0,
            ),
            factors=[
                FactorSemantic(
                    name="trend",
                    label="趋势",
                    value=50.0,
                    weight=0.40,
                    contribution=20.0,
                    is_bullish=False,
                    assessment="中性",
                ),
                FactorSemantic(
                    name="liquidity",
                    label="流动性",
                    value=50.0,
                    weight=0.35,
                    contribution=17.5,
                    is_bullish=False,
                    assessment="中性",
                ),
                FactorSemantic(
                    name="momentum",
                    label="动量",
                    value=50.0,
                    weight=0.25,
                    contribution=12.5,
                    is_bullish=False,
                    assessment="中性",
                ),
            ],
            risk=RiskSemantic(
                overall_level="MODERATE",
                drawdown_risk=0.5,
                volatility_risk=0.5,
                correlation_risk=0.5,
                scenario_vulnerability=0.5,
                warnings=[],
            ),
            confidence_score=0.5,
            action="HOLD",
            action_label="等待",
            summary="Initialized from stream event",
            semantic_version="1.0.0",
        )

    def _optimize_batch(self, batch: list[StreamEventRecord]) -> None:
        last_update: dict[str, int] = {}

        for i, record in enumerate(batch):
            if record.computed_delta:
                last_update[record.symbol] = i

        for i, record in enumerate(batch):
            if record.computed_delta and record.symbol in last_update:
                if i < last_update[record.symbol]:
                    record.computed_delta = None
