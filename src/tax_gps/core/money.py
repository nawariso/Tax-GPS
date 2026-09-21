"""Money value object with exact decimal semantics (THB only).

* Binary floats are rejected.
* Inputs created with :meth:`Money.of` must be whole satang (at most 2 decimal places).
* Derived amounts (e.g. ``Money * Percentage``) stay exact; no implicit rounding occurs.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from tax_gps.core.decimal_context import EXACT, canonical_decimal, exact, parse_decimal
from tax_gps.core.errors import InvalidMoneyError
from tax_gps.core.percentage import Percentage

CURRENCY = "THB"
_SATANG = Decimal("0.01")
_CANONICAL_MIN_PLACES = 2


@dataclass(frozen=True, slots=True, eq=False)
class Money:
    """An exact THB amount."""

    amount: Decimal
    currency: str = CURRENCY

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite():
            raise InvalidMoneyError("money amount must be a finite Decimal")
        if self.currency != CURRENCY:
            raise InvalidMoneyError(f"only {CURRENCY} is supported")

    @classmethod
    def of(cls, value: str | int | Decimal) -> Money:
        """Create money from an external input; precision must be whole satang."""
        money = cls(parse_decimal(value, InvalidMoneyError, "monetary amount"))
        if not money.is_whole_satang():
            raise InvalidMoneyError("input money must not be finer than 1 satang (0.01 THB)")
        return money

    @classmethod
    def zero(cls) -> Money:
        return cls(Decimal(0))

    @staticmethod
    def min(first: Money, second: Money) -> Money:
        return first if first <= second else second

    @staticmethod
    def max(first: Money, second: Money) -> Money:
        return first if first >= second else second

    @classmethod
    def sum(cls, values: Iterable[Money]) -> Money:
        total = cls.zero()
        for value in values:
            total = total + value
        return total

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(exact(EXACT.add, self.amount, other.amount, InvalidMoneyError))

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(exact(EXACT.subtract, self.amount, other.amount, InvalidMoneyError))

    def __mul__(self, other: Percentage) -> Money:
        if not isinstance(other, Percentage):
            return NotImplemented
        return Money(exact(EXACT.multiply, self.amount, other.ratio, InvalidMoneyError))

    def times(self, factor: int) -> Money:
        """Scale by a non-negative whole number (e.g. a policy month count)."""
        if isinstance(factor, bool) or not isinstance(factor, int) or factor < 0:
            raise InvalidMoneyError("money scale factor must be a non-negative int")
        return Money(exact(EXACT.multiply, self.amount, Decimal(factor), InvalidMoneyError))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount

    def __hash__(self) -> int:
        return hash(self.amount)

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount >= other.amount

    def is_zero(self) -> bool:
        return self.amount.is_zero()

    def is_negative(self) -> bool:
        return self.amount < 0

    def is_positive(self) -> bool:
        return self.amount > 0

    def is_whole_satang(self) -> bool:
        remainder = exact(EXACT.remainder, self.amount, _SATANG, InvalidMoneyError)
        return remainder.is_zero()

    def floor_at_zero(self) -> Money:
        return self if not self.is_negative() else Money.zero()

    def canonical(self) -> str:
        """Plain decimal string with at least two fractional digits, e.g. ``820000.00``."""
        return canonical_decimal(self.amount, min_places=_CANONICAL_MIN_PLACES)

    def __repr__(self) -> str:
        return f"Money('{self.canonical()} {self.currency}')"
