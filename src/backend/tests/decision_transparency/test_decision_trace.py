from datetime import datetime, timezone

import pytest

from app.decision_transparency.decision_trace import (
    DecisionTracer,
    DecisionTrace,
    TraceStep,
)
from app.domain.market.market_score import MarketScore
from app.strategy.signal_mapper import SizedSignal
from app.strategy.position_sizer import StrategyPosition
from app.strategy.risk_manager import RiskAdjustedPosition, RiskResult


class TestDecisionTracer:

    def test_start_clears_steps(self):
        tracer = DecisionTracer()
        tracer.record_step("step1", {"a": 1}, {"b": 2})
        tracer.start()
        trace = tracer.build()
        assert trace.step_count == 0

    def test_record_market_score(self):
        tracer = DecisionTracer()
        score = MarketScore(trend=75.0, liquidity=65.0, breadth=60.0, volatility=55.0, sentiment=50.0)
        step = tracer.record_market_score(score)

        assert step.step_name == "market_score_computation"
        assert step.input_data["trend"] == 75.0
        assert step.output_data["total_score"] == score.total
        assert step.output_data["market_state"] == score.state

    def test_record_signal_mapping(self):
        tracer = DecisionTracer()
        ts = datetime.now(timezone.utc)
        signal = SizedSignal(timestamp=ts, score=75.0, direction=1, weight=0.5)
        step = tracer.record_signal_mapping(75.0, signal)

        assert step.step_name == "signal_mapping"
        assert step.output_data["direction"] == 1
        assert step.output_data["weight"] == 0.5

    def test_record_position_sizing(self):
        tracer = DecisionTracer()
        ts = datetime.now(timezone.utc)
        signal = SizedSignal(timestamp=ts, score=75.0, direction=1, weight=0.5)
        position = StrategyPosition(timestamp=ts, direction=1, signal_weight=0.5, position_pct=0.5, notional=50000.0)
        step = tracer.record_position_sizing(signal, position)

        assert step.step_name == "position_sizing"
        assert step.output_data["position_pct"] == 0.5
        assert step.output_data["notional"] == 50000.0

    def test_record_risk_adjustment(self):
        tracer = DecisionTracer()
        ts = datetime.now(timezone.utc)
        position = StrategyPosition(timestamp=ts, direction=1, signal_weight=0.5, position_pct=0.8, notional=80000.0)
        adjusted = RiskAdjustedPosition(
            original=position,
            adjusted_position_pct=0.5,
            capped_by_exposure=True,
            capped_by_turnover=False,
            adjustment_reason="single_exposure",
        )
        step = tracer.record_risk_adjustment(position, adjusted)

        assert step.step_name == "risk_adjustment"
        assert step.output_data["capped_by_exposure"] is True
        assert step.output_data["adjustment_reason"] == "single_exposure"

    def test_record_user_decision(self):
        tracer = DecisionTracer()
        ts = datetime.now(timezone.utc)
        signal = SizedSignal(timestamp=ts, score=75.0, direction=1, weight=0.5)
        step = tracer.record_user_decision(signal, "APPROVE", reason="信号强度合理")

        assert step.step_name == "user_decision"
        assert step.input_data["user_action"] == "APPROVE"
        assert step.input_data["user_reason"] == "信号强度合理"

    def test_record_user_decision_with_modification(self):
        tracer = DecisionTracer()
        ts = datetime.now(timezone.utc)
        signal = SizedSignal(timestamp=ts, score=75.0, direction=1, weight=0.5)
        modified = SizedSignal(timestamp=ts, score=65.0, direction=1, weight=0.3)
        step = tracer.record_user_decision(signal, "MODIFY", modified_signal=modified, reason="降低仓位")

        assert step.output_data["modified_direction"] == 1
        assert step.output_data["modified_weight"] == 0.3

    def test_build_creates_trace_with_id(self):
        tracer = DecisionTracer()
        tracer.record_step("step1", {"a": 1}, {"b": 2})
        trace = tracer.build()

        assert len(trace.trace_id) > 0
        assert trace.model_version == "1.0.0"
        assert trace.scoring_engine_version == "1.0.0"
        assert trace.step_count == 1
        assert len(trace.input_hash) == 16
        assert len(trace.full_lineage) > 0

    def test_full_pipeline_trace(self):
        tracer = DecisionTracer()
        ts = datetime.now(timezone.utc)
        score = MarketScore(trend=80.0, liquidity=75.0, breadth=70.0, volatility=60.0, sentiment=65.0)

        tracer.record_market_score(score)
        signal = SizedSignal(timestamp=ts, score=score.total, direction=1, weight=0.6)
        tracer.record_signal_mapping(score.total, signal)
        position = StrategyPosition(timestamp=ts, direction=1, signal_weight=0.6, position_pct=0.6, notional=60000.0)
        tracer.record_position_sizing(signal, position)
        adjusted = RiskAdjustedPosition(
            original=position, adjusted_position_pct=0.5,
            capped_by_exposure=True, capped_by_turnover=False, adjustment_reason="single_exposure"
        )
        tracer.record_risk_adjustment(position, adjusted)
        tracer.record_user_decision(signal, "APPROVE", reason="通过")

        trace = tracer.build()
        assert trace.step_count == 5
        assert trace.full_lineage.count("\n") >= 4

    def test_trace_steps_ordered(self):
        tracer = DecisionTracer()
        tracer.record_step("first", {}, {})
        tracer.record_step("second", {}, {})
        tracer.record_step("third", {}, {})

        trace = tracer.build()
        orders = [s.step_order for s in trace.steps]
        assert orders == [1, 2, 3]

    def test_float_sanitization(self):
        tracer = DecisionTracer()
        tracer.record_step("test", {"value": 1.0 / 3.0}, {"result": 0.123456789})
        trace = tracer.build()
        step = trace.steps[0]
        assert isinstance(step.input_data["value"], float)
        assert step.input_data["value"] == pytest.approx(1.0 / 3.0, rel=1e-6)

    def test_trace_reproducibility(self):
        tracer1 = DecisionTracer()
        ts = datetime.now(timezone.utc)
        score = MarketScore(trend=50.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)
        tracer1.record_market_score(score)
        trace1 = tracer1.build()

        tracer2 = DecisionTracer()
        score2 = MarketScore(trend=50.0, liquidity=50.0, breadth=50.0, volatility=50.0, sentiment=50.0)
        tracer2.record_market_score(score2)
        trace2 = tracer2.build()

        assert trace1.input_hash == trace2.input_hash

    def test_direction_label(self):
        tracer = DecisionTracer()
        assert tracer._direction_label(1) == "LONG"
        assert tracer._direction_label(-1) == "SHORT"
        assert tracer._direction_label(0) == "NEUTRAL"
