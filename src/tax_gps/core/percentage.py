"""Percentage value object, stored as an exact decimal ratio in [0, 1]."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tax_gps.core.decimal_context import canonical_decimal, parse_decimal
from tax_gps.core.errors import InvalidPercentageError


@dataclass(frozen=True, slots=True, eq=False)
class Percentage:
    """A ratio such as ``0.05`` meaning 5%."""

    ratio: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.ratio, Decimal) or not self.ratio.is_finite():
            raise InvalidPercentageError("percentage ratio must be a finite Decimal")
        if not Decimal(0) <= self.ratio <= Decimal(1):
            raise InvalidPercentageError("percentage ratio must be between 0 and 1")

    @classmethod
    def of(cls, value: str | int | Decimal) -> Percentage:
        return cls(parse_decimal(value, InvalidPercentageError, "percentage"))

    @classmethod
    def zero(cls) -> Percentage:
        return cls(Decimal(0))

    def canonical(self) -> str:
        return canonical_decimal(self.ratio)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.ratio == other.ratio

    def __hash__(self) -> int:
        return hash(self.ratio)

    def __lt__(self, other: Percentage) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.ratio < other.ratio

    def __repr__(self) -> str:
        return f"Percentage({self.canonical()!r})"
