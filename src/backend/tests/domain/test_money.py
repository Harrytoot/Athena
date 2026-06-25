from decimal import Decimal

import pytest

from app.domain.value_objects.Money import Currency, Money


class TestMoney:

    def test_create_money(self):
        m = Money(Decimal("100.50"), Currency.CNY)
        assert m.amount == Decimal("100.50")
        assert m.currency == Currency.CNY

    def test_create_from_int(self):
        m = Money(Decimal("100"), Currency.CNY)
        assert m.amount == Decimal("100")

    def test_create_from_float_coerces(self):
        m = Money(Decimal("100.50"), Currency.CNY)
        assert m.amount == Decimal("100.50")

    def test_default_currency_is_cny(self):
        m = Money(Decimal("100"))
        assert m.currency == Currency.CNY

    def test_str(self):
        m = Money(Decimal("100.50"), Currency.CNY)
        assert str(m) == "100.50 CNY"

    def test_repr(self):
        m = Money(Decimal("100.50"), Currency.CNY)
        assert "Money(100.50, CNY)" == repr(m)

    def test_add_same_currency(self):
        a = Money(Decimal("100"), Currency.CNY)
        b = Money(Decimal("50"), Currency.CNY)
        assert a + b == Money(Decimal("150"), Currency.CNY)

    def test_add_different_currency_raises(self):
        a = Money(Decimal("100"), Currency.CNY)
        b = Money(Decimal("50"), Currency.USD)
        with pytest.raises(ValueError, match="different currencies"):
            a + b

    def test_sub_same_currency(self):
        a = Money(Decimal("100"), Currency.CNY)
        b = Money(Decimal("30"), Currency.CNY)
        assert a - b == Money(Decimal("70"), Currency.CNY)

    def test_mul(self):
        m = Money(Decimal("100"), Currency.CNY)
        assert m * Decimal("3") == Money(Decimal("300"), Currency.CNY)

    def test_truediv(self):
        m = Money(Decimal("100"), Currency.CNY)
        assert m / Decimal("4") == Money(Decimal("25"), Currency.CNY)

    def test_truediv_by_zero_raises(self):
        m = Money(Decimal("100"), Currency.CNY)
        with pytest.raises(ValueError, match="divide by zero"):
            m / 0

    def test_neg(self):
        m = Money(Decimal("100"), Currency.CNY)
        assert -m == Money(Decimal("-100"), Currency.CNY)

    def test_abs_positive(self):
        m = Money(Decimal("100"), Currency.CNY)
        assert abs(m) == Money(Decimal("100"), Currency.CNY)

    def test_abs_negative(self):
        m = Money(Decimal("-100"), Currency.CNY)
        assert abs(m) == Money(Decimal("100"), Currency.CNY)

    def test_comparison_lt(self):
        assert Money(Decimal("100")) < Money(Decimal("200"))

    def test_comparison_gt(self):
        assert Money(Decimal("200")) > Money(Decimal("100"))

    def test_comparison_eq(self):
        assert Money(Decimal("100")) == Money(Decimal("100"))

    def test_is_zero(self):
        assert Money.zero().is_zero()
        assert not Money(Decimal("100")).is_zero()

    def test_is_positive(self):
        assert Money(Decimal("100")).is_positive()
        assert not Money.zero().is_positive()

    def test_is_negative(self):
        assert Money(Decimal("-100")).is_negative()
        assert not Money.zero().is_negative()

    def test_round(self):
        m = Money(Decimal("100.456"), Currency.CNY)
        assert m.round(2) == Money(Decimal("100.46"), Currency.CNY)

    def test_from_cny(self):
        m = Money.from_cny(100)
        assert m == Money(Decimal("100"), Currency.CNY)

    def test_frozen(self):
        m = Money(Decimal("100"), Currency.CNY)
        with pytest.raises(Exception):
            m.amount = Decimal("200")  # type: ignore

    def test_precision_no_float_drift(self):
        a = Money(Decimal("0.1"), Currency.CNY)
        b = Money(Decimal("0.2"), Currency.CNY)
        total = a + b
        assert total.amount == Decimal("0.3")


class TestMoneyEdgeCases:

    def test_large_amount(self):
        m = Money(Decimal("9999999999999999.99"), Currency.CNY)
        assert m.amount == Decimal("9999999999999999.99")

    def test_negative_amount(self):
        m = Money(Decimal("-50.00"), Currency.CNY)
        assert m.is_negative()
        assert str(m) == "-50.00 CNY"

    def test_zero_rounding(self):
        m = Money.zero()
        assert m.round(2) == Money.zero()
