"""Unit tests for the Percentage value object (TGPS-P1-001 §3.1)."""

from decimal import Decimal

import pytest

from tax_gps.core.errors import InvalidPercentageError
from tax_gps.core.percentage import Percentage


def test_of_ratio_string() -> None:
    assert Percentage.of("0.05").ratio == Decimal("0.05")


def test_of_int_ratio() -> None:
    assert Percentage.of(1).ratio == Decimal(1)
    assert Percentage.of(0).ratio == Decimal(0)


def test_of_decimal() -> None:
    assert Percentage.of(Decimal("0.35")).ratio == Decimal("0.35")


def test_zero() -> None:
    assert Percentage.zero() == Percentage.of(0)


@pytest.mark.parametrize("value", ["-0.01", "1.01", "2"])
def test_out_of_range_is_rejected(value: str) -> None:
    with pytest.raises(InvalidPercentageError, match="between 0 and 1"):
        Percentage.of(value)


def test_float_is_rejected() -> None:
    with pytest.raises(InvalidPercentageError, match="float"):
        Percentage.of(0.05)  # type: ignore[arg-type]


def test_bool_is_rejected() -> None:
    with pytest.raises(InvalidPercentageError):
        Percentage.of(False)


@pytest.mark.parametrize("value", ["NaN", "x", "Infinity"])
def test_non_finite_or_malformed_is_rejected(value: str) -> None:
    with pytest.raises(InvalidPercentageError):
        Percentage.of(value)


def test_unsupported_type_is_rejected() -> None:
    with pytest.raises(InvalidPercentageError):
        Percentage.of(None)  # type: ignore[arg-type]


def test_direct_constructor_validates() -> None:
    with pytest.raises(InvalidPercentageError):
        Percentage("0.5")  # type: ignore[arg-type]


def test_equality_and_hash_ignore_representation() -> None:
    assert Percentage.of("0.20") == Percentage.of("0.2")
    assert hash(Percentage.of("0.20")) == hash(Percentage.of("0.2"))
    assert Percentage.of("0.2") != Decimal("0.2")


def test_ordering() -> None:
    assert Percentage.of("0.05") < Percentage.of("0.10")


def test_ordering_with_other_type_is_not_supported() -> None:
    with pytest.raises(TypeError):
        _ = Percentage.of("0.05") < 1  # type: ignore[operator]


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [("0.20", "0.2"), ("0", "0"), ("1", "1"), ("0.05", "0.05"), ("0.350", "0.35")],
)
def test_canonical(ratio: str, expected: str) -> None:
    assert Percentage.of(ratio).canonical() == expected


def test_repr() -> None:
    assert repr(Percentage.of("0.2")) == "Percentage('0.2')"
