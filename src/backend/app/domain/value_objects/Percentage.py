from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


@dataclass(frozen=True)
class Percentage:
    value: Decimal

    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))
        if self.value.is_nan() or self.value.is_infinite():
            raise ValueError(f"Percentage value must be finite, got {self.value}")

    def __str__(self) -> str:
        return f"{self.value}%"

    def __repr__(self) -> str:
        return f"Percentage({self.value})"

    def __add__(self, other: Percentage) -> Percentage:
        return Percentage(self.value + other.value)

    def __sub__(self, other: Percentage) -> Percentage:
        return Percentage(self.value - other.value)

    def __mul__(self, factor: Decimal | int | float) -> Percentage:
        if isinstance(factor, float):
            factor = Decimal(str(factor))
        return Percentage(self.value * Decimal(str(factor)))

    def __truediv__(self, divisor: Decimal | int | float) -> Percentage:
        if isinstance(divisor, (int, float)):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Percentage(self.value / divisor)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: Percentage) -> bool:
        return self.value < other.value

    def __le__(self, other: Percentage) -> bool:
        return self.value <= other.value

    def __gt__(self, other: Percentage) -> bool:
        return self.value > other.value

    def __ge__(self, other: Percentage) -> bool:
        return self.value >= other.value

    def is_zero(self) -> bool:
        return self.value == 0

    def is_positive(self) -> bool:
        return self.value > 0

    def is_negative(self) -> bool:
        return self.value < 0

    @property
    def as_decimal_ratio(self) -> Decimal:
        return self.value / Decimal("100")

    @property
    def basis_points(self) -> Decimal:
        return self.value * Decimal("100")

    def round(self, precision: int = 2) -> Percentage:
        quantize_str = "0." + "0" * precision
        quantized = self.value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        return Percentage(quantized)

    @classmethod
    def zero(cls) -> Percentage:
        return cls(Decimal("0"))

    @classmethod
    def from_decimal_ratio(cls, ratio: Decimal | float | str) -> Percentage:
        return cls(Decimal(str(ratio)) * Decimal("100"))
