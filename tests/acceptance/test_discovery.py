"""TGPS-P1-002 mandatory acceptance tests DISC-01..DISC-20 and golden personas."""

from dataclasses import fields, replace
from datetime import date

import pytest

from tax_gps.calculation.models import DeductionCapacity, TaxStatus
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import DISCOVERY_ENGINE_VERSION, discover_opportunities
from tax_gps.discovery.models import (
    DiscoveredOpportunity,
    DiscoveredRight,
    DiscoveryReasonCode,
    DiscoveryResult,
    DiscoveryStatus,
)
from tax_gps.engine import calculate_tax
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.opportunity.models import OpportunityStatus, OpportunityType
from tax_gps.profile.models import (
    ArtworkIntent,
    Child,
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    RetirementContribution,
    SharedLimitUsage,
    SolarRooftopIntent,
    UnsupportedIncome,
    UserProfile,
)
from tests.support.catalog import (
    activate_catalog_dict,
    artwork_ready_catalog,
    bundled_catalog_dict,
    catalog_definition_dict,
    mark_rule_ready,
    production_catalog,
    solar_ready_catalog,
    solar_unverified_catalog,
)
from tests.support.policy import production_pack

PLANNING_DATE = date(2026, 6, 1)

ARTWORK_FULLY_ASSERTED = ArtworkIntent(
    intends_to_purchase=True,
    artwork_is_qualifying=True,
    seller_is_qualifying=True,
    has_required_document=True,
)
SOLAR_FULLY_ASSERTED = SolarRooftopIntent(
    intends_to_install=True,
    is_natural_person=True,
    single_system_single_use=True,
    building_is_occupiable=True,
    on_grid_connected_to_mea_or_pea=True,
    paid_to_vat_registrant=True,
    has_electronic_tax_invoice=True,
    grid_connection_completed_in_tax_year=True,
    no_duplicate_tax_benefit=True,
    meets_director_general_conditions=True,
)


def profile(
    salary: int = 990500,
    *,
    sso: int = 10500,
    benefits: ExistingTaxBenefits | None = None,
    facts: OpportunityFacts | None = None,
) -> UserProfile:
    return UserProfile(
        profile_id="persona",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(salary)),
        benefits=benefits or ExistingTaxBenefits(social_security_paid=Money.of(sso)),
        opportunity_facts=(facts if facts is not None else OpportunityFacts(shared_limit_usage=())),
    )


def discover(
    user: UserProfile,
    *,
    catalog: ActivatedOpportunityCatalog | None = None,
    planning_date: date = PLANNING_DATE,
) -> DiscoveryResult:
    state = calculate_tax(user, production_pack())
    return discover_opportunities(
        user,
        state,
        production_pack(),
        catalog or production_catalog(),
        DiscoveryContext(TaxYear(2026), planning_date),
    )


def right(result: DiscoveryResult, right_id: str) -> DiscoveredRight:
    return next(item for item in result.existing_rights if item.right_id == right_id)


@pytest.mark.negative
def test_existing_right_with_an_unready_rule_is_reported_not_ready() -> None:
    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.PERSONAL_ALLOWANCE)["rule_ids"] = [
        "TH-PIT-RULE-MISSING"
    ]
    result = discover(profile(), catalog=activate_catalog_dict(catalog))
    personal = right(result, opportunity_ids.PERSONAL_ALLOWANCE)
    assert personal.status is OpportunityStatus.RULE_NOT_READY
    assert personal.reason_codes == (DiscoveryReasonCode.RULE_NOT_READY,)


@pytest.mark.negative
def test_existing_right_outside_its_effective_period_is_reported_outside_period() -> None:
    result = discover(profile(), planning_date=date(2025, 12, 31))
    personal = right(result, opportunity_ids.PERSONAL_ALLOWANCE)
    assert personal.status is OpportunityStatus.OUTSIDE_EFFECTIVE_PERIOD
    assert personal.reason_codes == (DiscoveryReasonCode.OUTSIDE_EFFECTIVE_PERIOD,)


def opportunity(result: DiscoveryResult, opportunity_id: str) -> DiscoveredOpportunity:
    return next(item for item in result.opportunities if item.opportunity_id == opportunity_id)


@pytest.mark.mandatory
def test_disc_01_existing_rights_precede_new_cash_opportunities() -> None:
    result = discover(
        profile(
            benefits=ExistingTaxBenefits(
                social_security_paid=Money.of(10500),
                parents=(Parent("father", True), Parent("mother", True)),
                mortgage_interest_paid=Money.of(125000),
                mortgage_eligible=True,
            )
        )
    )
    assert result.status is DiscoveryStatus.READY
    right_ids = [item.right_id for item in result.existing_rights]
    assert opportunity_ids.PARENT_ALLOWANCE in right_ids
    assert opportunity_ids.MORTGAGE_INTEREST in right_ids
    assert opportunity(result, opportunity_ids.THAI_ESG).status is OpportunityStatus.AVAILABLE
    keys = list(result.to_dict())
    assert keys.index("existing_rights") < keys.index("opportunities")
    assert all(
        item.opportunity_type is OpportunityType.EXISTING_RIGHT for item in result.existing_rights
    )


@pytest.mark.mandatory
def test_disc_02_two_eligible_parents_are_a_sixty_thousand_baht_existing_right() -> None:
    result = discover(
        profile(
            benefits=ExistingTaxBenefits(
                parents=(Parent("father", True), Parent("mother", True)),
            )
        )
    )
    parents = right(result, opportunity_ids.PARENT_ALLOWANCE)
    assert parents.claimed_amount == Money.of(60000)
    assert parents.status is OpportunityStatus.AVAILABLE
    assert parents.reason_codes == (DiscoveryReasonCode.EXISTING_RIGHT_AVAILABLE,)
    assert parents.requires_new_cash is False


@pytest.mark.mandatory
def test_disc_03_mortgage_interest_of_125000_is_capped_at_100000() -> None:
    result = discover(
        profile(
            benefits=ExistingTaxBenefits(
                mortgage_interest_paid=Money.of(125000), mortgage_eligible=True
            )
        )
    )
    mortgage = right(result, opportunity_ids.MORTGAGE_INTEREST)
    assert mortgage.claimed_amount == Money.of(100000)
    assert (
        mortgage.claimed_amount
        == calculate_tax(
            profile(
                benefits=ExistingTaxBenefits(
                    mortgage_interest_paid=Money.of(125000), mortgage_eligible=True
                )
            ),
            production_pack(),
        ).allowances.mortgage_interest
    )


@pytest.mark.mandatory
def test_disc_04_thai_esg_capacity_is_thirty_percent_of_800000_assessable_income() -> None:
    result = discover(profile(800000))
    thai_esg = opportunity(result, opportunity_ids.THAI_ESG)
    assert thai_esg.status is OpportunityStatus.AVAILABLE
    assert thai_esg.remaining_capacity == Money.of(240000)


@pytest.mark.mandatory
def test_disc_05_thai_esg_capacity_is_capped_at_300000_for_high_income() -> None:
    result = discover(profile(2000000))
    assert opportunity(result, opportunity_ids.THAI_ESG).remaining_capacity == Money.of(300000)


@pytest.mark.mandatory
def test_disc_06_shared_pool_usage_reduces_capacity_without_a_second_cap() -> None:
    used = OpportunityFacts(
        shared_limit_usage=(SharedLimitUsage(opportunity_ids.THAI_ESG_2026_POOL, Money.of(120000)),)
    )
    result = discover(profile(2000000, facts=used))
    thai_esg = opportunity(result, opportunity_ids.THAI_ESG)
    assert thai_esg.remaining_capacity == Money.of(180000)
    assert DiscoveryReasonCode.SHARED_LIMIT_APPLIED in thai_esg.reason_codes


@pytest.mark.mandatory
def test_disc_06_exhausted_shared_pool_reports_no_remaining_capacity() -> None:
    exhausted = OpportunityFacts(
        shared_limit_usage=(SharedLimitUsage(opportunity_ids.THAI_ESG_2026_POOL, Money.of(300000)),)
    )
    thai_esg = opportunity(discover(profile(2000000, facts=exhausted)), opportunity_ids.THAI_ESG)
    assert thai_esg.status is not OpportunityStatus.AVAILABLE
    assert thai_esg.remaining_capacity == Money.zero()
    assert thai_esg.reason_codes == (
        DiscoveryReasonCode.NO_REMAINING_CAPACITY,
        DiscoveryReasonCode.SHARED_LIMIT_APPLIED,
    )


def test_zero_income_capacity_does_not_claim_that_shared_usage_was_applied() -> None:
    thai_esg = opportunity(discover(profile(0, sso=0)), opportunity_ids.THAI_ESG)

    assert thai_esg.status is OpportunityStatus.INELIGIBLE
    assert thai_esg.remaining_capacity == Money.zero()
    assert thai_esg.reason_codes == (DiscoveryReasonCode.NO_REMAINING_CAPACITY,)


@pytest.mark.mandatory
def test_disc_07_artwork_is_available_at_100000_when_governed_and_fully_asserted() -> None:
    result = discover(
        profile(facts=OpportunityFacts(artwork=ARTWORK_FULLY_ASSERTED)),
        catalog=artwork_ready_catalog(),
    )
    artwork = opportunity(result, opportunity_ids.ARTWORK)
    assert artwork.status is OpportunityStatus.AVAILABLE
    assert artwork.remaining_capacity == Money.of(100000)
    assert artwork.reason_codes == (DiscoveryReasonCode.ELIGIBLE_OPPORTUNITY,)
    assert artwork.evidence_requirements


@pytest.mark.mandatory
def test_disc_08_explicit_absence_of_artwork_intent_is_ineligible() -> None:
    for catalog in (production_catalog(), artwork_ready_catalog()):
        result = discover(
            profile(facts=OpportunityFacts(artwork=ArtworkIntent(intends_to_purchase=False))),
            catalog=catalog,
        )
        artwork = opportunity(result, opportunity_ids.ARTWORK)
        assert artwork.status is OpportunityStatus.INELIGIBLE
        assert artwork.reason_codes == (DiscoveryReasonCode.NO_INTRINSIC_NEED,)


@pytest.mark.mandatory
def test_disc_09_explicit_absence_of_solar_intent_is_ineligible() -> None:
    result = discover(
        profile(
            facts=OpportunityFacts(
                solar_rooftop=replace(SOLAR_FULLY_ASSERTED, intends_to_install=False)
            )
        )
    )
    solar = opportunity(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.status is not OpportunityStatus.AVAILABLE
    assert solar.status is OpportunityStatus.INELIGIBLE
    assert solar.reason_codes == (DiscoveryReasonCode.NO_INTRINSIC_NEED,)


@pytest.mark.mandatory
def test_disc_10_unverified_solar_policy_is_rule_not_ready() -> None:
    result = discover(
        profile(facts=OpportunityFacts(solar_rooftop=SOLAR_FULLY_ASSERTED)),
        catalog=solar_unverified_catalog(),
    )
    solar = opportunity(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.status is OpportunityStatus.RULE_NOT_READY
    assert solar.reason_codes == (DiscoveryReasonCode.RULE_NOT_READY,)
    assert solar.remaining_capacity is None


@pytest.mark.mandatory
@pytest.mark.golden
def test_disc_11_g01_zero_pit_keeps_the_opportunity_but_reports_no_current_benefit() -> None:
    result = discover(profile(300000))
    thai_esg = opportunity(result, opportunity_ids.THAI_ESG)
    assert thai_esg.status is OpportunityStatus.AVAILABLE
    assert thai_esg.maximum_tax_saving_at_capacity == Money.zero()
    assert DiscoveryReasonCode.ZERO_CURRENT_TAX_BENEFIT in thai_esg.reason_codes


@pytest.mark.mandatory
@pytest.mark.golden
def test_disc_12_g02_saving_on_100000_is_18500_not_20000() -> None:
    result = discover(
        profile(facts=OpportunityFacts(artwork=ARTWORK_FULLY_ASSERTED)),
        catalog=artwork_ready_catalog(),
    )
    artwork = opportunity(result, opportunity_ids.ARTWORK)
    assert artwork.remaining_capacity == Money.of(100000)
    assert artwork.maximum_tax_saving_at_capacity == Money.of(18500)


@pytest.mark.mandatory
def test_disc_13_a_missing_material_fact_requires_input_rather_than_assuming_no() -> None:
    result = discover(
        profile(
            facts=OpportunityFacts(
                solar_rooftop=replace(SOLAR_FULLY_ASSERTED, paid_to_vat_registrant=None)
            )
        ),
        catalog=solar_ready_catalog(),
    )
    solar = opportunity(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.status is OpportunityStatus.REQUIRES_INPUT
    assert solar.reason_codes == (DiscoveryReasonCode.REQUIRES_INPUT,)
    assert solar.missing_fact_ids == ("solar_rooftop.paid_to_vat_registrant",)
    assert solar.failed_fact_ids == ()


@pytest.mark.mandatory
def test_disc_16_an_opportunity_outside_its_effective_period_stays_visible() -> None:
    result = discover(
        profile(facts=OpportunityFacts(solar_rooftop=SOLAR_FULLY_ASSERTED, shared_limit_usage=())),
        catalog=solar_ready_catalog(),
        planning_date=date(2026, 1, 15),
    )
    solar = opportunity(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.status is OpportunityStatus.OUTSIDE_EFFECTIVE_PERIOD
    assert solar.reason_codes == (DiscoveryReasonCode.OUTSIDE_EFFECTIVE_PERIOD,)
    assert DiscoveryReasonCode.OUTSIDE_EFFECTIVE_PERIOD in result.reason_codes
    assert opportunity(result, opportunity_ids.THAI_ESG).status is OpportunityStatus.AVAILABLE


@pytest.mark.mandatory
def test_disc_17_an_unverified_policy_rule_blocks_availability_in_discovery() -> None:
    artwork = opportunity(discover(profile()), opportunity_ids.ARTWORK)
    assert artwork.status is OpportunityStatus.RULE_NOT_READY
    assert artwork.reason_codes == (DiscoveryReasonCode.RULE_NOT_READY,)


@pytest.mark.mandatory
def test_disc_20_the_output_carries_no_ranking_or_recommendation_semantics() -> None:
    forbidden = ("best", "recommended", "rank", "score", "priority_score")
    result = discover(
        profile(
            benefits=ExistingTaxBenefits(
                parents=(Parent("father", True),),
                mortgage_interest_paid=Money.of(125000),
                mortgage_eligible=True,
                retirement_contributions=(RetirementContribution("PVD", Money.of(100000)),),
            ),
            facts=OpportunityFacts(artwork=ARTWORK_FULLY_ASSERTED),
        )
    )

    def check_keys(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(token in key.lower() for token in forbidden), key
                check_keys(item)
        elif isinstance(value, list):
            for item in value:
                check_keys(item)

    check_keys(result.to_dict())
    for model in (DiscoveryResult, DiscoveredRight, DiscoveredOpportunity):
        for field in fields(model):
            assert not any(token in field.name.lower() for token in forbidden), field.name


@pytest.mark.golden
def test_g04_fully_used_retirement_capacity_reports_zero_remaining() -> None:
    result = discover(
        profile(
            2800000,
            benefits=ExistingTaxBenefits(
                social_security_paid=Money.of(10500),
                retirement_contributions=(RetirementContribution("PVD", Money.of(500000)),),
            ),
        )
    )
    retirement = right(result, opportunity_ids.RETIREMENT_SHARED_CAPACITY)
    assert retirement.claimed_amount == Money.of(500000)
    assert retirement.remaining_capacity == Money.zero()
    assert retirement.reason_codes == (
        DiscoveryReasonCode.EXISTING_RIGHT_AVAILABLE,
        DiscoveryReasonCode.NO_REMAINING_CAPACITY,
    )


def test_retirement_right_resolves_capacity_by_shared_group_not_position() -> None:
    user = profile(
        2800000,
        benefits=ExistingTaxBenefits(
            retirement_contributions=(RetirementContribution("PVD", Money.of(100000)),),
        ),
    )
    state = calculate_tax(user, production_pack())
    unrelated = DeductionCapacity(
        category="UNRELATED",
        standalone_limit=Money.of(1),
        amount_used=Money.zero(),
        standalone_remaining=Money.of(1),
        shared_group="UNRELATED",
        shared_limit=Money.of(1),
        shared_amount_used=Money.zero(),
        shared_remaining=Money.of(1),
        usable_amount=Money.of(1),
    )
    state = replace(state, deduction_capacities=(unrelated, *state.deduction_capacities))

    result = discover_opportunities(
        user,
        state,
        production_pack(),
        production_catalog(),
        DiscoveryContext(TaxYear(2026), PLANNING_DATE),
    )

    retirement = right(result, opportunity_ids.RETIREMENT_SHARED_CAPACITY)
    assert retirement.remaining_capacity == Money.of(400000)


@pytest.mark.golden
def test_g08_parent_and_mortgage_rights_are_both_discovered() -> None:
    result = discover(
        profile(
            benefits=ExistingTaxBenefits(
                social_security_paid=Money.of(10500),
                parents=(Parent("father", True), Parent("mother", True)),
                children=(Child("c1", order=1, legally_eligible=True, birth_year=2017),),
                mortgage_interest_paid=Money.of(125000),
                mortgage_eligible=True,
            )
        )
    )
    assert [item.right_id for item in result.existing_rights] == [
        opportunity_ids.PERSONAL_ALLOWANCE,
        opportunity_ids.PARENT_ALLOWANCE,
        opportunity_ids.CHILD_ALLOWANCE,
        opportunity_ids.SOCIAL_SECURITY,
        opportunity_ids.MORTGAGE_INTEREST,
    ]
    assert right(result, opportunity_ids.PARENT_ALLOWANCE).claimed_amount == Money.of(60000)
    assert right(result, opportunity_ids.MORTGAGE_INTEREST).claimed_amount == Money.of(100000)


@pytest.mark.golden
def test_g09_solar_is_available_only_when_every_gate_passes() -> None:
    complete = OpportunityFacts(solar_rooftop=SOLAR_FULLY_ASSERTED)
    assert (
        opportunity(
            discover(profile(facts=complete), catalog=solar_ready_catalog()),
            opportunity_ids.SOLAR_ROOFTOP,
        ).status
        is OpportunityStatus.AVAILABLE
    )
    assert (
        opportunity(
            discover(profile(facts=complete), catalog=solar_unverified_catalog()),
            opportunity_ids.SOLAR_ROOFTOP,
        ).status
        is OpportunityStatus.RULE_NOT_READY
    )
    assert (
        opportunity(
            discover(
                profile(facts=complete),
                catalog=solar_ready_catalog(),
                planning_date=date(2029, 1, 1),
            ),
            opportunity_ids.SOLAR_ROOFTOP,
        ).status
        is OpportunityStatus.OUTSIDE_EFFECTIVE_PERIOD
    )
    assert (
        opportunity(
            discover(
                profile(
                    facts=OpportunityFacts(
                        solar_rooftop=replace(SOLAR_FULLY_ASSERTED, is_natural_person=None)
                    )
                ),
                catalog=solar_ready_catalog(),
            ),
            opportunity_ids.SOLAR_ROOFTOP,
        ).status
        is OpportunityStatus.REQUIRES_INPUT
    )
    assert (
        opportunity(
            discover(
                profile(
                    facts=OpportunityFacts(
                        solar_rooftop=replace(SOLAR_FULLY_ASSERTED, is_natural_person=False)
                    )
                ),
                catalog=solar_ready_catalog(),
            ),
            opportunity_ids.SOLAR_ROOFTOP,
        ).status
        is OpportunityStatus.INELIGIBLE
    )


def test_a_declared_condition_answered_no_is_ineligible_and_names_the_failed_facts() -> None:
    solar = opportunity(
        discover(
            profile(
                facts=OpportunityFacts(
                    solar_rooftop=replace(
                        SOLAR_FULLY_ASSERTED,
                        on_grid_connected_to_mea_or_pea=False,
                        no_duplicate_tax_benefit=False,
                    )
                )
            ),
            catalog=solar_ready_catalog(),
        ),
        opportunity_ids.SOLAR_ROOFTOP,
    )
    assert solar.status is OpportunityStatus.INELIGIBLE
    assert solar.failed_fact_ids == (
        "solar_rooftop.on_grid_connected_to_mea_or_pea",
        "solar_rooftop.no_duplicate_tax_benefit",
    )
    assert solar.reason_codes == (DiscoveryReasonCode.ELIGIBILITY_CONDITION_FAILED,)


def test_personal_allowance_and_social_security_are_reported_as_existing_rights() -> None:
    result = discover(profile())
    assert right(result, opportunity_ids.PERSONAL_ALLOWANCE).claimed_amount == Money.of(60000)
    assert right(result, opportunity_ids.SOCIAL_SECURITY).claimed_amount == Money.of(10500)
    assert "UNCLAIMED" not in str(result.to_dict())


@pytest.mark.negative
def test_existing_rights_fail_closed_for_missing_rules_and_outside_periods() -> None:
    catalog_data = bundled_catalog_dict()
    catalog_definition_dict(catalog_data, opportunity_ids.PERSONAL_ALLOWANCE)["rule_ids"] = [
        "MISSING-RULE"
    ]
    personal = right(
        discover(profile(), catalog=activate_catalog_dict(catalog_data)),
        opportunity_ids.PERSONAL_ALLOWANCE,
    )
    assert personal.status is OpportunityStatus.RULE_NOT_READY
    assert personal.reason_codes == (DiscoveryReasonCode.RULE_NOT_READY,)

    catalog_data = bundled_catalog_dict()
    catalog_definition_dict(catalog_data, opportunity_ids.PERSONAL_ALLOWANCE)["effective_from"] = (
        "2027-01-01"
    )
    personal = right(
        discover(profile(), catalog=activate_catalog_dict(catalog_data)),
        opportunity_ids.PERSONAL_ALLOWANCE,
    )
    assert personal.status is OpportunityStatus.OUTSIDE_EFFECTIVE_PERIOD
    assert personal.reason_codes == (DiscoveryReasonCode.OUTSIDE_EFFECTIVE_PERIOD,)


def test_rights_absent_from_the_tax_state_are_not_reported() -> None:
    result = discover(profile(sso=0))
    assert [item.right_id for item in result.existing_rights] == [
        opportunity_ids.PERSONAL_ALLOWANCE
    ]


def test_result_reports_applied_rules_and_authoritative_sources() -> None:
    result = discover(profile(facts=OpportunityFacts(solar_rooftop=SOLAR_FULLY_ASSERTED)))
    assert "TH-PIT-ALLOWANCE-PERSONAL" in result.rules_applied
    assert opportunity_ids.THAI_ESG_RULE in result.rules_applied
    assert opportunity_ids.SOLAR_ROOFTOP_RULE in result.rules_applied
    assert len(result.rules_applied) == len(set(result.rules_applied))
    assert result.sources
    assert all(source.url.startswith("https://") for source in result.sources)
    assert len(result.sources) == len({source.source_id for source in result.sources})
    assert result.engine_version == DISCOVERY_ENGINE_VERSION
    assert result.catalog_version == production_catalog().version
    assert result.tax_state_hash == calculate_tax(profile(), production_pack()).output_hash


@pytest.mark.negative
def test_an_unsupported_tax_state_produces_an_explicit_unsupported_result() -> None:
    user = replace(
        profile(),
        income=IncomeProfile(
            section_40_1=Money.of(300000), unsupported=(UnsupportedIncome("40(8)", Money.of(1)),)
        ),
    )
    state = calculate_tax(user, production_pack())
    assert state.status is TaxStatus.ADVANCED_TAX_PATH_REQUIRED
    result = discover_opportunities(
        user,
        state,
        production_pack(),
        production_catalog(),
        DiscoveryContext(TaxYear(2026), PLANNING_DATE),
    )
    assert result.status is DiscoveryStatus.UNSUPPORTED
    assert result.reason_codes == (DiscoveryReasonCode.UNSUPPORTED_TAX_STATE,)
    assert result.existing_rights == ()
    assert result.opportunities == ()
    assert result.discovery_hash


@pytest.mark.negative
def test_discovery_rejects_misaligned_tax_years() -> None:
    user = profile()
    state = calculate_tax(user, production_pack())
    with pytest.raises(ValueError, match="tax year"):
        discover_opportunities(
            user,
            state,
            production_pack(),
            production_catalog(),
            DiscoveryContext(TaxYear(2025), PLANNING_DATE),
        )


def test_capacity_is_never_presented_as_an_amount_to_spend() -> None:
    thai_esg = opportunity(discover(profile(800000)), opportunity_ids.THAI_ESG)
    data = thai_esg.to_dict()
    assert data["remaining_capacity"] == "240000.00"
    assert data["requires_new_cash"] is True
    assert data["lockup_metadata"] == {
        "minimum_holding_years": 5,
        "measurement": "purchase-date-to-purchase-date",
    }


def test_unknown_parent_eligibility_is_an_explicit_missing_input() -> None:
    result = discover(profile(benefits=ExistingTaxBenefits(parents=(Parent("father", None),))))
    parent = right(result, opportunity_ids.PARENT_ALLOWANCE)
    assert parent.status is OpportunityStatus.REQUIRES_INPUT
    assert parent.missing_fact_ids == ("parent.father.eligible",)


@pytest.mark.negative
def test_explicitly_ineligible_rights_are_not_reported_as_available() -> None:
    result = discover(
        profile(
            benefits=ExistingTaxBenefits(
                parents=(Parent("father", False),),
                children=(Child("c1", order=1, legally_eligible=False, birth_year=2018),),
                mortgage_interest_paid=Money.of(125000),
                mortgage_eligible=False,
            )
        )
    )
    ids = {item.right_id for item in result.existing_rights}
    assert opportunity_ids.PARENT_ALLOWANCE not in ids
    assert opportunity_ids.CHILD_ALLOWANCE not in ids
    assert opportunity_ids.MORTGAGE_INTEREST not in ids


@pytest.mark.negative
def test_unknown_shared_pool_usage_requires_input() -> None:
    thai_esg = opportunity(discover(profile(facts=OpportunityFacts())), opportunity_ids.THAI_ESG)
    assert thai_esg.status is OpportunityStatus.REQUIRES_INPUT
    assert thai_esg.reason_codes == (DiscoveryReasonCode.REQUIRES_INPUT,)
    assert thai_esg.missing_fact_ids == ("shared_limit_usage.THAI_ESG_2026_POOL",)


@pytest.mark.negative
def test_discovery_rejects_a_tax_state_from_another_profile() -> None:
    user = profile(100000)
    other = profile(800000)
    with pytest.raises(ValueError, match="tax state does not match"):
        discover_opportunities(
            user,
            calculate_tax(other, production_pack()),
            production_pack(),
            production_catalog(),
            DiscoveryContext(TaxYear(2026), PLANNING_DATE),
        )


@pytest.mark.golden
def test_g03_high_income_discovery_has_capped_capacity_and_positive_tax_impact() -> None:
    result = discover(profile(2_800_000))
    thai_esg = opportunity(result, opportunity_ids.THAI_ESG)
    assert thai_esg.remaining_capacity == Money.of(300000)
    assert thai_esg.maximum_tax_saving_at_capacity is not None
    assert thai_esg.maximum_tax_saving_at_capacity.is_positive()


def test_unknown_intrinsic_intent_requires_input_after_the_rule_is_ready() -> None:
    artwork = opportunity(
        discover(profile(), catalog=artwork_ready_catalog()), opportunity_ids.ARTWORK
    )
    assert artwork.status is OpportunityStatus.REQUIRES_INPUT
    assert artwork.reason_codes == (DiscoveryReasonCode.REQUIRES_INPUT,)


def test_zero_standalone_capacity_without_a_shared_group_is_not_available() -> None:
    catalog = mark_rule_ready(bundled_catalog_dict(), opportunity_ids.ARTWORK_RULE)
    catalog_definition_dict(catalog, opportunity_ids.ARTWORK)["standalone_limit"] = "0.00"
    next(rule for rule in catalog["rules"] if rule["rule_id"] == opportunity_ids.ARTWORK_RULE)[
        "parameters"
    ]["cap"] = "0.00"
    artwork = opportunity(
        discover(
            profile(facts=OpportunityFacts(artwork=ARTWORK_FULLY_ASSERTED)),
            catalog=activate_catalog_dict(catalog),
        ),
        opportunity_ids.ARTWORK,
    )
    assert artwork.status is OpportunityStatus.INELIGIBLE
    assert artwork.reason_codes == (DiscoveryReasonCode.NO_REMAINING_CAPACITY,)


def test_unresolved_catalog_references_fail_closed_and_are_not_serialized_as_sources() -> None:
    catalog = bundled_catalog_dict()
    thai_esg = catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)
    thai_esg["rule_ids"] = [opportunity_ids.THAI_ESG_RULE, "MISSING-RULE"]
    thai_esg["source_ids"] = ["MISSING-SOURCE"]
    result = discover(profile(), catalog=activate_catalog_dict(catalog))
    item = opportunity(result, opportunity_ids.THAI_ESG)
    assert item.status is OpportunityStatus.RULE_NOT_READY
    assert all(source.source_id != "MISSING-SOURCE" for source in result.sources)
