"""Isolated DMN-aligned discovery decisions: eligibility, intent, period, capacity."""

from datetime import date

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.capacity import calculate_opportunity_capacity
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.effective_period import EffectivePeriodOutcome, check_effective_period
from tax_gps.discovery.eligibility import (
    EligibilityDecision,
    EligibilityFact,
    assess_eligibility,
)
from tax_gps.discovery.facts import collect_facts
from tax_gps.discovery.intent import IntentOutcome, check_intrinsic_intent
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.models import OpportunityDefinition
from tax_gps.profile.models import (
    ArtworkIntent,
    IncomeProfile,
    OpportunityFacts,
    SharedLimitUsage,
    SolarRooftopIntent,
    UserProfile,
)
from tests.support.catalog import production_catalog


def context(planning_date: date) -> DiscoveryContext:
    return DiscoveryContext(TaxYear(2026), planning_date)


def profile(facts: OpportunityFacts, salary: int = 800000) -> UserProfile:
    return UserProfile(
        profile_id="p",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(salary)),
        opportunity_facts=facts,
    )


def definition(opportunity_id: str) -> OpportunityDefinition:
    return production_catalog().catalog.definition(opportunity_id)


def test_eligibility_is_ineligible_when_any_declared_fact_is_false() -> None:
    assessment = assess_eligibility(
        (
            EligibilityFact("a", True),
            EligibilityFact("b", False),
            EligibilityFact("c", None),
            EligibilityFact("d", False),
        )
    )
    assert assessment.decision is EligibilityDecision.INELIGIBLE
    assert assessment.failed_fact_ids == ("b", "d")
    assert assessment.missing_fact_ids == ("c",)


def test_eligibility_requires_input_when_a_fact_is_unknown() -> None:
    assessment = assess_eligibility((EligibilityFact("a", True), EligibilityFact("b", None)))
    assert assessment.decision is EligibilityDecision.INSUFFICIENT_FACTS
    assert assessment.missing_fact_ids == ("b",)
    assert assessment.failed_fact_ids == ()


def test_eligibility_is_eligible_only_when_every_fact_is_explicitly_true() -> None:
    assessment = assess_eligibility((EligibilityFact("a", True),))
    assert assessment.decision is EligibilityDecision.ELIGIBLE
    assert assess_eligibility(()).decision is EligibilityDecision.ELIGIBLE


def test_intrinsic_intent_distinguishes_unknown_from_no() -> None:
    artwork = definition(opportunity_ids.ARTWORK)
    thai_esg = definition(opportunity_ids.THAI_ESG)
    assert (
        check_intrinsic_intent(thai_esg, EligibilityFact("i", None)) is IntentOutcome.NOT_REQUIRED
    )
    assert check_intrinsic_intent(artwork, EligibilityFact("i", None)) is IntentOutcome.UNKNOWN
    assert (
        check_intrinsic_intent(artwork, EligibilityFact("i", False)) is IntentOutcome.NOT_INTENDED
    )
    assert check_intrinsic_intent(artwork, EligibilityFact("i", True)) is IntentOutcome.INTENDED


def test_effective_period_check_uses_the_explicit_planning_date() -> None:
    solar = definition(opportunity_ids.SOLAR_ROOFTOP)
    assert check_effective_period(solar, context(date(2026, 3, 2))) is (
        EffectivePeriodOutcome.OUTSIDE_PERIOD
    )
    assert check_effective_period(solar, context(date(2026, 3, 3))) is (
        EffectivePeriodOutcome.WITHIN_PERIOD
    )
    assert check_effective_period(solar, context(date(2028, 12, 31))) is (
        EffectivePeriodOutcome.WITHIN_PERIOD
    )
    assert check_effective_period(solar, context(date(2029, 1, 1))) is (
        EffectivePeriodOutcome.OUTSIDE_PERIOD
    )


def test_open_ended_effective_period_never_expires() -> None:
    personal = definition(opportunity_ids.PERSONAL_ALLOWANCE)
    assert personal.effective_to is None
    assert check_effective_period(personal, context(date(2099, 1, 1))) is (
        EffectivePeriodOutcome.WITHIN_PERIOD
    )


def test_thai_esg_capacity_is_the_lesser_of_the_income_test_and_the_statutory_cap() -> None:
    catalog = production_catalog().catalog
    thai_esg = definition(opportunity_ids.THAI_ESG)
    low = calculate_opportunity_capacity(
        thai_esg, catalog, assessable_income=Money.of(800000), shared_amount_used=Money.zero()
    )
    high = calculate_opportunity_capacity(
        thai_esg, catalog, assessable_income=Money.of(2000000), shared_amount_used=Money.zero()
    )
    assert low.remaining_capacity == Money.of(240000)
    assert high.remaining_capacity == Money.of(300000)
    assert low.shared_limit == Money.of(240000)
    assert low.shared_limit_group == opportunity_ids.THAI_ESG_2026_POOL


def test_shared_pool_usage_reduces_capacity_and_never_falls_below_zero() -> None:
    catalog = production_catalog().catalog
    thai_esg = definition(opportunity_ids.THAI_ESG)
    partial = calculate_opportunity_capacity(
        thai_esg, catalog, assessable_income=Money.of(2000000), shared_amount_used=Money.of(120000)
    )
    exhausted = calculate_opportunity_capacity(
        thai_esg, catalog, assessable_income=Money.of(2000000), shared_amount_used=Money.of(400000)
    )
    assert partial.remaining_capacity == Money.of(180000)
    assert exhausted.remaining_capacity == Money.zero()


def test_capacity_without_a_shared_group_uses_the_standalone_limit_only() -> None:
    catalog = production_catalog().catalog
    capacity = calculate_opportunity_capacity(
        definition(opportunity_ids.ARTWORK),
        catalog,
        assessable_income=Money.of(2000000),
        shared_amount_used=Money.zero(),
    )
    assert capacity.remaining_capacity == Money.of(100000)
    assert capacity.shared_limit_group is None
    assert capacity.shared_limit is None
    assert capacity.to_dict()["shared_limit"] is None


@pytest.mark.negative
def test_capacity_requires_a_governed_standalone_limit() -> None:
    catalog = production_catalog().catalog
    with pytest.raises(ValueError, match="standalone limit"):
        calculate_opportunity_capacity(
            definition(opportunity_ids.PERSONAL_ALLOWANCE),
            catalog,
            assessable_income=Money.of(1),
            shared_amount_used=Money.zero(),
        )


def test_artwork_facts_are_collected_as_explicit_optional_booleans() -> None:
    facts = collect_facts(
        definition(opportunity_ids.ARTWORK),
        profile(OpportunityFacts(artwork=ArtworkIntent(intends_to_purchase=True))),
    )
    assert facts.intent.value is True
    assert [fact.value for fact in facts.conditions] == [None, None, None]
    assert all(fact.fact_id.startswith("artwork.") for fact in facts.conditions)


def test_solar_facts_cover_every_material_royal_decree_condition() -> None:
    facts = collect_facts(
        definition(opportunity_ids.SOLAR_ROOFTOP),
        profile(OpportunityFacts(solar_rooftop=SolarRooftopIntent(is_natural_person=True))),
    )
    assert facts.intent.value is None
    assert len(facts.conditions) == 9
    assert facts.conditions[0].value is True


def test_thai_esg_declares_no_intrinsic_intent_or_condition_facts() -> None:
    facts = collect_facts(
        definition(opportunity_ids.THAI_ESG),
        profile(
            OpportunityFacts(
                shared_limit_usage=(
                    SharedLimitUsage(opportunity_ids.THAI_ESG_2026_POOL, Money.of(1)),
                )
            )
        ),
    )
    assert facts.conditions == ()
    assert facts.intent.value is None


def test_unregistered_opportunity_yields_no_asserted_facts() -> None:
    facts = collect_facts(
        definition(opportunity_ids.PERSONAL_ALLOWANCE), profile(OpportunityFacts())
    )
    assert facts.conditions == ()
    assert facts.intent.fact_id.endswith(".intrinsic_intent")


def test_discovery_context_carries_an_explicit_planning_date_and_never_reads_a_clock() -> None:
    assert DiscoveryContext(TaxYear(2026), date(2026, 6, 1)).planning_date == date(2026, 6, 1)
    assert DiscoveryContext(TaxYear(2026), date(2029, 6, 1)).to_dict() == {
        "tax_year": 2026,
        "planning_date": "2029-06-01",
    }
