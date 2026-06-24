from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Position:
    id: Optional[str] = None
    symbol: str = ""
    name: str = ""
    shares: Decimal = Decimal("0")
    cost_price: Decimal = Decimal("0")
    current_price: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    @property
    def cost_value(self) -> Decimal:
        return self.shares * self.cost_price

    @property
    def market_value(self) -> Decimal:
        if self.current_price is None:
            return self.cost_value
        return self.shares * self.current_price

    @property
    def pnl(self) -> Decimal:
        return self.market_value - self.cost_value

    @property
    def pnl_pct(self) -> Decimal:
        if self.cost_value == 0:
            return Decimal("0")
        return (self.pnl / self.cost_value) * Decimal("100")


@dataclass
class Portfolio:
    id: Optional[str] = None
    name: str = ""
    cash: Decimal = Decimal("0")
    positions: list[Position] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def total_cost(self) -> Decimal:
        return sum((p.cost_value for p in self.positions), Decimal("0"))

    @property
    def total_market_value(self) -> Decimal:
        return sum((p.market_value for p in self.positions), Decimal("0"))

    @property
    def total_assets(self) -> Decimal:
        return self.cash + self.total_market_value

    @property
    def total_pnl(self) -> Decimal:
        return self.total_market_value - self.total_cost

    @property
    def total_pnl_pct(self) -> Decimal:
        if self.total_cost == 0:
            return Decimal("0")
        return (self.total_pnl / self.total_cost) * Decimal("100")

    @property
    def position_count(self) -> int:
        return len(self.positions)

    def add_position(self, position: Position):
        for p in self.positions:
            if p.symbol == position.symbol:
                return
        self.positions.append(position)

    def remove_position(self, position_id: str):
        self.positions = [p for p in self.positions if p.id != position_id]

    def get_weight(self, position: Position) -> Decimal:
        if self.total_assets == 0:
            return Decimal("0")
        return (position.market_value / self.total_assets) * Decimal("100")
