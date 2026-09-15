"""Immutable, explicit taxpayer input models for the supported phase-1 boundary."""

from __future__ import annotations

from dataclasses import dataclass, field

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear


def _non_negative(amount: Money, field: str) -> None:
    if amount.is_negative():
        raise InvalidValueError(f"{field} cannot be negative")


@dataclass(frozen=True, slots=True)
class Parent:
    relationship: str
    eligible: bool


@dataclass(frozen=True, slots=True)
class Child:
    order: int
    legally_eligible: bool
    birth_year: int

    def __post_init__(self) -> None:
        if isinstance(self.order, bool) or self.order < 1:
            raise InvalidValueError("child order must be a positive integer")
        if isinstance(self.birth_year, bool) or not 1900 <= self.birth_year <= 2100:
            raise InvalidValueError("child birth year must be Gregorian")


@dataclass(frozen=True, slots=True)
class UnsupportedIncome:
    category: str
    amount: Money

    def __post_init__(self) -> None:
        _non_negative(self.amount, "unsupported income")


@dataclass(frozen=True, slots=True)
class RetirementContribution:
    category: str
    amount_used: Money

    def __post_init__(self) -> None:
        _non_negative(self.amount_used, "retirement contribution")


@dataclass(frozen=True, slots=True)
class IncomeProfile:
    section_40_1: Money
    unsupported: tuple[UnsupportedIncome, ...] = ()

    def __post_init__(self) -> None:
        _non_negative(self.section_40_1, "section 40(1) income")


@dataclass(frozen=True, slots=True)
class ExistingTaxBenefits:
    personal_eligible: bool = True
    social_security_paid: Money = field(default_factory=Money.zero)
    parents: tuple[Parent, ...] = ()
    children: tuple[Child, ...] = ()
    mortgage_interest_paid: Money = field(default_factory=Money.zero)
    mortgage_eligible: bool = False
    retirement_contributions: tuple[RetirementContribution, ...] = ()

    def __post_init__(self) -> None:
        _non_negative(self.social_security_paid, "social security paid")
        _non_negative(self.mortgage_interest_paid, "mortgage interest paid")


@dataclass(frozen=True, slots=True)
class UserProfile:
    profile_id: str
    version: str
    tax_year: TaxYear
    income: IncomeProfile
    benefits: ExistingTaxBenefits = ExistingTaxBenefits()

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "tax_year": self.tax_year.gregorian,
            "income": {
                "section_40_1": self.income.section_40_1.canonical(),
                "unsupported": [
                    {"category": item.category, "amount": item.amount.canonical()}
                    for item in self.income.unsupported
                ],
            },
            "benefits": {
                "personal_eligible": self.benefits.personal_eligible,
                "social_security_paid": self.benefits.social_security_paid.canonical(),
                "parents": [
                    {"relationship": parent.relationship, "eligible": parent.eligible}
                    for parent in self.benefits.parents
                ],
                "children": [
                    {
                        "order": child.order,
                        "legally_eligible": child.legally_eligible,
                        "birth_year": child.birth_year,
                    }
                    for child in self.benefits.children
                ],
                "mortgage_interest_paid": self.benefits.mortgage_interest_paid.canonical(),
                "mortgage_eligible": self.benefits.mortgage_eligible,
                "retirement_contributions": [
                    {"category": item.category, "amount_used": item.amount_used.canonical()}
                    for item in self.benefits.retirement_contributions
                ],
            },
        }

    def profile_hash(self) -> str:
        return sha256_hex(canonical_json(self.to_dict()))
