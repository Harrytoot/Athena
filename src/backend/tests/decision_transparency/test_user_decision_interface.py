from datetime import datetime, timezone

import pytest

from app.decision_transparency.user_decision_interface import (
    UserDecisionInterface,
    DecisionAction,
    ApprovalConfig,
    UserDecision,
)
from app.strategy.signal_mapper import SizedSignal


def _signal(score: float = 75.0, direction: int = 1, weight: float = 0.5) -> SizedSignal:
    return SizedSignal(
        timestamp=datetime.now(timezone.utc),
        score=score,
        direction=direction,
        weight=weight,
    )


class TestUserDecisionInterface:

    def test_require_approval_creates_pending_decision(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        assert decision.action == DecisionAction.PENDING
        assert decision.approval_mode is True
        assert len(ui.pending_decisions) == 1

    def test_approve_changes_state(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        result = ui.approve(decision.decision_id, reason="信号合理", user="trader1")

        assert result.action == DecisionAction.APPROVE
        assert len(ui.approved_decisions) == 1
        assert len(ui.pending_decisions) == 0

    def test_reject_changes_state(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        result = ui.reject(decision.decision_id, reason="风险过高", user="trader1")

        assert result.action == DecisionAction.REJECT
        assert len(ui.rejected_decisions) == 1

    def test_modify_changes_state(self):
        ui = UserDecisionInterface()
        signal = _signal(score=75.0, direction=1, weight=0.5)
        decision = ui.require_approval(signal)

        result = ui.modify(
            decision.decision_id,
            new_score=65.0,
            new_direction=1,
            new_weight=0.3,
            reason="降低暴露",
            user="trader1",
        )

        assert result.action == DecisionAction.MODIFY
        assert result.modified_signal is not None
        assert result.modified_signal.score == 65.0
        assert result.modified_signal.weight == 0.3

    def test_reject_requires_reason(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        with pytest.raises(ValueError, match="Reason"):
            ui.reject(decision.decision_id, reason="", user="trader1")

    def test_modify_requires_reason(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        with pytest.raises(ValueError, match="Reason"):
            ui.modify(decision.decision_id, new_score=65.0, reason="", user="trader1")

    def test_modify_deviation_limit(self):
        config = ApprovalConfig(max_modify_deviation=0.1)
        ui = UserDecisionInterface(config=config)
        signal = _signal(score=75.0)
        decision = ui.require_approval(signal)

        with pytest.raises(ValueError, match="deviation"):
            ui.modify(decision.decision_id, new_score=30.0, reason="大幅修改", user="trader1")

    def test_cannot_approve_non_pending(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)
        ui.approve(decision.decision_id, reason="ok", user="trader1")

        with pytest.raises(ValueError, match="not in PENDING"):
            ui.approve(decision.decision_id, reason="again", user="trader1")

    def test_cannot_reject_non_pending(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)
        ui.reject(decision.decision_id, reason="bad", user="trader1")

        with pytest.raises(ValueError, match="not in PENDING"):
            ui.reject(decision.decision_id, reason="again", user="trader1")

    def test_cannot_modify_non_pending(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)
        ui.approve(decision.decision_id, reason="ok", user="trader1")

        with pytest.raises(ValueError, match="not in PENDING"):
            ui.modify(decision.decision_id, new_score=60.0, reason="change", user="trader1")

    def test_not_found_decision(self):
        ui = UserDecisionInterface()

        with pytest.raises(ValueError, match="not found"):
            ui.approve("nonexistent", reason="x", user="trader1")

        with pytest.raises(ValueError, match="not found"):
            ui.reject("nonexistent", reason="x", user="trader1")

        with pytest.raises(ValueError, match="not found"):
            ui.modify("nonexistent", new_score=60.0, reason="x", user="trader1")

    def test_can_auto_execute_disabled_by_default(self):
        ui = UserDecisionInterface()
        signal = _signal()
        assert ui.can_auto_execute(signal) is False

    def test_auto_approve_when_approval_disabled(self):
        config = ApprovalConfig(enabled=False)
        ui = UserDecisionInterface(config=config)
        signal = _signal()
        decision = ui.require_approval(signal)

        assert decision.action == DecisionAction.APPROVE
        assert ui.can_auto_execute(signal) is True

    def test_get_final_signal_approved(self):
        ui = UserDecisionInterface()
        signal = _signal(score=75.0)
        decision = ui.require_approval(signal)
        ui.approve(decision.decision_id, reason="ok", user="trader1")

        final = ui.get_final_signal(decision.decision_id)
        assert final is not None
        assert final.score == 75.0

    def test_get_final_signal_rejected_returns_none(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)
        ui.reject(decision.decision_id, reason="bad", user="trader1")

        final = ui.get_final_signal(decision.decision_id)
        assert final is None

    def test_get_final_signal_modified(self):
        ui = UserDecisionInterface()
        signal = _signal(score=75.0, direction=1, weight=0.5)
        decision = ui.require_approval(signal)
        ui.modify(decision.decision_id, new_score=60.0, new_direction=1, new_weight=0.3, reason="调整", user="trader1")

        final = ui.get_final_signal(decision.decision_id)
        assert final is not None
        assert final.score == 60.0
        assert final.weight == 0.3

    def test_get_final_signal_pending_returns_none(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        final = ui.get_final_signal(decision.decision_id)
        assert final is None

    def test_get_status(self):
        ui = UserDecisionInterface()
        signal = _signal()
        decision = ui.require_approval(signal)

        assert ui.get_status(decision.decision_id) == "PENDING"
        ui.approve(decision.decision_id, reason="ok", user="trader1")
        assert ui.get_status(decision.decision_id) == "APPROVE"
        assert ui.get_status("nonexistent") == "NOT_FOUND"

    def test_clear_history(self):
        ui = UserDecisionInterface()
        ui.require_approval(_signal())
        ui.require_approval(_signal())
        assert len(ui.decision_history) == 2

        ui.clear_history()
        assert len(ui.decision_history) == 0

    def test_multiple_decisions_tracking(self):
        ui = UserDecisionInterface()
        d1 = ui.require_approval(_signal(score=80.0))
        d2 = ui.require_approval(_signal(score=20.0))

        ui.approve(d1.decision_id, reason="看多", user="trader1")
        ui.reject(d2.decision_id, reason="看空", user="trader1")

        assert len(ui.approved_decisions) == 1
        assert len(ui.rejected_decisions) == 1
        assert len(ui.pending_decisions) == 0

    def test_approval_config_defaults(self):
        config = ApprovalConfig()
        assert config.enabled is True
        assert config.require_reason is True
        assert config.max_modify_deviation == 0.3
        assert config.auto_reject_timeout_minutes == 60

    def test_modify_preserves_original_fields_if_not_specified(self):
        ui = UserDecisionInterface()
        signal = _signal(score=75.0, direction=1, weight=0.5)
        decision = ui.require_approval(signal)
        ui.modify(decision.decision_id, new_score=65.0, reason="仅改分数", user="trader1")

        final = ui.get_final_signal(decision.decision_id)
        assert final.score == 65.0
        assert final.direction == 1
        assert final.weight == 0.5

    def test_decision_dataclass_fields(self):
        signal = _signal()
        decision = UserDecision(
            decision_id="test-id",
            action=DecisionAction.PENDING,
            original_signal=signal,
            modified_signal=None,
            reason="",
            decided_at=datetime.now(timezone.utc),
            decided_by="",
            approval_mode=True,
        )
        assert decision.decision_id == "test-id"
        assert decision.action == DecisionAction.PENDING
        assert decision.approval_mode is True
