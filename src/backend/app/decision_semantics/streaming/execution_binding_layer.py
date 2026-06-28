import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.schema import DecisionSemantic


@dataclass
class ExecutionIntent:
    symbol: str
    action: str
    target_notional: float
    reference_price: float
    confidence: float
    strategy_id: str
    urgency: str
    reasoning: str
    intent_id: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.intent_id:
            self.intent_id = self._compute_id()

    def _compute_id(self) -> str:
        raw = json.dumps({
            "symbol": self.symbol,
            "action": self.action,
            "target_notional": self.target_notional,
            "strategy_id": self.strategy_id,
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def is_active(self) -> bool:
        return self.action in ("BUY", "SELL")

    @property
    def side(self) -> str:
        if self.action == "BUY":
            return "buy"
        if self.action == "SELL":
            return "sell"
        return "hold"

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "target_notional": self.target_notional,
            "reference_price": self.reference_price,
            "confidence": self.confidence,
            "strategy_id": self.strategy_id,
            "urgency": self.urgency,
            "reasoning": self.reasoning,
            "intent_id": self.intent_id,
        }

    def to_execution_order(self) -> dict:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "notional": self.target_notional,
            "price": self.reference_price,
            "strategy_id": self.strategy_id,
        }


@dataclass
class ExecutionBinding:
    intent: ExecutionIntent
    semantic_snapshot: DecisionSemantic | None = None
    is_routed: bool = False
    routed_at: str = ""
    error_message: str = ""


@dataclass
class ExecutionBindingResult:
    executions: list[ExecutionBinding] = field(default_factory=list)
    blocked_executions: list[ExecutionBinding] = field(default_factory=list)
    portfolio_issues: list[str] = field(default_factory=list)
    processed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def total_intents(self) -> int:
        return len(self.executions) + len(self.blocked_executions)

    @property
    def success_rate(self) -> float:
        if self.total_intents == 0:
            return 1.0
        return len(self.executions) / self.total_intents


_ACTION_MAP: dict[str, str] = {
    "APPROVE": "BUY",
    "REJECT": "SELL",
    "HOLD": "HOLD",
    "BUY": "BUY",
    "SELL": "SELL",
}

_URGENCY_MAP: dict[str, str] = {
    "APPROVE": "IMMEDIATE",
    "REJECT": "IMMEDIATE",
    "HOLD": "PASSIVE",
    "BUY": "NORMAL",
    "SELL": "NORMAL",
}


class ExecutionBindingLayer:

    def __init__(self, default_notional: float = 10000.0, default_price: float = 100.0):
        self._default_notional = default_notional
        self._default_price = default_price
        self._executions: dict[str, ExecutionBinding] = {}
        self._history: list[ExecutionBinding] = []

    def bind(
        self,
        semantic: DecisionSemantic,
        notional_override: float | None = None,
        price_override: float | None = None,
    ) -> ExecutionIntent:
        action = _ACTION_MAP.get(semantic.action, "HOLD")
        urgency = _URGENCY_MAP.get(semantic.action, "PASSIVE")

        notional = notional_override or self._default_notional
        reference_price = price_override or self._default_price

        if semantic.execution:
            if semantic.execution.estimated_slippage_bps > 50.0:
                urgency = "PASSIVE"

        intent = ExecutionIntent(
            symbol=semantic.symbol,
            action=action,
            target_notional=notional,
            reference_price=reference_price,
            confidence=semantic.confidence_score,
            strategy_id=semantic.name,
            urgency=urgency,
            reasoning=semantic.summary,
            metadata={
                "feasibility": semantic.execution.feasibility if semantic.execution else 0.5,
                "estimated_slippage_bps": semantic.execution.estimated_slippage_bps if semantic.execution else 0.0,
                "quality_grade": semantic.execution.quality_grade if semantic.execution else "C",
            },
        )

        binding = ExecutionBinding(
            intent=intent,
            semantic_snapshot=semantic,
        )

        self._executions[semantic.symbol] = binding
        self._history.append(binding)

        return intent

    def bind_portfolio(
        self,
        semantics: dict[str, DecisionSemantic],
        notional_overrides: dict[str, float] | None = None,
        price_overrides: dict[str, float] | None = None,
    ) -> ExecutionBindingResult:
        if notional_overrides is None:
            notional_overrides = {}
        if price_overrides is None:
            price_overrides = {}

        executions: list[ExecutionBinding] = []
        blocked: list[ExecutionBinding] = []
        issues: list[str] = []

        for symbol, semantic in semantics.items():
            action = _ACTION_MAP.get(semantic.action, "HOLD")
            urgency = _URGENCY_MAP.get(semantic.action, "PASSIVE")

            notional = notional_overrides.get(symbol, self._default_notional)
            reference_price = price_overrides.get(symbol, self._default_price)

            if semantic.execution:
                if semantic.execution.estimated_slippage_bps > 50.0:
                    urgency = "PASSIVE"

            intent = ExecutionIntent(
                symbol=semantic.symbol,
                action=action,
                target_notional=notional,
                reference_price=reference_price,
                confidence=semantic.confidence_score,
                strategy_id=semantic.name,
                urgency=urgency,
                reasoning=semantic.summary,
                metadata={
                    "feasibility": semantic.execution.feasibility if semantic.execution else 0.5,
                    "estimated_slippage_bps": semantic.execution.estimated_slippage_bps if semantic.execution else 0.0,
                    "quality_grade": semantic.execution.quality_grade if semantic.execution else "C",
                },
            )

            binding = ExecutionBinding(
                intent=intent,
                semantic_snapshot=semantic,
            )

            if intent.action == "HOLD":
                binding.is_routed = False
            else:
                if semantic.execution and semantic.execution.feasibility < 0.3:
                    binding.is_routed = False
                    binding.error_message = f"Low feasibility: {semantic.execution.feasibility}"
                    blocked.append(binding)
                    issues.append(f"{symbol}: blocked due to low feasibility ({semantic.execution.feasibility})")
                else:
                    binding.is_routed = True
                    binding.routed_at = datetime.now(timezone.utc).isoformat()
                    executions.append(binding)

            self._executions[symbol] = binding
            self._history.append(binding)

        return ExecutionBindingResult(
            executions=executions,
            blocked_executions=blocked,
            portfolio_issues=issues,
        )

    def validate_portfolio_consistency(
        self, blocked_intents: list[str], conflict_pairs: list[tuple[str, str]]
    ) -> bool:
        active_intents = {
            sym: b.intent
            for sym, b in self._executions.items()
            if b.is_routed
        }

        for sym in blocked_intents:
            if sym in active_intents:
                return False

        for sym_a, sym_b in conflict_pairs:
            intent_a = active_intents.get(sym_a)
            intent_b = active_intents.get(sym_b)
            if intent_a is None or intent_b is None:
                continue
            if intent_a.action != intent_b.action:
                return False

        return True

    def get_intent(self, symbol: str) -> ExecutionIntent | None:
        binding = self._executions.get(symbol)
        if binding is None:
            return None
        return binding.intent

    def get_active_intents(self) -> dict[str, ExecutionIntent]:
        return {
            sym: b.intent
            for sym, b in self._executions.items()
            if b.is_routed and b.error_message == ""
        }

    def get_all_intents(self) -> dict[str, ExecutionIntent]:
        return {sym: b.intent for sym, b in self._executions.items()}

    def get_blocked_intents(self) -> dict[str, ExecutionBinding]:
        return {
            sym: b for sym, b in self._executions.items()
            if not b.is_routed or b.error_message != ""
        }

    def get_binding_history(self) -> list[ExecutionBinding]:
        return list(self._history)

    def reset(self) -> None:
        self._executions.clear()
        self._history.clear()
