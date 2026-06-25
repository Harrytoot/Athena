from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class Currency:
    CNY = "CNY"
    USD = "USD"
    HKD = "HKD"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = Currency.CNY

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if self.amount.is_nan() or self.amount.is_infinite():
            raise ValueError(f"Amount must be a finite number, got {self.amount}")

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency})"

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int | float) -> Money:
        if isinstance(factor, float):
            factor = Decimal(str(factor))
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __truediv__(self, divisor: Decimal | int | float) -> Money:
        if isinstance(divisor, (int, float)):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Money(self.amount / divisor, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount >= other.amount

    def _check_currency(self, other: Money):
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} vs {other.currency}"
            )

    def is_zero(self) -> bool:
        return self.amount == 0

    def is_positive(self) -> bool:
        return self.amount > 0

    def is_negative(self) -> bool:
        return self.amount < 0

    def round(self, precision: int = 2) -> Money:
        quantize_str = "0." + "0" * precision
        quantized = self.amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        return Money(quantized, self.currency)

    @classmethod
    def zero(cls, currency: str = Currency.CNY) -> Money:
        return cls(Decimal("0"), currency)

    @classmethod
    def from_cny(cls, amount: Decimal | int | float | str) -> Money:
        return cls(Decimal(str(amount)), Currency.CNY)
