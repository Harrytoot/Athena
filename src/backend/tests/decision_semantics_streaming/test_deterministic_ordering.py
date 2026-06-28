import pytest

from app.decision_semantics.streaming.streaming_engine import (
    StreamingEngine,
)
from app.decision_semantics.streaming.stream_processor import (
    StreamEventType,
    StreamEventRaw,
    StreamEventRecord,
)
from app.decision_semantics.streaming.streaming_state_coordinator import (
    StreamingStateCoordinator,
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


class TestDeterministicOrdering:

    def setup_method(self):
        pass

    def _build_stream_events(self) -> list[StreamEventRaw]:
        return [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL",
                          {"signal_strength": 0.90, "confidence": 0.88}),
            StreamEventRaw(StreamEventType.MARKET_TICK, "MSFT",
                          {"volatility": 0.30}),
            StreamEventRaw(StreamEventType.RISK_EVENT, "AAPL",
                          {"overall_level": "HIGH", "drawdown_risk": 0.55}),
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "TSLA",
                          {"signal_strength": 0.70, "confidence": 0.72}),
            StreamEventRaw(StreamEventType.RISK_EVENT, "MSFT",
                          {"volatility_risk": 0.45}),
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL",
                          {"confidence": 0.92}),
        ]

    def test_stream_ordering_is_monotonic(self):
        events = self._build_stream_events()

        engines = []
        for _ in range(3):
            engine = StreamingEngine()
            s_aapl = _make_semantic("AAPL", "APPROVE")
            s_msft = _make_semantic("MSFT", "APPROVE")
            s_tsla = _make_semantic("TSLA", "REJECT")
            engine.get_runtime_engine().initialize("AAPL", s_aapl)
            engine.get_runtime_engine().initialize("MSFT", s_msft)
            engine.get_runtime_engine().initialize("TSLA", s_tsla)
            engine.get_portfolio_graph().register_symbol("AAPL", s_aapl)
            engine.get_portfolio_graph().register_symbol("MSFT", s_msft)
            engine.get_portfolio_graph().register_symbol("TSLA", s_tsla)
            engine.set_correlation("AAPL", "MSFT", 0.7)
            engine.set_correlation("MSFT", "TSLA", -0.3)
            engine.ingest_events(events)
            engine.process_cycle()
            engines.append(engine)

        for i in range(1, len(engines)):
            log0 = engines[0].get_event_log()
            log_i = engines[i].get_event_log()
            assert len(log0) == len(log_i)
            for j in range(len(log0)):
                assert log0[j].global_sequence_number == log_i[j].global_sequence_number
                assert log0[j].event_type == log_i[j].event_type
                assert log0[j].symbol == log_i[j].symbol

    def test_deterministic_order_preserved_across_cycles(self):
        engine = StreamingEngine()

        s_aapl = _make_semantic("AAPL", "APPROVE")
        engine.get_runtime_engine().initialize("AAPL", s_aapl)
        engine.get_portfolio_graph().register_symbol("AAPL", s_aapl)

        events_cycle1 = [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL", {"confidence": 0.85}),
            StreamEventRaw(StreamEventType.RISK_EVENT, "AAPL", {"volatility_risk": 0.35}),
        ]
        events_cycle2 = [
            StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL", {"confidence": 0.90}),
            StreamEventRaw(StreamEventType.MARKET_TICK, "AAPL", {"volatility": 0.28}),
        ]

        assert engine.get_event_log() == []

        engine.ingest_events(events_cycle1)
        engine.process_cycle()

        log_after_cycle1 = engine.get_event_log()
        seqs_c1 = [e.global_sequence_number for e in log_after_cycle1]
        for i in range(1, len(seqs_c1)):
            assert seqs_c1[i] > seqs_c1[i - 1]

        engine.ingest_events(events_cycle2)
        engine.process_cycle()

        log_after_cycle2 = engine.get_event_log()
        seqs_c2 = [e.global_sequence_number for e in log_after_cycle2]
        for i in range(1, len(seqs_c2)):
            assert seqs_c2[i] > seqs_c2[i - 1]

        assert len(log_after_cycle2) > len(log_after_cycle1)

    def test_replay_with_deterministic_engine(self):
        events = self._build_stream_events()

        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")
        s_tsla = _make_semantic("TSLA", "REJECT")

        results_runs = []
        for _ in range(3):
            engine = StreamingEngine()
            engine.get_runtime_engine().initialize("AAPL", s_aapl)
            engine.get_runtime_engine().initialize("MSFT", s_msft)
            engine.get_runtime_engine().initialize("TSLA", s_tsla)
            engine.get_portfolio_graph().register_symbol("AAPL", s_aapl)
            engine.get_portfolio_graph().register_symbol("MSFT", s_msft)
            engine.get_portfolio_graph().register_symbol("TSLA", s_tsla)
            engine.set_correlation("AAPL", "MSFT", 0.7)
            engine.set_correlation("MSFT", "TSLA", -0.3)
            engine.ingest_events(events)
            engine.process_cycle()
            results_runs.append(engine)

        r1 = results_runs[0]
        for i in range(1, len(results_runs)):
            rn = results_runs[i]

            active1 = r1.get_active_semantics()
            active_n = rn.get_active_semantics()

            for sym in active1:
                assert active_n[sym].action == active1[sym].action
                assert active_n[sym].confidence_score == active1[sym].confidence_score

            issues1 = r1.check_portfolio_consistency()
            issues_n = rn.check_portfolio_consistency()
            assert len(issues1) == len(issues_n)

    def test_deterministic_ordering_with_coordinator(self):
        coordinator = StreamingStateCoordinator()

        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "REJECT")

        coordinator.set_active("AAPL", s_aapl)
        coordinator.set_active("MSFT", s_msft)

        order_runs = []
        for _ in range(5):
            coord = StreamingStateCoordinator()
            coord.set_active("AAPL", s_aapl)
            coord.set_active("MSFT", s_msft)
            order = coord.ensure_deterministic_ordering()
            order_runs.append(order)

        for i in range(1, len(order_runs)):
            assert order_runs[i] == order_runs[0]

    def test_ordering_preserved_with_interleaved_events(self):
        s_aapl = _make_semantic("AAPL", "APPROVE")
        s_msft = _make_semantic("MSFT", "APPROVE")

        run_results = []
        for _ in range(3):
            engine = StreamingEngine()
            engine.get_runtime_engine().initialize("AAPL", s_aapl)
            engine.get_runtime_engine().initialize("MSFT", s_msft)
            engine.get_portfolio_graph().register_symbol("AAPL", s_aapl)
            engine.get_portfolio_graph().register_symbol("MSFT", s_msft)
            engine.set_correlation("AAPL", "MSFT", 0.75)

            events = [
                StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL", {"confidence": 0.88}),
                StreamEventRaw(StreamEventType.FEATURE_UPDATE, "MSFT", {"confidence": 0.82}),
                StreamEventRaw(StreamEventType.RISK_EVENT, "AAPL", {"volatility_risk": 0.40}),
                StreamEventRaw(StreamEventType.RISK_EVENT, "MSFT", {"volatility_risk": 0.38}),
                StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL", {"confidence": 0.91}),
                StreamEventRaw(StreamEventType.FEATURE_UPDATE, "MSFT", {"confidence": 0.86}),
            ]
            engine.ingest_events(events)
            engine.process_cycle()
            run_results.append(engine)

        base = run_results[0]
        for i in range(1, len(run_results)):
            base_log = base.get_event_log()
            run_log = run_results[i].get_event_log()
            assert [e.symbol for e in base_log] == [e.symbol for e in run_log]

    def test_sequence_numbers_never_decrease(self):
        engine = StreamingEngine()
        s_aapl = _make_semantic("AAPL", "APPROVE")
        engine.get_runtime_engine().initialize("AAPL", s_aapl)
        engine.get_portfolio_graph().register_symbol("AAPL", s_aapl)

        prev_seq = 0
        prev_log_len = 0
        for batch_num in range(5):
            events = [
                StreamEventRaw(StreamEventType.FEATURE_UPDATE, "AAPL",
                              {"confidence": 0.80 + batch_num * 0.02}),
            ]
            engine.ingest_events(events)

            log = engine.get_event_log()
            new_events = log[prev_log_len:]
            for e in new_events:
                assert e.global_sequence_number > prev_seq
                prev_seq = e.global_sequence_number
            prev_log_len = len(log)

        assert prev_seq > 0
