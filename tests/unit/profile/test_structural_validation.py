"""Structural taxpayer-profile validation and explicit opportunity fact representation."""

import pytest

from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.profile.models import (
    ArtworkIntent,
    Child,
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    SharedLimitUsage,
    SolarRooftopIntent,
    UserProfile,
)


def child(child_id: str, order: int, *, legally_eligible: bool = True) -> Child:
    return Child(child_id, order=order, legally_eligible=legally_eligible, birth_year=2018)


@pytest.mark.mandatory
@pytest.mark.negative
def test_disc_14_duplicate_parent_identity_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="duplicate parent"):
        ExistingTaxBenefits(parents=(Parent("father", True), Parent("father", True)))


def test_distinct_parent_roles_are_accepted() -> None:
    benefits = ExistingTaxBenefits(parents=(Parent("father", True), Parent("mother", True)))
    assert len(benefits.parents) == 2


@pytest.mark.negative
def test_parent_relationship_must_be_named() -> None:
    with pytest.raises(InvalidValueError, match="parent relationship"):
        Parent("  ", True)


def test_parent_eligibility_may_be_unknown() -> None:
    assert Parent("father", None).eligible is None


@pytest.mark.mandatory
@pytest.mark.negative
def test_disc_15_duplicate_child_identity_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="duplicate child id"):
        ExistingTaxBenefits(children=(child("c1", 1), child("c1", 2)))


@pytest.mark.mandatory
@pytest.mark.negative
def test_disc_15_duplicate_legal_child_order_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="duplicate legal child order"):
        ExistingTaxBenefits(children=(child("c1", 1), child("c2", 1)))


def test_order_may_repeat_for_children_that_are_not_legally_eligible() -> None:
    benefits = ExistingTaxBenefits(
        children=(child("c1", 1), child("c2", 1, legally_eligible=False))
    )
    assert len(benefits.children) == 2


@pytest.mark.negative
def test_child_id_must_be_named() -> None:
    with pytest.raises(InvalidValueError, match="child id"):
        Child("", order=1, legally_eligible=True, birth_year=2018)


@pytest.mark.negative
def test_shared_limit_usage_rejects_negative_amounts_and_duplicate_groups() -> None:
    with pytest.raises(InvalidValueError, match="negative"):
        SharedLimitUsage("THAI_ESG_2026_POOL", Money.of(-1))
    with pytest.raises(InvalidValueError, match="group"):
        SharedLimitUsage("   ", Money.zero())
    with pytest.raises(InvalidValueError, match="duplicate shared limit group"):
        OpportunityFacts(
            shared_limit_usage=(
                SharedLimitUsage("THAI_ESG_2026_POOL", Money.of(1)),
                SharedLimitUsage("THAI_ESG_2026_POOL", Money.of(2)),
            )
        )


def test_shared_limit_amount_used_defaults_to_zero_for_unknown_group() -> None:
    facts = OpportunityFacts(
        shared_limit_usage=(SharedLimitUsage("THAI_ESG_2026_POOL", Money.of(100000)),)
    )
    assert facts.shared_limit_amount_used("THAI_ESG_2026_POOL") == Money.of(100000)
    assert facts.shared_limit_amount_used("OTHER") == Money.zero()
    assert facts.shared_limit_amount_used(None) == Money.zero()


def test_intent_and_material_facts_default_to_unknown() -> None:
    facts = OpportunityFacts()
    assert facts.artwork.intends_to_purchase is None
    assert facts.artwork.artwork_is_qualifying is None
    assert facts.solar_rooftop.intends_to_install is None
    assert facts.solar_rooftop.is_natural_person is None


def test_profile_dict_and_hash_cover_opportunity_facts() -> None:
    base = UserProfile(
        profile_id="p",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(1000)),
    )
    with_facts = UserProfile(
        profile_id="p",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(1000)),
        benefits=ExistingTaxBenefits(parents=(Parent("father", None),), children=(child("c1", 1),)),
        opportunity_facts=OpportunityFacts(
            artwork=ArtworkIntent(intends_to_purchase=True),
            solar_rooftop=SolarRooftopIntent(intends_to_install=False),
            shared_limit_usage=(SharedLimitUsage("THAI_ESG_2026_POOL", Money.of(50000)),),
        ),
    )
    data = with_facts.to_dict()
    assert "opportunity_facts" in data
    assert base.profile_hash() != with_facts.profile_hash()
    benefits = data["benefits"]
    assert isinstance(benefits, dict)
    assert benefits["parents"] == [{"relationship": "father", "eligible": None}]
    assert benefits["children"] == [
        {"child_id": "c1", "order": 1, "legally_eligible": True, "birth_year": 2018}
    ]
