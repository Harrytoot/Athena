import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    level: LogLevel = LogLevel.INFO
    event: str = ""
    order_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    quantity: str | None = None
    price: str | None = None
    notional: str | None = None
    status: str | None = None
    strategy_id: str | None = None
    message: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "event": self.event,
        }
        if self.order_id:
            d["order_id"] = self.order_id
        if self.symbol:
            d["symbol"] = self.symbol
        if self.side:
            d["side"] = self.side
        if self.quantity:
            d["quantity"] = self.quantity
        if self.price:
            d["price"] = self.price
        if self.notional:
            d["notional"] = self.notional
        if self.status:
            d["status"] = self.status
        if self.strategy_id:
            d["strategy_id"] = self.strategy_id
        if self.message:
            d["message"] = self.message
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class ExecutionLogger:

    def __init__(self, log_dir: str | None = None, max_memory_entries: int = 10000):
        self._entries: list[LogEntry] = []
        self._max_memory_entries = max_memory_entries
        self._log_dir = Path(log_dir) if log_dir else None
        self._session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._file_handle = None
        if self._log_dir:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self._log_dir / f"execution_{self._session_id}.log"
            self._file_handle = open(str(log_path), "a", encoding="utf-8")

    def log(
        self,
        event: str,
        level: LogLevel = LogLevel.INFO,
        order_id: str | None = None,
        symbol: str | None = None,
        side: str | None = None,
        quantity: Decimal | None = None,
        price: Decimal | None = None,
        notional: Decimal | None = None,
        status: str | None = None,
        strategy_id: str | None = None,
        message: str = "",
        metadata: dict | None = None,
    ):
        entry = LogEntry(
            level=level,
            event=event,
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=str(quantity) if quantity is not None else None,
            price=str(price) if price is not None else None,
            notional=str(notional) if notional is not None else None,
            status=status,
            strategy_id=strategy_id,
            message=message,
            metadata=metadata or {},
        )

        self._entries.append(entry)
        if len(self._entries) > self._max_memory_entries:
            self._entries = self._entries[-self._max_memory_entries // 2:]

        if self._file_handle:
            self._file_handle.write(entry.to_json() + "\n")
            self._file_handle.flush()

    def log_order_created(self, order_id: str, symbol: str, side: str, quantity: Decimal, **kwargs):
        self.log(
            event="order_created",
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            **kwargs,
        )

    def log_order_submitted(self, order_id: str, broker_order_id: str, **kwargs):
        self.log(
            event="order_submitted",
            order_id=order_id,
            message=f"Submitted to broker: {broker_order_id}",
            **kwargs,
        )

    def log_order_filled(self, order_id: str, quantity: Decimal, price: Decimal, **kwargs):
        self.log(
            event="order_filled",
            order_id=order_id,
            quantity=quantity,
            price=price,
            notional=quantity * price,
            **kwargs,
        )

    def log_order_rejected(self, order_id: str, reason: str, **kwargs):
        self.log(
            event="order_rejected",
            level=LogLevel.WARNING,
            order_id=order_id,
            message=reason,
            **kwargs,
        )

    def log_order_cancelled(self, order_id: str, **kwargs):
        self.log(
            event="order_cancelled",
            order_id=order_id,
            **kwargs,
        )

    def log_risk_violation(self, message: str, **kwargs):
        self.log(
            event="risk_violation",
            level=LogLevel.WARNING,
            message=message,
            **kwargs,
        )

    def log_kill_switch(self, reason: str, **kwargs):
        self.log(
            event="kill_switch_activated",
            level=LogLevel.CRITICAL,
            message=reason,
            **kwargs,
        )

    def log_engine_cycle(self, cycle_id: str, status: str, **kwargs):
        self.log(
            event="engine_cycle",
            message=f"Cycle {cycle_id}: {status}",
            metadata={"cycle_id": cycle_id, "status": status, **kwargs},
        )

    def log_position_sync(self, sync_result, **kwargs):
        self.log(
            event="position_sync",
            message=f"Reconciled: {sync_result.reconciled}, Changes: {sync_result.change_count}",
            metadata={
                "reconciled": sync_result.reconciled,
                "change_count": sync_result.change_count,
                **kwargs,
            },
        )

    def get_entries(
        self,
        level: LogLevel | None = None,
        event: str | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        entries = self._entries
        if level:
            entries = [e for e in entries if e.level == level]
        if event:
            entries = [e for e in entries if e.event == event]
        return entries[-limit:]

    def get_errors(self, limit: int = 100) -> list[LogEntry]:
        return [
            e for e in self._entries
            if e.level in (LogLevel.ERROR, LogLevel.CRITICAL)
        ][-limit:]

    def get_recent(self, limit: int = 50) -> list[LogEntry]:
        return self._entries[-limit:]

    def entry_count(self) -> int:
        return len(self._entries)

    def flush(self):
        if self._file_handle:
            self._file_handle.flush()

    def close(self):
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
