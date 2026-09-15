"""Unit tests for TaxYear (TGPS-P1-001 §3.1: Gregorian canonical, Buddhist display only)."""

import pytest

from tax_gps.core.errors import InvalidTaxYearError
from tax_gps.core.tax_year import TaxYear


def test_canonical_year_is_gregorian() -> None:
    assert TaxYear(2026).gregorian == 2026


def test_buddhist_year_is_display_metadata() -> None:
    assert TaxYear(2026).buddhist == 2569


def test_from_buddhist() -> None:
    assert TaxYear.from_buddhist(2569) == TaxYear(2026)


def test_equality_and_ordering() -> None:
    assert TaxYear(2026) == TaxYear(2026)
    assert TaxYear(2025) < TaxYear(2026)


@pytest.mark.negative
def test_buddhist_year_passed_as_gregorian_is_rejected() -> None:
    with pytest.raises(InvalidTaxYearError, match="Buddhist"):
        TaxYear(2569)


@pytest.mark.negative
@pytest.mark.parametrize("value", [0, -2026, 1940])
def test_implausible_gregorian_year_is_rejected(value: int) -> None:
    with pytest.raises(InvalidTaxYearError):
        TaxYear(value)


@pytest.mark.negative
@pytest.mark.parametrize("value", [True, "2026", 2026.0, None])
def test_non_int_is_rejected(value: object) -> None:
    with pytest.raises(InvalidTaxYearError):
        TaxYear(value)  # type: ignore[arg-type]


@pytest.mark.negative
def test_from_buddhist_rejects_gregorian_value() -> None:
    with pytest.raises(InvalidTaxYearError):
        TaxYear.from_buddhist(2026)


@pytest.mark.negative
def test_from_buddhist_rejects_non_int() -> None:
    with pytest.raises(InvalidTaxYearError):
        TaxYear.from_buddhist("2569")  # type: ignore[arg-type]


def test_is_immutable() -> None:
    year = TaxYear(2026)
    with pytest.raises(AttributeError):
        year.gregorian = 2027  # type: ignore[misc]


def test_str() -> None:
    assert str(TaxYear(2026)) == "2026"
