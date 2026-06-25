from decimal import Decimal

import pytest

from app.domain.value_objects.Percentage import Percentage


class TestPercentage:

    def test_create(self):
        p = Percentage(Decimal("15.50"))
        assert p.value == Decimal("15.50")

    def test_create_from_float_coerces(self):
        p = Percentage(Decimal("15.50"))
        assert p.value == Decimal("15.50")

    def test_str(self):
        p = Percentage(Decimal("15.50"))
        assert str(p) == "15.50%"

    def test_repr(self):
        p = Percentage(Decimal("15.50"))
        assert "Percentage(15.50)" == repr(p)

    def test_add(self):
        assert Percentage(Decimal("10")) + Percentage(Decimal("5")) == Percentage(Decimal("15"))

    def test_sub(self):
        assert Percentage(Decimal("10")) - Percentage(Decimal("3")) == Percentage(Decimal("7"))

    def test_mul(self):
        assert Percentage(Decimal("10")) * 2 == Percentage(Decimal("20"))

    def test_truediv(self):
        assert Percentage(Decimal("10")) / 2 == Percentage(Decimal("5"))

    def test_truediv_by_zero_raises(self):
        with pytest.raises(ValueError, match="divide by zero"):
            Percentage(Decimal("10")) / 0

    def test_comparison_lt(self):
        assert Percentage(Decimal("10")) < Percentage(Decimal("20"))

    def test_comparison_gt(self):
        assert Percentage(Decimal("20")) > Percentage(Decimal("10"))

    def test_comparison_eq(self):
        assert Percentage(Decimal("10")) == Percentage(Decimal("10"))

    def test_is_zero(self):
        assert Percentage.zero().is_zero()
        assert not Percentage(Decimal("10")).is_zero()

    def test_is_positive(self):
        assert Percentage(Decimal("10")).is_positive()
        assert not Percentage.zero().is_positive()

    def test_is_negative(self):
        assert Percentage(Decimal("-5")).is_negative()
        assert not Percentage.zero().is_negative()

    def test_as_decimal_ratio(self):
        p = Percentage(Decimal("25"))
        assert p.as_decimal_ratio == Decimal("0.25")

    def test_as_decimal_ratio_negative(self):
        p = Percentage(Decimal("-10"))
        assert p.as_decimal_ratio == Decimal("-0.10")

    def test_basis_points(self):
        p = Percentage(Decimal("1"))
        assert p.basis_points == Decimal("100")

    def test_round(self):
        p = Percentage(Decimal("15.556"))
        assert p.round(2) == Percentage(Decimal("15.56"))

    def test_from_decimal_ratio(self):
        p = Percentage.from_decimal_ratio(Decimal("0.25"))
        assert p == Percentage(Decimal("25"))

    def test_from_decimal_ratio_negative(self):
        p = Percentage.from_decimal_ratio(Decimal("-0.10"))
        assert p == Percentage(Decimal("-10"))

    def test_frozen(self):
        p = Percentage(Decimal("10"))
        with pytest.raises(Exception):
            p.value = Decimal("20")  # type: ignore

    def test_precision_no_float_drift(self):
        a = Percentage(Decimal("0.1"))
        b = Percentage(Decimal("0.2"))
        total = a + b
        assert total.value == Decimal("0.3")


class TestPercentageEdgeCases:

    def test_zero_percentage(self):
        p = Percentage.zero()
        assert p.as_decimal_ratio == Decimal("0")
        assert p.basis_points == Decimal("0")

    def test_hundred_percent(self):
        p = Percentage(Decimal("100"))
        assert p.as_decimal_ratio == Decimal("1")

    def test_small_fraction(self):
        p = Percentage(Decimal("0.01"))
        assert p.basis_points == Decimal("1")
