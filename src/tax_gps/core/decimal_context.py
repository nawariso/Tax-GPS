"""Explicit, isolated decimal arithmetic and strict decimal parsing.

Tax arithmetic never uses the ambient (thread-global, mutable) ``decimal`` context. All
operations go through ``EXACT``, which traps ``Inexact`` and ``Rounded`` so any result that
cannot be represented exactly raises instead of being silently rounded.
"""

import re
from collections.abc import Callable
from decimal import (
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
    Rounded,
    Underflow,
)

from tax_gps.core.errors import InvalidValueError

_PRECISION = 50
_DECIMAL_PATTERN = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?")

EXACT = Context(
    prec=_PRECISION,
    traps=[InvalidOperation, DivisionByZero, Overflow, Underflow, Inexact, Rounded],
)


def parse_decimal(value: object, error: type[InvalidValueError], kind: str) -> Decimal:
    """Convert an external value to a finite Decimal; floats, bools and loose strings fail."""
    if isinstance(value, bool):
        raise error(f"bool is not a valid {kind}")
    if isinstance(value, float):
        raise error(f"binary float is not allowed for {kind}")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise error(f"{kind} must be finite")
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        if _DECIMAL_PATTERN.fullmatch(value) is None:
            raise error(f"malformed {kind}: {value!r}")
        return Decimal(value)
    raise error(f"unsupported {kind} type: {type(value).__name__}")


def exact(
    operation: Callable[[Decimal, Decimal], Decimal],
    left: Decimal,
    right: Decimal,
    error: type[InvalidValueError],
) -> Decimal:
    """Apply an ``EXACT`` context operation, converting decimal signals to ``error``."""
    try:
        return operation(left, right)
    except DecimalException as exc:
        raise error("decimal arithmetic result is not exact") from exc


def canonical_decimal(value: Decimal, *, min_places: int = 0) -> str:
    """Render a finite decimal in plain notation (no exponent) with trailing zeros removed.

    At least ``min_places`` fractional digits are kept. Negative zero renders as zero.
    """
    normalized = value.normalize(EXACT)
    if normalized.is_zero():
        normalized = Decimal(0)
    exponent = normalized.as_tuple().exponent
    if not isinstance(exponent, int):  # pragma: no cover - guarded by finite-only constructors
        raise InvalidValueError("decimal must be finite")
    places = max(min_places, -exponent)
    return f"{normalized:.{places}f}"
