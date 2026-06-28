import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.runtime.semantic_runtime_engine import (
    SemanticRuntimeEngine,
    RuntimeEventRecord,
    RuntimeUpdateResult,
)
from app.decision_semantics.runtime.state_transition_model import TransitionEvent
from app.decision_semantics.schema import DecisionSemantic
from app.decision_semantics.streaming.portfolio_runtime_graph import (
    PortfolioRuntimeGraph,
    PortfolioUpdateResult,
)
from app.decision_semantics.streaming.execution_binding_layer import (
    ExecutionBindingLayer,
    ExecutionBindingResult,
    ExecutionIntent,
)
from app.decision_semantics.streaming.streaming_state_coordinator import (
    StreamingStateCoordinator,
)
from app.decision_semantics.streaming.stream_processor import (
    StreamEventRaw,
    StreamEventRecord,
    StreamProcessor,
    StreamEventType,
)


@dataclass
class StreamIngestionResult:
    record: StreamEventRecord
    runtime_result: RuntimeUpdateResult | None = None
    portfolio_result: PortfolioUpdateResult | None = None


@dataclass
class StreamCycleResult:
    ingested: list[StreamIngestionResult] = field(default_factory=list)
    execution_result: ExecutionBindingResult | None = None
    cycle_time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def total_ingested(self) -> int:
        return len(self.ingested)

    @property
    def symbols_updated(self) -> list[str]:
        return list(set(
            r.record.symbol for r in self.ingested
            if r.runtime_result is not None
        ))


class StreamingEngine:

    def __init__(self, batch_window: int = 10):
        self._runtime = SemanticRuntimeEngine()
        self._graph = PortfolioRuntimeGraph(correlation_threshold=0.3)
        self._binding = ExecutionBindingLayer()
        self._coordinator = StreamingStateCoordinator()
        self._processor = StreamProcessor(batch_window=batch_window)
        self._is_running = False
        self._cycle_count: int = 0
        self._event_log: list[StreamEventRecord] = []
        self._ingestion_history: list[StreamIngestionResult] = []

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

    def ingest_events(self, raws: list[StreamEventRaw]) -> list[StreamIngestionResult]:
        records = self._processor.ingest_batch(raws)
        results: list[StreamIngestionResult] = []

        for record in records:
            result = self._apply_stream_event(record)
            results.append(result)
            self._ingestion_history.append(result)

        self._event_log.extend(records)
        return results

    def process_cycle(self) -> StreamCycleResult:
        self._cycle_count += 1

        batch = self._processor.process_batch()
        ingested: list[StreamIngestionResult] = []

        for record in batch:
            result = self._apply_stream_event(record)
            ingested.append(result)
            self._ingestion_history.append(result)

        self._event_log.extend(batch)

        active_semantics = self.get_active_semantics()
        exec_result = self._binding.bind_portfolio(active_semantics)

        for symbol, semantic in active_semantics.items():
            self._graph.register_symbol(symbol, semantic)

        return StreamCycleResult(
            ingested=ingested,
            execution_result=exec_result,
        )

    def get_active_semantics(self) -> dict[str, DecisionSemantic]:
        return self._runtime.get_active_semantics()

    def get_active_semantic(self, symbol: str) -> DecisionSemantic | None:
        return self._runtime.get_active(symbol)

    def get_runtime_engine(self) -> SemanticRuntimeEngine:
        return self._runtime

    def get_portfolio_graph(self) -> PortfolioRuntimeGraph:
        return self._graph

    def get_binding_layer(self) -> ExecutionBindingLayer:
        return self._binding

    def get_execution_intents(self) -> dict[str, ExecutionIntent]:
        return self._binding.get_active_intents()

    def get_blocked_intents(self) -> dict[str, ExecutionIntent]:
        return {
            sym: b.intent for sym, b in self._binding.get_blocked_intents().items()
        }

    def setup_correlations(
        self, correlations: list[tuple[str, str, float]]
    ) -> None:
        self._graph.set_correlations(correlations)

    def set_correlation(
        self, symbol_a: str, symbol_b: str, coefficient: float
    ) -> None:
        self._graph.set_correlation(symbol_a, symbol_b, coefficient)

    def check_portfolio_consistency(self) -> list[str]:
        return self._graph.check_portfolio_consistency()

    def resolve_portfolio_conflicts(self) -> list[dict]:
        conflicts: list[dict] = []
        edges = self._graph.get_all_edges()

        for edge in edges:
            if not edge.is_significant:
                continue
            resolution = self._coordinator.resolve_conflicts(
                edge.from_symbol, edge.to_symbol, edge.coefficient
            )
            if resolution.get("status") == "conflict_detected":
                conflicts.append(resolution)

        return conflicts

    def get_event_log(self) -> list[StreamEventRecord]:
        return list(self._event_log)

    def get_ingestion_history(self) -> list[StreamIngestionResult]:
        return list(self._ingestion_history)

    def get_cycle_count(self) -> int:
        return self._cycle_count

    def get_portfolio_state(self) -> dict:
        return {
            "symbols": self._graph.get_all_symbols(),
            "semantics": {
                sym: {
                    "action": node.active_semantic.action if node.active_semantic else None,
                    "confidence": node.active_semantic.confidence_score if node.active_semantic else None,
                }
                for sym, node in self._graph._nodes.items()
            },
            "correlations": {
                e.edge_id: {
                    "from": e.from_symbol,
                    "to": e.to_symbol,
                    "coefficient": e.coefficient,
                }
                for e in self._graph.get_all_edges()
            },
            "consistency_issues": self._graph.check_portfolio_consistency(),
        }

    def replay_events(
        self, events: list[StreamEventRecord]
    ) -> dict[str, list[StreamIngestionResult]]:
        self.reset()

        results: dict[str, list[StreamIngestionResult]] = {}

        for event in events:
            self._processor._sequence_counter = max(
                self._processor._sequence_counter, event.global_sequence_number
            )
            result = self._apply_stream_event(event)
            results.setdefault(event.symbol, []).append(result)
            self._ingestion_history.append(result)
            self._event_log.append(event)

        return results

    def reset(self) -> None:
        self._runtime = SemanticRuntimeEngine()
        self._graph = PortfolioRuntimeGraph(correlation_threshold=0.3)
        self._binding = ExecutionBindingLayer()
        self._coordinator = StreamingStateCoordinator()
        self._processor = StreamProcessor()
        self._is_running = False
        self._cycle_count = 0
        self._event_log.clear()
        self._ingestion_history.clear()

    def _apply_stream_event(
        self, record: StreamEventRecord
    ) -> StreamIngestionResult:
        runtime_result = None
        portfolio_result = None

        is_new = self._runtime.get_active(record.symbol) is None

        if is_new:
            semantic = self._processor._build_minimal_semantic(record)
            if semantic is not None:
                runtime_result = self._runtime.initialize(record.symbol, semantic)
                self._graph.register_symbol(record.symbol, semantic)
                self._coordinator.set_active(record.symbol, semantic)
        else:
            if record.is_delta_event and record.computed_delta is not None:
                try:
                    runtime_result = self._runtime.apply_delta(
                        record.symbol, record.computed_delta
                    )
                except ValueError:
                    pass

        if runtime_result is not None and runtime_result.snapshot is not None:
            updated_semantic = runtime_result.snapshot.semantic
            portfolio_result = self._graph.update_symbol(
                record.symbol, updated_semantic
            )
            self._coordinator.set_active(record.symbol, updated_semantic)

        return StreamIngestionResult(
            record=record,
            runtime_result=runtime_result,
            portfolio_result=portfolio_result,
        )

    def _capture_full_state(self) -> dict:
        return {
            "runtime_events": [
                {
                    "event_type": e.event_type.value,
                    "symbol": e.symbol,
                    "sequence": e.sequence_number,
                }
                for e in self._runtime.get_event_log()
            ],
            "stream_events": [
                {
                    "event_type": e.event_type.value,
                    "symbol": e.symbol,
                    "global_seq": e.global_sequence_number,
                }
                for e in self._event_log
            ],
            "active_semantics": self._runtime.get_active_semantics(),
            "graph_symbols": self._graph.get_all_symbols(),
            "execution_intents": self._binding.get_active_intents(),
        }
