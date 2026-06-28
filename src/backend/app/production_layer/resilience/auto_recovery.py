from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RecoveryPhase(Enum):
    IDLE = "IDLE"
    DIAGNOSING = "DIAGNOSING"
    MITIGATING = "MITIGATING"
    STABILIZING = "STABILIZING"
    RESTORING = "RESTORING"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True)
class RecoveryAction:
    name: str
    description: str
    phase: RecoveryPhase
    action_fn: str


@dataclass(frozen=True)
class RecoveryStep:
    action: RecoveryAction
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None


@dataclass
class AutoRecovery:
    recovery_actions: Dict[str, Callable[[], bool]] = field(default_factory=dict)
    max_retries: int = 3
    stabilization_period_seconds: int = 30
    recovery_history: List[RecoveryStep] = field(default_factory=list)
    current_phase: RecoveryPhase = RecoveryPhase.IDLE
    phase_started_at: Optional[datetime] = None
    stabilization_started_at: Optional[datetime] = None

    def register_action(self, name: str, fn: Callable[[], bool]) -> None:
        self.recovery_actions[name] = fn

    def is_stabilized(self) -> bool:
        if self.stabilization_started_at is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.stabilization_started_at).total_seconds()
        return elapsed >= self.stabilization_period_seconds

    def execute_recovery(
        self, actions: List[RecoveryAction]
    ) -> List[RecoveryStep]:
        results: List[RecoveryStep] = []
        self.current_phase = RecoveryPhase.MITIGATING

        for action in actions:
            step = RecoveryStep(
                action=action,
                started_at=datetime.now(timezone.utc),
            )
            self.current_phase = action.phase

            success = False
            error_msg = None
            fn = self.recovery_actions.get(action.action_fn)

            if fn is not None:
                for attempt in range(1, self.max_retries + 1):
                    try:
                        if fn():
                            success = True
                            break
                    except Exception as e:
                        error_msg = str(e)

            step = RecoveryStep(
                action=action,
                started_at=step.started_at,
                completed_at=datetime.now(timezone.utc),
                success=success,
                error_message=error_msg,
            )
            results.append(step)
            self.recovery_history.append(step)

            if not success:
                break

        if all(r.success for r in results):
            self.current_phase = RecoveryPhase.STABILIZING
            self.stabilization_started_at = datetime.now(timezone.utc)
        else:
            self.current_phase = RecoveryPhase.IDLE

        return results

    def verify_stabilization(self) -> bool:
        if self.is_stabilized():
            self.current_phase = RecoveryPhase.VERIFIED
            return True
        return False

    def reset(self) -> None:
        self.current_phase = RecoveryPhase.IDLE
        self.stabilization_started_at = None
        self.recovery_history.clear()

    def get_latest_attempt(self) -> List[RecoveryStep]:
        return [s for s in self.recovery_history if s.completed_at is not None]
