"""Financial Profile: caller-supplied financial facts (TGPS-P1-003 §8-15).

No inference is performed anywhere in this module. Every field defaults to ``None`` /
empty and stays that way until a caller supplies a value. ``Unknown != zero != false``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from tax_gps.core.decimal_context import EXACT, exact, parse_decimal
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money


class DebtCategory(StrEnum):
    CREDIT_CARD = "CREDIT_CARD"
    PERSONAL_LOAN = "PERSONAL_LOAN"
    CASH_CARD = "CASH_CARD"
    AUTO_LOAN = "AUTO_LOAN"
    MORTGAGE = "MORTGAGE"
    STUDENT_LOAN = "STUDENT_LOAN"
    OTHER = "OTHER"


def _annual_percentage_rate(value: str | int | Decimal) -> Decimal:
    """APR as an exact Decimal ratio (0.18 = 18.00% p.a.); no invented upper bound (§12)."""
    rate = parse_decimal(value, InvalidValueError, "annual percentage rate")
    if rate < 0:
        raise InvalidValueError("annual percentage rate cannot be negative")
    return rate


def canonical_apr(rate: Decimal) -> str:
    normalized = rate.normalize(EXACT)
    if normalized.is_zero():
        normalized = Decimal(0)
    exponent = normalized.as_tuple().exponent
    if not isinstance(exponent, int):  # pragma: no cover - guarded by finite-only construction
        raise InvalidValueError("annual percentage rate must be finite")
    places = max(4, -exponent)
    return f"{normalized:.{places}f}"


@dataclass(frozen=True, slots=True)
class Debt:
    debt_id: str
    category: DebtCategory
    outstanding_balance: Money
    annual_percentage_rate: Decimal
    minimum_monthly_payment: Money
    secured: bool

    def __post_init__(self) -> None:
        if not self.debt_id.strip():
            raise InvalidValueError("debt id must be named")
        if self.outstanding_balance.is_negative():
            raise InvalidValueError("debt outstanding balance cannot be negative")
        if self.minimum_monthly_payment.is_negative():
            raise InvalidValueError("debt minimum monthly payment cannot be negative")
        object.__setattr__(
            self, "annual_percentage_rate", _annual_percentage_rate(self.annual_percentage_rate)
        )
        if not isinstance(self.secured, bool):
            raise InvalidValueError("debt secured must be a boolean")

    def to_dict(self) -> dict[str, object]:
        return {
            "debt_id": self.debt_id,
            "category": self.category.value,
            "outstanding_balance": self.outstanding_balance.canonical(),
            "annual_percentage_rate": canonical_apr(self.annual_percentage_rate),
            "minimum_monthly_payment": self.minimum_monthly_payment.canonical(),
            "secured": self.secured,
        }


@dataclass(frozen=True, slots=True)
class CommittedCashNeed:
    need_id: str
    amount: Money
    due_date: date
    mandatory: bool
    description: str

    def __post_init__(self) -> None:
        if not self.need_id.strip():
            raise InvalidValueError("committed cash need id must be named")
        if self.amount.is_negative():
            raise InvalidValueError("committed cash need amount cannot be negative")
        if not isinstance(self.mandatory, bool):
            raise InvalidValueError("committed cash need mandatory must be a boolean")

    def to_dict(self) -> dict[str, object]:
        return {
            "need_id": self.need_id,
            "amount": self.amount.canonical(),
            "due_date": self.due_date.isoformat(),
            "mandatory": self.mandatory,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class ProtectionProfile:
    required_life_coverage: Money | None = None
    existing_life_coverage: Money | None = None

    def __post_init__(self) -> None:
        if self.required_life_coverage is not None and self.required_life_coverage.is_negative():
            raise InvalidValueError("required life coverage cannot be negative")
        if self.existing_life_coverage is not None and self.existing_life_coverage.is_negative():
            raise InvalidValueError("existing life coverage cannot be negative")

    @property
    def protection_gap(self) -> Money | None:
        """``None`` (unknown) unless both coverage figures are known (§14)."""
        if self.required_life_coverage is None or self.existing_life_coverage is None:
            return None
        gap = exact(
            EXACT.subtract,
            self.required_life_coverage.amount,
            self.existing_life_coverage.amount,
            InvalidValueError,
        )
        return Money(gap).floor_at_zero()

    def to_dict(self) -> dict[str, object]:
        return {
            "required_life_coverage": _money(self.required_life_coverage),
            "existing_life_coverage": _money(self.existing_life_coverage),
        }


def _money(value: Money | None) -> str | None:
    return value.canonical() if value is not None else None


@dataclass(frozen=True, slots=True)
class FinancialProfile:
    liquid_assets: Money | None = None
    monthly_essential_expenses: Money | None = None
    debts: tuple[Debt, ...] = ()
    committed_cash_needs: tuple[CommittedCashNeed, ...] = ()
    protection: ProtectionProfile = ProtectionProfile()

    def __post_init__(self) -> None:
        object.__setattr__(self, "debts", tuple(self.debts))
        object.__setattr__(self, "committed_cash_needs", tuple(self.committed_cash_needs))
        if self.liquid_assets is not None and self.liquid_assets.is_negative():
            raise InvalidValueError("liquid assets cannot be negative")
        if (
            self.monthly_essential_expenses is not None
            and self.monthly_essential_expenses.is_negative()
        ):
            raise InvalidValueError("monthly essential expenses cannot be negative")
        debt_ids = [item.debt_id.strip().casefold() for item in self.debts]
        if len(set(debt_ids)) != len(debt_ids):
            raise InvalidValueError("duplicate debt id")
        need_ids = [item.need_id.strip().casefold() for item in self.committed_cash_needs]
        if len(set(need_ids)) != len(need_ids):
            raise InvalidValueError("duplicate committed cash need id")

    def to_dict(self) -> dict[str, object]:
        return {
            "liquid_assets": _money(self.liquid_assets),
            "monthly_essential_expenses": _money(self.monthly_essential_expenses),
            "debts": [item.to_dict() for item in self.debts],
            "committed_cash_needs": [item.to_dict() for item in self.committed_cash_needs],
            "protection": self.protection.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FinancialPlanningContext:
    """Explicit planning date and the cash under consideration for new allocation (§22)."""

    planning_date: date
    available_budget: Money

    def __post_init__(self) -> None:
        if self.available_budget.is_negative():
            raise InvalidValueError("available budget cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "planning_date": self.planning_date.isoformat(),
            "available_budget": self.available_budget.canonical(),
        }


__all__ = [
    "CommittedCashNeed",
    "Debt",
    "DebtCategory",
    "FinancialPlanningContext",
    "FinancialProfile",
    "ProtectionProfile",
    "canonical_apr",
]
