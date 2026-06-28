import pytest

from app.decision_semantics.streaming.stream_processor import (
    StreamEventType,
    StreamEventRaw,
    StreamProcessor,
)
from app.decision_semantics.schema import (
    DecisionSemantic,
    SignalSemantic,
    FactorSemantic,
    RiskSemantic,
    ScenarioSemantic,
    ConsistencyReport,
)


def _make_semantic(symbol: str = "AAPL", action: str = "APPROVE") -> DecisionSemantic:
    return DecisionSemantic(
        symbol=symbol,
        name="Test Stock",
        signal=SignalSemantic(
            direction="LONG" if action == "APPROVE" else "NEUTRAL",
            direction_label="看多" if action == "APPROVE" else "中性",
            strength=0.85,
            base_confidence=82.0,
        ),
        factors=[
            FactorSemantic(
                name="trend",
                label="趋势",
                value=88.0,
                weight=0.30,
                contribution=26.4,
                is_bullish=True,
                assessment="强看多",
            ),
            FactorSemantic(
                name="liquidity",
                label="流动性",
                value=72.0,
                weight=0.25,
                contribution=18.0,
                is_bullish=True,
                assessment="偏多",
            ),
            FactorSemantic(
                name="momentum",
                label="动量",
                value=65.0,
                weight=0.25,
                contribution=16.25,
                is_bullish=True,
                assessment="偏多",
            ),
        ],
        risk=RiskSemantic(
            overall_level="MODERATE",
            drawdown_risk=0.3,
            volatility_risk=0.4,
            correlation_risk=0.2,
            scenario_vulnerability=0.35,
            warnings=[],
        ),
        scenario=ScenarioSemantic(
            stability_score=0.75,
            worst_case_score_change=-18.0,
            state_change_count=1,
            entries=[],
        ),
        confidence_score=0.82,
        consistency=ConsistencyReport(
            is_consistent=True,
            contradictions=[],
            consistency_score=0.95,
        ),
        action=action,
        action_label="执行买入" if action == "APPROVE" else "等待",
        summary="Test summary",
        semantic_version="1.0.0",
    )


class TestStreamingEventReplay:

    def setup_method(self):
        self._processor = StreamProcessor()

    def _build_events(self) -> list[StreamEventRaw]:
        return [
            StreamEventRaw(
                event_type=StreamEventType.FEATURE_UPDATE,
                symbol="AAPL",
                payload={"signal_strength": 0.90, "confidence": 0.88},
            ),
            StreamEventRaw(
                event_type=StreamEventType.MARKET_TICK,
                symbol="AAPL",
                payload={"volatility": 0.35},
            ),
            StreamEventRaw(
                event_type=StreamEventType.RISK_EVENT,
                symbol="AAPL",
                payload={"overall_level": "HIGH", "drawdown_risk": 0.6},
            ),
        ]

    def test_replay_produces_identical_event_log(self):
        raws = self._build_events()

        run_logs = []
        for _ in range(3):
            processor = StreamProcessor()
            processor.ingest_batch(raws)
            processor.process_all_pending()
            log = processor.get_event_log()
            run_logs.append(log)

        log0 = run_logs[0]
        for i in range(1, len(run_logs)):
            log_i = run_logs[i]
            assert len(log0) == len(log_i)
            for j in range(len(log0)):
                assert log0[j].event_type == log_i[j].event_type
                assert log0[j].symbol == log_i[j].symbol
                assert log0[j].global_sequence_number == log_i[j].global_sequence_number

    def test_replay_same_events_same_sequence_numbers(self):
        raws = self._build_events()

        seq_runs = []
        for _ in range(3):
            processor = StreamProcessor()
            processor.ingest_batch(raws)
            processor.process_all_pending()
            seqs = [e.global_sequence_number for e in processor.get_event_log()]
            seq_runs.append(seqs)

        for i in range(1, len(seq_runs)):
            assert seq_runs[i] == seq_runs[0]

    def test_replay_empty_events(self):
        processor = StreamProcessor()
        logs = processor.process_batch()
        assert len(logs) == 0
        assert processor.event_count == 0

    def test_replay_with_multiple_batches(self):
        batch1 = [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL", {"signal_strength": 0.85}),
        ]
        batch2 = [
            StreamEventRaw(StreamEventType.RISK_EVENT, "AAPL", {"volatility_risk": 0.45}),
        ]

        logs_runs = []
        for _ in range(3):
            processor = StreamProcessor()
            processor.ingest_batch(batch1)
            processor.process_all_pending()
            processor.ingest_batch(batch2)
            processor.process_all_pending()
            logs_runs.append(processor.get_event_log())

        for i in range(1, len(logs_runs)):
            assert len(logs_runs[i]) == len(logs_runs[0])
            for j in range(len(logs_runs[0])):
                assert logs_runs[i][j].event_id == logs_runs[0][j].event_id

    def test_replay_is_idempotent(self):
        raws = self._build_events()

        processor = StreamProcessor()
        processor.ingest_batch(raws)
        first_log = [e.event_id for e in processor.get_event_log()]

        processor.reset()
        processor.ingest_batch(raws)
        second_log = [e.event_id for e in processor.get_event_log()]

        assert first_log == second_log

    def test_deteministic_event_id_generation(self):
        raw1 = StreamEventRaw(StreamEventType.FEATURE_UPDATE, "TSLA", {"signal_strength": 0.9})

        ids = []
        for _ in range(10):
            processor = StreamProcessor()
            processor.ingest_raw(raw1)
            processor.process_all_pending()
            ids.append(processor.get_event_log()[0].event_id)

        for i in range(1, len(ids)):
            assert ids[i] == ids[0]
