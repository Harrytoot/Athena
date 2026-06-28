from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from app.strategy.signal_mapper import SizedSignal


class DecisionAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    PENDING = "PENDING"


@dataclass
class UserDecision:
    decision_id: str
    action: DecisionAction
    original_signal: SizedSignal
    modified_signal: SizedSignal | None
    reason: str
    decided_at: datetime
    decided_by: str
    approval_mode: bool


@dataclass
class ApprovalConfig:
    enabled: bool = True
    require_reason: bool = True
    max_modify_deviation: float = 0.3
    auto_reject_timeout_minutes: int = 60


class UserDecisionInterface:

    def __init__(self, config: ApprovalConfig | None = None):
        self._config = config or ApprovalConfig()
        self._history: list[UserDecision] = []

    @property
    def approval_enabled(self) -> bool:
        return self._config.enabled

    @property
    def decision_history(self) -> list[UserDecision]:
        return list(self._history)

    @property
    def pending_decisions(self) -> list[UserDecision]:
        return [d for d in self._history if d.action == DecisionAction.PENDING]

    @property
    def approved_decisions(self) -> list[UserDecision]:
        return [d for d in self._history if d.action == DecisionAction.APPROVE]

    @property
    def rejected_decisions(self) -> list[UserDecision]:
        return [d for d in self._history if d.action == DecisionAction.REJECT]

    @property
    def modified_decisions(self) -> list[UserDecision]:
        return [d for d in self._history if d.action == DecisionAction.MODIFY]

    def require_approval(self, signal: SizedSignal) -> UserDecision:
        if not self._config.enabled:
            return UserDecision(
                decision_id=str(uuid4()),
                action=DecisionAction.APPROVE,
                original_signal=signal,
                modified_signal=None,
                reason="approval mode disabled - auto approved",
                decided_at=datetime.now(timezone.utc),
                decided_by="system",
                approval_mode=False,
            )

        decision = UserDecision(
            decision_id=str(uuid4()),
            action=DecisionAction.PENDING,
            original_signal=signal,
            modified_signal=None,
            reason="",
            decided_at=datetime.now(timezone.utc),
            decided_by="",
            approval_mode=True,
        )
        self._history.append(decision)
        return decision

    def approve(self, decision_id: str, reason: str = "", user: str = "") -> UserDecision:
        decision = self._find_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision {decision_id} not found")
        if decision.action != DecisionAction.PENDING:
            raise ValueError(f"Decision {decision_id} is not in PENDING state")

        decision.action = DecisionAction.APPROVE
        decision.reason = reason
        decision.decided_at = datetime.now(timezone.utc)
        decision.decided_by = user
        return decision

    def reject(self, decision_id: str, reason: str = "", user: str = "") -> UserDecision:
        decision = self._find_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision {decision_id} not found")
        if decision.action != DecisionAction.PENDING:
            raise ValueError(f"Decision {decision_id} is not in PENDING state")

        if self._config.require_reason and not reason.strip():
            raise ValueError("Reason is required to reject a decision")

        decision.action = DecisionAction.REJECT
        decision.reason = reason
        decision.decided_at = datetime.now(timezone.utc)
        decision.decided_by = user
        return decision

    def modify(
        self,
        decision_id: str,
        new_score: float,
        new_direction: int | None = None,
        new_weight: float | None = None,
        reason: str = "",
        user: str = "",
    ) -> UserDecision:
        decision = self._find_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision {decision_id} not found")
        if decision.action != DecisionAction.PENDING:
            raise ValueError(f"Decision {decision_id} is not in PENDING state")

        orig_score = decision.original_signal.score
        deviation = abs(new_score - orig_score) / max(abs(orig_score), 1.0)
        if deviation > self._config.max_modify_deviation:
            raise ValueError(
                f"Modification deviation {deviation:.2%} exceeds max allowed "
                f"{self._config.max_modify_deviation:.0%}"
            )

        if self._config.require_reason and not reason.strip():
            raise ValueError("Reason is required to modify a decision")

        modified = SizedSignal(
            timestamp=decision.original_signal.timestamp,
            score=new_score,
            direction=new_direction if new_direction is not None else decision.original_signal.direction,
            weight=new_weight if new_weight is not None else decision.original_signal.weight,
        )

        decision.action = DecisionAction.MODIFY
        decision.modified_signal = modified
        decision.reason = reason
        decision.decided_at = datetime.now(timezone.utc)
        decision.decided_by = user
        return decision

    def can_auto_execute(self, signal: SizedSignal) -> bool:
        if not self._config.enabled:
            return True
        return False

    def get_final_signal(self, decision_id: str) -> SizedSignal | None:
        decision = self._find_decision(decision_id)
        if decision is None:
            return None
        if decision.action == DecisionAction.APPROVE:
            return decision.original_signal
        if decision.action == DecisionAction.MODIFY and decision.modified_signal:
            return decision.modified_signal
        return None

    def get_status(self, decision_id: str) -> str:
        decision = self._find_decision(decision_id)
        if decision is None:
            return "NOT_FOUND"
        return decision.action.value

    def clear_history(self) -> None:
        self._history = []

    def _find_decision(self, decision_id: str) -> UserDecision | None:
        for d in self._history:
            if d.decision_id == decision_id:
                return d
        return None
