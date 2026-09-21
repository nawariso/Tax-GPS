"""Unit tests for the Money value object (TGPS-P1-001 §3.1)."""

from collections.abc import Callable
from decimal import Decimal, localcontext
from operator import ge, gt, le

import pytest

from tax_gps.core.errors import InvalidMoneyError
from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage


class TestConstruction:
    def test_of_accepts_int(self) -> None:
        assert Money.of(990500).amount == Decimal("990500")

    def test_of_accepts_decimal_string(self) -> None:
        assert Money.of("1234.56").amount == Decimal("1234.56")

    def test_of_accepts_decimal(self) -> None:
        assert Money.of(Decimal("10.5")).amount == Decimal("10.5")

    def test_currency_is_thb(self) -> None:
        assert Money.of(1).currency == "THB"

    def test_zero(self) -> None:
        assert Money.zero().is_zero()
        assert Money.zero() == Money.of(0)

    def test_binary_float_is_rejected(self) -> None:
        with pytest.raises(InvalidMoneyError, match="float"):
            Money.of(0.1)  # type: ignore[arg-type]

    def test_bool_is_rejected(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(True)

    @pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "sNaN"])
    def test_non_finite_is_rejected(self, value: str) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(value)

    @pytest.mark.parametrize("value", ["", "abc", "1,000", " 10", "1e3x"])
    def test_malformed_string_is_rejected(self, value: str) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(value)

    def test_input_precision_finer_than_satang_is_rejected(self) -> None:
        with pytest.raises(InvalidMoneyError, match="satang"):
            Money.of("0.001")

    def test_exponent_notation_within_satang_is_accepted(self) -> None:
        assert Money.of("1E+3") == Money.of(1000)

    def test_direct_constructor_rejects_non_decimal(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money(1)  # type: ignore[arg-type]

    def test_direct_constructor_rejects_other_currency(self) -> None:
        with pytest.raises(InvalidMoneyError, match="THB"):
            Money(Decimal(1), currency="USD")

    def test_is_immutable(self) -> None:
        money = Money.of(1)
        with pytest.raises(AttributeError):
            money.amount = Decimal(2)  # type: ignore[misc]

    def test_unsupported_type_is_rejected(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of([1])  # type: ignore[arg-type]


class TestArithmetic:
    def test_add(self) -> None:
        assert Money.of("0.10") + Money.of("0.20") == Money.of("0.30")

    def test_subtract(self) -> None:
        assert Money.of(990500) - Money.of(170500) == Money.of(820000)

    def test_subtract_can_go_negative_internally(self) -> None:
        assert (Money.of(1) - Money.of(2)).is_negative()

    def test_multiply_by_percentage_is_exact(self) -> None:
        assert Money.of("100000.01") * Percentage.of("0.5") == Money(Decimal("50000.005"))

    def test_money_times_money_is_not_supported(self) -> None:
        with pytest.raises(TypeError):
            _ = Money.of(1) * Money.of(1)  # type: ignore[operator]

    def test_add_non_money_is_not_supported(self) -> None:
        with pytest.raises(TypeError):
            _ = Money.of(1) + 1  # type: ignore[operator]

    def test_subtract_non_money_is_not_supported(self) -> None:
        with pytest.raises(TypeError):
            _ = Money.of(1) - 1  # type: ignore[operator]

    def test_min_and_max(self) -> None:
        assert Money.min(Money.of(1), Money.of(2)) == Money.of(1)
        assert Money.max(Money.of(1), Money.of(2)) == Money.of(2)

    def test_floor_at_zero(self) -> None:
        assert Money.of(-5).floor_at_zero() == Money.zero()
        assert Money.of(5).floor_at_zero() == Money.of(5)

    def test_sum(self) -> None:
        assert Money.sum([Money.of(1), Money.of(2), Money.of(3)]) == Money.of(6)
        assert Money.sum([]) == Money.zero()

    def test_times_scales_by_whole_number(self) -> None:
        assert Money.of(50000).times(3) == Money.of(150000)
        assert Money.of(50000).times(0) == Money.zero()

    def test_times_does_not_mutate_the_original(self) -> None:
        original = Money.of(50000)
        scaled = original.times(3)
        assert original == Money.of(50000)
        assert scaled == Money.of(150000)
        assert scaled is not original

    def test_times_preserves_canonical_quantization(self) -> None:
        assert Money.of(50000).times(3).canonical() == "150000.00"
        assert Money.zero().times(5).canonical() == "0.00"

    def test_times_rejects_negative_factor(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(1).times(-1)

    def test_times_rejects_bool_factor(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(1).times(True)

    def test_times_rejects_non_int_factor(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(1).times(1.5)  # type: ignore[arg-type]

    def test_comparisons(self) -> None:
        assert Money.of(1) < Money.of(2)
        assert Money.of(2) <= Money.of(2)
        assert Money.of(3) > Money.of(2)
        assert Money.of(3) >= Money.of(3)

    def test_comparison_with_non_money_is_not_supported(self) -> None:
        with pytest.raises(TypeError):
            _ = Money.of(1) < 2  # type: ignore[operator]

    @pytest.mark.parametrize("compare", [le, gt, ge])
    def test_remaining_comparisons_reject_non_money(
        self, compare: Callable[[object, object], bool]
    ) -> None:
        money = Money.of(1)
        with pytest.raises(TypeError):
            compare(money, 1)

    def test_equality_ignores_trailing_zero_representation(self) -> None:
        assert Money.of("100.00") == Money.of(100)
        assert hash(Money.of("100.00")) == hash(Money.of(100))

    def test_equality_with_non_money_is_false(self) -> None:
        assert Money.of(1) != Decimal(1)

    def test_arithmetic_is_independent_of_ambient_decimal_context(self) -> None:
        with localcontext() as ctx:
            ctx.prec = 3
            assert Money.of("123456789.12") + Money.of("0.01") == Money.of("123456789.13")
            assert Money.of("123456789.12") * Percentage.of("0.05") == Money(Decimal("6172839.456"))

    def test_huge_values_that_would_need_rounding_raise(self) -> None:
        huge = Money(Decimal("1" * 60))
        with pytest.raises(InvalidMoneyError, match="exact"):
            _ = huge + Money(Decimal("0.000000000001"))

    def test_non_finite_decimal_is_rejected_by_factory(self) -> None:
        with pytest.raises(InvalidMoneyError, match="finite"):
            Money.of(Decimal("NaN"))


class TestPredicatesAndFormatting:
    def test_sign_predicates(self) -> None:
        assert Money.of(-1).is_negative()
        assert not Money.of(0).is_negative()
        assert Money.of(1).is_positive()
        assert not Money.of(0).is_positive()

    def test_is_whole_satang(self) -> None:
        assert Money.of("1.25").is_whole_satang()
        assert not Money(Decimal("1.255")).is_whole_satang()

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            ("820000", "820000.00"),
            ("0", "0.00"),
            ("-1.5", "-1.50"),
            ("1E+5", "100000.00"),
            ("50000.005", "50000.005"),
            ("0.12340", "0.1234"),
        ],
    )
    def test_canonical_string(self, amount: str, expected: str) -> None:
        assert Money(Decimal(amount)).canonical() == expected

    def test_negative_zero_is_canonicalised(self) -> None:
        assert Money(Decimal("-0")).canonical() == "0.00"

    def test_repr_is_readable(self) -> None:
        assert repr(Money.of(1)) == "Money('1.00 THB')"
