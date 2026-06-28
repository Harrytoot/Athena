from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class TradeAction(Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class TradeRecord:
    id: str
    order_id: str
    strategy_id: str
    symbol: str
    action: TradeAction
    quantity: Decimal
    price: Decimal
    filled_quantity: Decimal
    average_fill_price: Decimal
    commission: Decimal
    slippage_bps: Decimal
    status: TradeStatus
    broker: str
    submitted_at: datetime
    filled_at: Optional[datetime]
    rejection_reason: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        order_id: str,
        strategy_id: str,
        symbol: str,
        action: TradeAction,
        quantity: Decimal,
        price: Decimal,
        broker: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TradeRecord":
        return cls(
            id=str(uuid.uuid4()),
            order_id=order_id,
            strategy_id=strategy_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            filled_quantity=Decimal("0"),
            average_fill_price=Decimal("0"),
            commission=Decimal("0"),
            slippage_bps=Decimal("0"),
            status=TradeStatus.PENDING,
            broker=broker,
            submitted_at=datetime.now(timezone.utc),
            filled_at=None,
            rejection_reason=None,
            metadata=metadata or {},
        )

    def is_complete(self) -> bool:
        return self.status in (TradeStatus.FILLED, TradeStatus.REJECTED, TradeStatus.CANCELLED)


@dataclass
class TradeAuditLog:
    records: List[TradeRecord] = field(default_factory=list)
    max_records: int = 10000

    def record(self, trade: TradeRecord) -> None:
        self.records.append(trade)
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]

    def get_by_order_id(self, order_id: str) -> Optional[TradeRecord]:
        for r in reversed(self.records):
            if r.order_id == order_id:
                return r
        return None

    def get_by_id(self, trade_id: str) -> Optional[TradeRecord]:
        for r in self.records:
            if r.id == trade_id:
                return r
        return None

    def get_by_symbol(self, symbol: str, limit: int = 50) -> List[TradeRecord]:
        matches = [r for r in self.records if r.symbol == symbol]
        return matches[-limit:]

    def get_by_strategy(self, strategy_id: str, limit: int = 50) -> List[TradeRecord]:
        matches = [r for r in self.records if r.strategy_id == strategy_id]
        return matches[-limit:]

    def get_by_status(self, status: TradeStatus, limit: int = 50) -> List[TradeRecord]:
        matches = [r for r in self.records if r.status == status]
        return matches[-limit:]

    def get_total_filled(self, symbol: str) -> Decimal:
        return sum(
            (r.filled_quantity for r in self.records if r.symbol == symbol and r.status == TradeStatus.FILLED),
            Decimal("0"),
        )

    def get_total_commission(self, symbol: str) -> Decimal:
        return sum(
            (r.commission for r in self.records if r.symbol == symbol and r.status == TradeStatus.FILLED),
            Decimal("0"),
        )

    def clear(self) -> None:
        self.records.clear()
