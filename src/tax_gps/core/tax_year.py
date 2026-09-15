"""TaxYear value object. Gregorian year is canonical; Buddhist Era is display metadata only."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.core.errors import InvalidTaxYearError

BUDDHIST_ERA_OFFSET = 543
# Data-sanity guards, not tax rules: Thailand's calendar year has started on 1 January since
# 1941; any "Gregorian" value at or above 2400 is almost certainly a Buddhist Era year
# (B.E. 2400 = 1857 CE) entered by mistake.
_MIN_GREGORIAN_YEAR = 1941
_MIN_BUDDHIST_YEAR_SUSPECTED = 2400


def _require_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidTaxYearError("tax year must be an int")
    return value


@dataclass(frozen=True, slots=True, order=True)
class TaxYear:
    gregorian: int

    def __post_init__(self) -> None:
        year = _require_int(self.gregorian)
        if year >= _MIN_BUDDHIST_YEAR_SUSPECTED:
            raise InvalidTaxYearError(
                f"{year} looks like a Buddhist Era year; canonical tax year is Gregorian"
            )
        if year < _MIN_GREGORIAN_YEAR:
            raise InvalidTaxYearError(f"{year} is not a supported Gregorian tax year")

    @classmethod
    def from_buddhist(cls, buddhist_year: int) -> TaxYear:
        year = _require_int(buddhist_year)
        if year < _MIN_BUDDHIST_YEAR_SUSPECTED:
            raise InvalidTaxYearError(f"{year} is not a Buddhist Era year")
        return cls(year - BUDDHIST_ERA_OFFSET)

    @property
    def buddhist(self) -> int:
        return self.gregorian + BUDDHIST_ERA_OFFSET

    def __str__(self) -> str:
        return str(self.gregorian)
