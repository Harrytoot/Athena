from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from decimal import Decimal
from enum import Enum


class MarketId(str, Enum):
    A_SHARE = "a_share"
    US = "us"
    CRYPTO = "crypto"
    HK = "hk"
    FUTURES_CN = "futures_cn"


@dataclass
class TradingSession:
    open_time: time
    close_time: time
    name: str = ""

    def is_open(self, check_time: time) -> bool:
        if self.open_time <= self.close_time:
            return self.open_time <= check_time <= self.close_time
        return check_time >= self.open_time or check_time <= self.close_time


@dataclass
class MarketProfile:
    market_id: MarketId
    name: str = ""
    currency: str = "CNY"
    trading_sessions: list[TradingSession] = field(default_factory=list)
    lot_size: Decimal = Decimal("1")
    min_lot_size: Decimal = Decimal("1")
    tick_size: Decimal = Decimal("0.01")
    price_limit_pct: Decimal = Decimal("10")
    enable_short_selling: bool = False
    uptick_rule_required: bool = False
    t_plus_settlement: int = 1
    max_order_quantity: Decimal = Decimal("100000000")

    def validate_lot_size(self, quantity: Decimal) -> bool:
        if self.lot_size <= 0:
            return True
        remainder = quantity % self.lot_size
        return remainder == 0

    def validate_price_tick(self, price: Decimal) -> bool:
        if self.tick_size <= 0:
            return True
        remainder = price % self.tick_size
        return remainder == 0


A_SHARE_PROFILE = MarketProfile(
    market_id=MarketId.A_SHARE,
    name="A股",
    currency="CNY",
    trading_sessions=[
        TradingSession(open_time=time(9, 30), close_time=time(11, 30), name="morning"),
        TradingSession(open_time=time(13, 0), close_time=time(15, 0), name="afternoon"),
    ],
    lot_size=Decimal("100"),
    min_lot_size=Decimal("100"),
    tick_size=Decimal("0.01"),
    price_limit_pct=Decimal("10"),
    enable_short_selling=False,
    uptick_rule_required=False,
    t_plus_settlement=1,
    max_order_quantity=Decimal("1000000"),
)

US_PROFILE = MarketProfile(
    market_id=MarketId.US,
    name="US Equities",
    currency="USD",
    trading_sessions=[
        TradingSession(open_time=time(9, 30), close_time=time(16, 0), name="regular"),
        TradingSession(open_time=time(4, 0), close_time=time(9, 30), name="pre_market"),
        TradingSession(open_time=time(16, 0), close_time=time(20, 0), name="after_hours"),
    ],
    lot_size=Decimal("1"),
    min_lot_size=Decimal("1"),
    tick_size=Decimal("0.01"),
    price_limit_pct=Decimal("0"),
    enable_short_selling=True,
    uptick_rule_required=True,
    t_plus_settlement=2,
    max_order_quantity=Decimal("10000000"),
)

CRYPTO_PROFILE = MarketProfile(
    market_id=MarketId.CRYPTO,
    name="Crypto",
    currency="USD",
    trading_sessions=[],
    lot_size=Decimal("0.00000001"),
    min_lot_size=Decimal("0.00000001"),
    tick_size=Decimal("0.01"),
    price_limit_pct=Decimal("0"),
    enable_short_selling=True,
    uptick_rule_required=False,
    t_plus_settlement=0,
    max_order_quantity=Decimal("100000"),
)

HK_PROFILE = MarketProfile(
    market_id=MarketId.HK,
    name="港股",
    currency="HKD",
    trading_sessions=[
        TradingSession(open_time=time(9, 30), close_time=time(12, 0), name="morning"),
        TradingSession(open_time=time(13, 0), close_time=time(16, 0), name="afternoon"),
    ],
    lot_size=Decimal("1"),
    min_lot_size=Decimal("1"),
    tick_size=Decimal("0.01"),
    price_limit_pct=Decimal("0"),
    enable_short_selling=True,
    uptick_rule_required=False,
    t_plus_settlement=2,
    max_order_quantity=Decimal("10000000"),
)

FUTURES_CN_PROFILE = MarketProfile(
    market_id=MarketId.FUTURES_CN,
    name="中国期货",
    currency="CNY",
    trading_sessions=[
        TradingSession(open_time=time(9, 0), close_time=time(10, 15), name="morning_1"),
        TradingSession(open_time=time(10, 30), close_time=time(11, 30), name="morning_2"),
        TradingSession(open_time=time(13, 30), close_time=time(15, 0), name="afternoon"),
        TradingSession(open_time=time(21, 0), close_time=time(23, 0), name="night"),
    ],
    lot_size=Decimal("1"),
    min_lot_size=Decimal("1"),
    tick_size=Decimal("1"),
    price_limit_pct=Decimal("10"),
    enable_short_selling=True,
    uptick_rule_required=False,
    t_plus_settlement=0,
    max_order_quantity=Decimal("10000"),
)

DEFAULT_PROFILES = {
    MarketId.A_SHARE: A_SHARE_PROFILE,
    MarketId.US: US_PROFILE,
    MarketId.CRYPTO: CRYPTO_PROFILE,
    MarketId.HK: HK_PROFILE,
    MarketId.FUTURES_CN: FUTURES_CN_PROFILE,
}


@dataclass
class ExchangeRuleCheckResult:
    passed: bool = True
    market_id: str = ""
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    trading_hours_ok: bool = True
    lot_size_ok: bool = True
    price_tick_ok: bool = True
    short_selling_ok: bool = True
    price_limit_ok: bool = True
    quantity_limit_ok: bool = True

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


class ExchangeRulesEngine:

    def __init__(self, profiles: dict[MarketId, MarketProfile] | None = None):
        self._profiles = dict(profiles) if profiles else dict(DEFAULT_PROFILES)

    def register_profile(self, profile: MarketProfile):
        self._profiles[profile.market_id] = profile

    def get_profile(self, market_id: MarketId | str) -> MarketProfile | None:
        if isinstance(market_id, str):
            try:
                market_id = MarketId(market_id)
            except ValueError:
                return None
        return self._profiles.get(market_id)

    def check_order(
        self,
        market_id: MarketId | str,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        reference_price: Decimal | None = None,
        check_time: datetime | None = None,
    ) -> ExchangeRuleCheckResult:
        profile = self.get_profile(market_id)
        if profile is None:
            return ExchangeRuleCheckResult(
                passed=False,
                market_id=str(market_id),
                violations=[f"Unknown market: {market_id}"],
            )

        result = ExchangeRuleCheckResult(market_id=profile.market_id.value)

        if isinstance(quantity, (int, float)):
            quantity = Decimal(str(quantity))
        if isinstance(price, (int, float)):
            price = Decimal(str(price))

        if check_time is not None:
            check_t = check_time.time()
            if profile.trading_sessions:
                in_session = any(session.is_open(check_t) for session in profile.trading_sessions)
                if not in_session:
                    result.trading_hours_ok = False
                    result.violations.append(
                        f"Market {profile.name} is closed at {check_t}"
                    )
            else:
                result.warnings.append(f"No trading sessions defined for {profile.name}")

        if quantity > profile.max_order_quantity:
            result.quantity_limit_ok = False
            result.violations.append(
                f"Quantity {quantity} exceeds max {profile.max_order_quantity} for {profile.name}"
            )

        if not profile.validate_lot_size(quantity):
            result.lot_size_ok = False
            result.violations.append(
                f"Quantity {quantity} does not match lot size {profile.lot_size} for {profile.name}"
            )

        if not profile.validate_price_tick(price):
            result.price_tick_ok = False
            result.violations.append(
                f"Price {price} does not match tick size {profile.tick_size} for {profile.name}"
            )

        side_lower = side.lower() if isinstance(side, str) else side
        if side_lower == "sell" and not profile.enable_short_selling:
            result.short_selling_ok = False
            result.violations.append(
                f"Short selling not allowed on {profile.name}"
            )

        if profile.price_limit_pct > 0 and reference_price is not None:
            if isinstance(reference_price, (int, float)):
                reference_price = Decimal(str(reference_price))
            if reference_price > 0:
                limit = reference_price * profile.price_limit_pct / Decimal("100")
                upper = reference_price + limit
                lower = reference_price - limit

                if price > upper or price < lower:
                    result.price_limit_ok = False
                    result.violations.append(
                        f"Price {price} outside limits [{lower}, {upper}] ({profile.price_limit_pct}% limit)"
                    )

        result.passed = not result.has_violations
        return result

    def check_trading_hours(
        self,
        market_id: MarketId | str,
        check_time: datetime | None = None,
    ) -> ExchangeRuleCheckResult:
        if check_time is None:
            check_time = datetime.now(timezone.utc)

        profile = self.get_profile(market_id)
        if profile is None:
            return ExchangeRuleCheckResult(
                passed=False,
                market_id=str(market_id),
                violations=[f"Unknown market: {market_id}"],
            )

        result = ExchangeRuleCheckResult(market_id=profile.market_id.value)
        check_t = check_time.time()

        if not profile.trading_sessions:
            result.warnings.append(f"No trading sessions defined — always open for {profile.name}")
            return result

        in_session = any(session.is_open(check_t) for session in profile.trading_sessions)
        if not in_session:
            result.trading_hours_ok = False
            result.passed = False
            result.violations.append(
                f"Market {profile.name} closed at {check_t}. Sessions: "
                + ", ".join(f"{s.name or ''} {s.open_time}-{s.close_time}" for s in profile.trading_sessions)
            )

        return result

    def get_settlement_days(self, market_id: MarketId | str) -> int:
        profile = self.get_profile(market_id)
        if profile is None:
            return 1
        return profile.t_plus_settlement

    def list_markets(self) -> list[MarketId]:
        return list(self._profiles.keys())

    def get_profile_summary(self, market_id: MarketId | str) -> dict:
        profile = self.get_profile(market_id)
        if profile is None:
            return {"error": f"Unknown market: {market_id}"}
        return {
            "market_id": profile.market_id.value,
            "name": profile.name,
            "currency": profile.currency,
            "lot_size": str(profile.lot_size),
            "tick_size": str(profile.tick_size),
            "price_limit_pct": str(profile.price_limit_pct),
            "short_selling": profile.enable_short_selling,
            "t_plus": profile.t_plus_settlement,
            "sessions": [
                {"open": str(s.open_time), "close": str(s.close_time), "name": s.name}
                for s in profile.trading_sessions
            ],
        }
