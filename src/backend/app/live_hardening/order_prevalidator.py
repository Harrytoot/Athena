from dataclasses import dataclass, field
from decimal import Decimal

DEFAULT_MAX_ORDER_NOTIONAL = Decimal("100000000")
DEFAULT_MIN_ORDER_NOTIONAL = Decimal("0.01")
DEFAULT_MAX_QUANTITY = Decimal("100000000")
DEFAULT_MAX_PRICE = Decimal("100000000")


@dataclass
class PrevalidationResult:
    passed: bool = True
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalized_symbol: str = ""
    normalized_side: str = ""
    normalized_quantity: Decimal = Decimal("0")
    normalized_price: Decimal = Decimal("0")

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class OrderPrevalidator:

    def __init__(
        self,
        max_order_notional: Decimal = DEFAULT_MAX_ORDER_NOTIONAL,
        min_order_notional: Decimal = DEFAULT_MIN_ORDER_NOTIONAL,
        max_quantity: Decimal = DEFAULT_MAX_QUANTITY,
        max_price: Decimal = DEFAULT_MAX_PRICE,
        allowed_sides: set[str] | None = None,
    ):
        self.max_order_notional = max_order_notional
        self.min_order_notional = min_order_notional
        self.max_quantity = max_quantity
        self.max_price = max_price
        self.allowed_sides = allowed_sides or {"buy", "sell"}

    def validate(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        order_type: str = "market",
        strategy_id: str | None = None,
    ) -> PrevalidationResult:
        result = PrevalidationResult()

        symbol = (symbol or "").strip().upper()
        if not symbol:
            result.violations.append("Symbol is empty")
        result.normalized_symbol = symbol

        side = (side or "").strip().lower()
        if not side:
            result.violations.append("Side is empty")
        elif side not in self.allowed_sides:
            result.violations.append(
                f"Invalid side '{side}'. Allowed: {sorted(self.allowed_sides)}"
            )
        result.normalized_side = side

        if isinstance(quantity, (int, float)):
            quantity = Decimal(str(quantity))
        if not isinstance(quantity, Decimal):
            result.violations.append(f"Invalid quantity type: {type(quantity).__name__}")
            quantity = Decimal("0")
        if quantity <= 0:
            result.violations.append(f"Quantity must be positive, got {quantity}")
        if quantity > self.max_quantity:
            result.violations.append(
                f"Quantity {quantity} exceeds max {self.max_quantity}"
            )
        result.normalized_quantity = quantity

        if isinstance(price, (int, float)):
            price = Decimal(str(price))
        if not isinstance(price, Decimal):
            result.violations.append(f"Invalid price type: {type(price).__name__}")
            price = Decimal("0")
        if price <= 0:
            result.violations.append(f"Price must be positive, got {price}")
        if price > self.max_price:
            result.violations.append(
                f"Price {price} exceeds max {self.max_price}"
            )
        result.normalized_price = price

        notional = quantity * price
        if notional > self.max_order_notional:
            result.violations.append(
                f"Order notional {notional} exceeds max {self.max_order_notional}"
            )

        if notional < self.min_order_notional and notional > 0:
            result.violations.append(
                f"Order notional {notional} below min {self.min_order_notional}"
            )

        if order_type not in ("market", "limit"):
            result.violations.append(f"Unknown order type: {order_type}")

        if strategy_id is not None and not isinstance(strategy_id, str):
            result.violations.append(f"Invalid strategy_id type: {type(strategy_id).__name__}")

        if notional > 0:
            if quantity > 0 and notional / quantity != price:
                result.warnings.append("Notional/quantity mismatch with price")

        if price > 0 and quantity > 0 and notional > self.max_order_notional * Decimal("0.5"):
            result.warnings.append(
                f"Large order detected: {notional} notional"
            )

        result.passed = not result.has_violations
        return result

    def validate_batch(
        self,
        orders: list[dict],
    ) -> list[PrevalidationResult]:
        results: list[PrevalidationResult] = []
        seen_symbols: set[str] = set()

        for order in orders:
            result = self.validate(
                symbol=order.get("symbol", ""),
                side=order.get("side", "buy"),
                quantity=Decimal(str(order.get("quantity", "0"))),
                price=Decimal(str(order.get("price", "0"))),
                order_type=order.get("order_type", "market"),
                strategy_id=order.get("strategy_id"),
            )
            results.append(result)

            if result.passed:
                sym = result.normalized_symbol
                if sym in seen_symbols:
                    result.warnings.append(f"Duplicate order for symbol {sym}")
                seen_symbols.add(sym)

        return results

    def validate_single_field(
        self,
        symbol: str = "",
        side: str = "",
        quantity: Decimal | None = None,
        price: Decimal | None = None,
    ) -> PrevalidationResult:
        result = PrevalidationResult()

        if symbol:
            sym = symbol.strip().upper()
            if not sym:
                result.violations.append("Symbol is empty after normalization")
            result.normalized_symbol = sym

        if side:
            s = side.strip().lower()
            if s not in self.allowed_sides:
                result.violations.append(f"Invalid side: {s}")
            result.normalized_side = s

        if quantity is not None:
            if isinstance(quantity, (int, float)):
                quantity = Decimal(str(quantity))
            if quantity <= 0:
                result.violations.append(f"Quantity must be positive: {quantity}")
            if quantity > self.max_quantity:
                result.violations.append(f"Quantity {quantity} exceeds max")
            result.normalized_quantity = quantity

        if price is not None:
            if isinstance(price, (int, float)):
                price = Decimal(str(price))
            if price <= 0:
                result.violations.append(f"Price must be positive: {price}")
            if price > self.max_price:
                result.violations.append(f"Price {price} exceeds max")
            result.normalized_price = price

        result.passed = not result.has_violations
        return result
