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


def _optional_bool(value: bool | None, field: str) -> None:
    if value is not None and not isinstance(value, bool):
        raise InvalidValueError(f"{field} must be a boolean or null")


@dataclass(frozen=True, slots=True)
class Parent:
    relationship: str
    eligible: bool | None

    def __post_init__(self) -> None:
        if not self.relationship.strip():
            raise InvalidValueError("parent relationship must be named")
        _optional_bool(self.eligible, "parent eligible")


@dataclass(frozen=True, slots=True, init=False)
class Child:
    child_id: str
    order: int
    legally_eligible: bool
    birth_year: int

    def __init__(
        self,
        child_id: str | int | None = None,
        legally_eligible: bool | None = None,
        birth_year: int | None = None,
        *,
        order: int | None = None,
    ) -> None:
        if order is None:
            if isinstance(child_id, bool) or not isinstance(child_id, int):
                raise InvalidValueError("child order must be a positive integer")
            order = child_id
            stable_id = f"legal-order:{order}"
        else:
            if child_id is not None and not isinstance(child_id, str):
                raise InvalidValueError("child id must be a string")
            stable_id = child_id if child_id is not None else f"legal-order:{order}"
        if legally_eligible is None or birth_year is None:
            raise InvalidValueError("child eligibility and birth year are required")
        object.__setattr__(self, "child_id", stable_id)
        object.__setattr__(self, "order", order)
        object.__setattr__(self, "legally_eligible", legally_eligible)
        object.__setattr__(self, "birth_year", birth_year)
        self.__post_init__()

    def __post_init__(self) -> None:
        if not self.child_id.strip():
            raise InvalidValueError("child id must be named")
        if isinstance(self.order, bool) or self.order < 1:
            raise InvalidValueError("child order must be a positive integer")
        if isinstance(self.birth_year, bool) or not 1900 <= self.birth_year <= 2100:
            raise InvalidValueError("child birth year must be Gregorian")
        if not isinstance(self.legally_eligible, bool):
            raise InvalidValueError("child legally eligible must be a boolean")


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
        object.__setattr__(self, "unsupported", tuple(self.unsupported))
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
        object.__setattr__(self, "parents", tuple(self.parents))
        object.__setattr__(self, "children", tuple(self.children))
        object.__setattr__(self, "retirement_contributions", tuple(self.retirement_contributions))
        if not isinstance(self.personal_eligible, bool):
            raise InvalidValueError("personal eligible must be a boolean")
        if not isinstance(self.mortgage_eligible, bool):
            raise InvalidValueError("mortgage eligible must be a boolean")
        _non_negative(self.social_security_paid, "social security paid")
        _non_negative(self.mortgage_interest_paid, "mortgage interest paid")
        relationships = [parent.relationship.strip().casefold() for parent in self.parents]
        if len(set(relationships)) != len(relationships):
            raise InvalidValueError("duplicate parent relationship or identity")
        child_ids = [child.child_id.strip().casefold() for child in self.children]
        if len(set(child_ids)) != len(child_ids):
            raise InvalidValueError("duplicate child id")
        eligible_orders = [child.order for child in self.children if child.legally_eligible]
        if len(set(eligible_orders)) != len(eligible_orders):
            raise InvalidValueError("duplicate legal child order")


@dataclass(frozen=True, slots=True)
class SharedLimitUsage:
    group_id: str
    amount_used: Money

    def __post_init__(self) -> None:
        if not self.group_id.strip():
            raise InvalidValueError("shared limit group must be named")
        _non_negative(self.amount_used, "shared limit amount used")


@dataclass(frozen=True, slots=True)
class ArtworkIntent:
    intends_to_purchase: bool | None = None
    artwork_is_qualifying: bool | None = None
    seller_is_qualifying: bool | None = None
    has_required_document: bool | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "intends_to_purchase",
            "artwork_is_qualifying",
            "seller_is_qualifying",
            "has_required_document",
        ):
            _optional_bool(getattr(self, field_name), f"artwork {field_name}")


@dataclass(frozen=True, slots=True)
class SolarRooftopIntent:
    intends_to_install: bool | None = None
    is_natural_person: bool | None = None
    single_system_single_use: bool | None = None
    building_is_occupiable: bool | None = None
    on_grid_connected_to_mea_or_pea: bool | None = None
    paid_to_vat_registrant: bool | None = None
    has_electronic_tax_invoice: bool | None = None
    grid_connection_completed_in_tax_year: bool | None = None
    no_duplicate_tax_benefit: bool | None = None
    meets_director_general_conditions: bool | None = None

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _optional_bool(getattr(self, field_name), f"solar rooftop {field_name}")


@dataclass(frozen=True, slots=True)
class OpportunityFacts:
    artwork: ArtworkIntent = ArtworkIntent()
    solar_rooftop: SolarRooftopIntent = SolarRooftopIntent()
    shared_limit_usage: tuple[SharedLimitUsage, ...] | None = None

    def __post_init__(self) -> None:
        if self.shared_limit_usage is None:
            return
        object.__setattr__(self, "shared_limit_usage", tuple(self.shared_limit_usage))
        groups = [usage.group_id for usage in self.shared_limit_usage]
        if len(set(groups)) != len(groups):
            raise InvalidValueError("duplicate shared limit group")

    def shared_limit_amount_used(self, group_id: str | None) -> Money | None:
        if group_id is None:
            return Money.zero()
        if self.shared_limit_usage is None:
            return None
        return next(
            (usage.amount_used for usage in self.shared_limit_usage if usage.group_id == group_id),
            Money.zero(),
        )


@dataclass(frozen=True, slots=True)
class UserProfile:
    profile_id: str
    version: str
    tax_year: TaxYear
    income: IncomeProfile
    benefits: ExistingTaxBenefits = ExistingTaxBenefits()
    opportunity_facts: OpportunityFacts = OpportunityFacts()

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
                        "child_id": child.child_id,
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
            "opportunity_facts": {
                "artwork": {
                    "intends_to_purchase": self.opportunity_facts.artwork.intends_to_purchase,
                    "artwork_is_qualifying": self.opportunity_facts.artwork.artwork_is_qualifying,
                    "seller_is_qualifying": self.opportunity_facts.artwork.seller_is_qualifying,
                    "has_required_document": self.opportunity_facts.artwork.has_required_document,
                },
                "solar_rooftop": {
                    "intends_to_install": self.opportunity_facts.solar_rooftop.intends_to_install,
                    "is_natural_person": self.opportunity_facts.solar_rooftop.is_natural_person,
                    "single_system_single_use": (
                        self.opportunity_facts.solar_rooftop.single_system_single_use
                    ),
                    "building_is_occupiable": (
                        self.opportunity_facts.solar_rooftop.building_is_occupiable
                    ),
                    "on_grid_connected_to_mea_or_pea": (
                        self.opportunity_facts.solar_rooftop.on_grid_connected_to_mea_or_pea
                    ),
                    "paid_to_vat_registrant": (
                        self.opportunity_facts.solar_rooftop.paid_to_vat_registrant
                    ),
                    "has_electronic_tax_invoice": (
                        self.opportunity_facts.solar_rooftop.has_electronic_tax_invoice
                    ),
                    "grid_connection_completed_in_tax_year": (
                        self.opportunity_facts.solar_rooftop.grid_connection_completed_in_tax_year
                    ),
                    "no_duplicate_tax_benefit": (
                        self.opportunity_facts.solar_rooftop.no_duplicate_tax_benefit
                    ),
                    "meets_director_general_conditions": (
                        self.opportunity_facts.solar_rooftop.meets_director_general_conditions
                    ),
                },
                "shared_limit_usage": (
                    [
                        {
                            "group_id": usage.group_id,
                            "amount_used": usage.amount_used.canonical(),
                        }
                        for usage in self.opportunity_facts.shared_limit_usage
                    ]
                    if self.opportunity_facts.shared_limit_usage is not None
                    else None
                ),
            },
        }

    def profile_hash(self) -> str:
        return sha256_hex(canonical_json(self.to_dict()))
