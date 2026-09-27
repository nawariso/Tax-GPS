"""R2: profile-bound discovery replay is capacity authority, not a rehashed result."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.calculation.models import TaxState
from tax_gps.candidate.activation import activate_allocation_policy, bundled_allocation_policy
from tax_gps.candidate.audit import create_candidate_snapshot, replay_candidates
from tax_gps.candidate.engine import build_candidates
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.capacity import calculate_opportunity_capacity
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.discovery.models import DiscoveredOpportunity, DiscoveryResult
from tax_gps.engine import calculate_tax
from tax_gps.financial.engine import evaluate_guardrails
from tax_gps.financial.models import GuardrailResult
from tax_gps.financial.policy import activate_financial_policy, bundled_financial_policy
from tax_gps.financial.profile import FinancialPlanningContext
from tax_gps.financial.state import FinancialState
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.models import OpportunityStatus
from tax_gps.profile.models import SharedLimitUsage, UserProfile
from tests.acceptance.test_candidates import _inputs, _profile
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack


def _thai_esg(discovery: DiscoveryResult) -> DiscoveredOpportunity:
    return next(
        item for item in discovery.opportunities if item.opportunity_id == opportunity_ids.THAI_ESG
    )


def _case(
    profile: UserProfile,
) -> tuple[UserProfile, TaxState, DiscoveryResult, FinancialState, GuardrailResult]:
    tax = calculate_tax(profile, production_pack())
    discovery = discover_opportunities(
        profile,
        tax,
        production_pack(),
        production_catalog(),
        DiscoveryContext(TaxYear(2026), date(2026, 6, 1)),
    )
    financial = _inputs(budget="400000")[2]
    financial_policy = activate_financial_policy(bundled_financial_policy(TaxYear(2026)))
    guards = evaluate_guardrails(
        discovery,
        financial,
        financial_policy,
        FinancialPlanningContext(date(2026, 6, 1), Money.of(400000)),
    )
    return profile, tax, discovery, financial, guards


def _tamper(
    tax: TaxState, discovery: DiscoveryResult, financial: FinancialState, capacity: Money
) -> tuple[DiscoveryResult, GuardrailResult]:
    # Deliberately recompute every hash an upstream caller can produce. A hash is
    # integrity metadata, not proof that P1-002 derived the capacity from profile facts.
    item = next(x for x in discovery.opportunities if x.opportunity_id == opportunity_ids.THAI_ESG)
    replacement = replace(
        item,
        remaining_capacity=capacity,
        maximum_tax_saving_at_capacity=tax.tax_impact(capacity).saving,
    )
    forged = replace(
        discovery,
        opportunities=tuple(
            replacement if x.opportunity_id == item.opportunity_id else x
            for x in discovery.opportunities
        ),
    )
    forged = replace(forged, discovery_hash=sha256_hex(canonical_json(forged.material_dict())))
    financial_policy = activate_financial_policy(bundled_financial_policy(TaxYear(2026)))
    guards = evaluate_guardrails(
        forged,
        financial,
        financial_policy,
        FinancialPlanningContext(date(2026, 6, 1), Money.of(400000)),
    )
    assert forged.discovery_hash == sha256_hex(canonical_json(forged.material_dict()))
    assert guards.guardrail_hash == sha256_hex(canonical_json(guards.material_dict()))
    assert guards.discovery_hash == forged.discovery_hash
    return forged, guards


@pytest.mark.golden
def test_r2_a_untampered_discovery_activates_and_preserves_golden_and_replay() -> None:
    profile, tax, discovery, financial, guards = _case(_profile())
    raw = bundled_allocation_policy(profile, tax, discovery, production_catalog())
    active = activate_allocation_policy(raw, profile, tax, discovery, production_catalog())
    result = build_candidates(tax, discovery, financial, guards, active)
    assert active.profile_hash == profile.profile_hash() == discovery.profile_hash
    assert active.discovery_hash == discovery.discovery_hash
    assert active.tax_state_hash == tax.output_hash
    assert active.catalog_hash == production_catalog().content_hash
    assert active.content_hash == result.policy_hash
    assert [c.total_allocation.canonical() for c in result.candidates] == ["0.00", "297150.00"]
    assert result.candidates[0].tax_before == result.candidates[0].tax_after
    assert result.candidates[1].deductible_amount == Money.of(297150)
    snapshot = create_candidate_snapshot(result)
    assert profile.profile_id not in repr(snapshot.output)
    assert replay_candidates(snapshot, tax, discovery, financial, guards, active) == result


@pytest.mark.negative
def test_r2_b_income_ceiling_forgery_with_rehashed_discovery_and_guardrails_fails() -> None:
    profile, tax, discovery, financial, _ = _case(_profile())
    original = _thai_esg(discovery)
    assert original.remaining_capacity == Money.of(297150)
    forged, guards = _tamper(tax, discovery, financial, Money.of(300000))
    assert (
        _thai_esg(forged).maximum_tax_saving_at_capacity == tax.tax_impact(Money.of(300000)).saving
    )
    with pytest.raises(ValueError, match="governed catalog rule"):
        bundled_allocation_policy(profile, tax, forged, production_catalog())
    raw = bundled_allocation_policy(profile, tax, discovery, production_catalog())
    with pytest.raises(ValueError, match="governed catalog rule"):
        activate_allocation_policy(raw, profile, tax, forged, production_catalog())
    assert guards.discovery_hash == forged.discovery_hash


@pytest.mark.negative
def test_r2_c_catalog_standalone_cap_forgery_fails() -> None:
    profile, tax, discovery, financial, _ = _case(_profile(Money.of(2000000)))
    actual = _thai_esg(discovery)
    assert actual.remaining_capacity == Money.of(300000)
    forged, _ = _tamper(tax, discovery, financial, Money.of(310000))
    with pytest.raises(ValueError, match="governed catalog rule"):
        bundled_allocation_policy(profile, tax, forged, production_catalog())


@pytest.mark.golden
def test_r2_e_nonzero_accepted_shared_usage_yields_exact_remaining() -> None:
    usage = (SharedLimitUsage(opportunity_ids.THAI_ESG_2026_POOL, Money.of(25000)),)
    profile, tax, discovery, financial, guards = _case(_profile(shared_limit_usage=usage))
    actual = _thai_esg(discovery)
    assert actual.remaining_capacity == Money.of(272150)
    raw = bundled_allocation_policy(profile, tax, discovery, production_catalog())
    assert raw.shared_limits[0].remaining == Money.of(272150)
    active = activate_allocation_policy(raw, profile, tax, discovery, production_catalog())
    result = build_candidates(tax, discovery, financial, guards, active)
    assert result.candidates[-1].total_allocation == Money.of(272150)


@pytest.mark.negative
def test_r2_f_nonzero_usage_forged_remainder_with_all_hashes_recomputed_fails() -> None:
    usage = (SharedLimitUsage(opportunity_ids.THAI_ESG_2026_POOL, Money.of(25000)),)
    profile, tax, discovery, financial, _ = _case(_profile(shared_limit_usage=usage))
    forged, _ = _tamper(tax, discovery, financial, Money.of(297150))
    with pytest.raises(ValueError, match="governed catalog rule"):
        bundled_allocation_policy(profile, tax, forged, production_catalog())
    raw = bundled_allocation_policy(profile, tax, discovery, production_catalog())
    with pytest.raises(ValueError, match="governed catalog rule"):
        activate_allocation_policy(raw, profile, tax, forged, production_catalog())


@pytest.mark.negative
def test_r2_g_profile_hash_mismatch_fails_before_policy_construction() -> None:
    _, tax, discovery, _, _ = _case(_profile())
    wrong = replace(_profile(), profile_id="wrong-profile")
    with pytest.raises(ValueError, match="profile hash"):
        bundled_allocation_policy(wrong, tax, discovery, production_catalog())


@pytest.mark.negative
def test_r2_h_unknown_shared_usage_has_no_allocatable_candidate() -> None:
    profile, tax, discovery, financial, guards = _case(_profile(shared_limit_usage=None))
    item = _thai_esg(discovery)
    assert item.status is OpportunityStatus.REQUIRES_INPUT
    assert item.remaining_capacity is None
    raw = bundled_allocation_policy(profile, tax, discovery, production_catalog())
    active = activate_allocation_policy(raw, profile, tax, discovery, production_catalog())
    result = build_candidates(tax, discovery, financial, guards, active)
    assert len(result.candidates) == 1
    assert result.candidates[0].allocations == ()


@pytest.mark.negative
def test_r2_unknown_usage_cannot_be_promoted_to_available_by_rehashing() -> None:
    profile, tax, discovery, _, _ = _case(_profile(shared_limit_usage=None))
    item = _thai_esg(discovery)
    forged_item = replace(
        item,
        status=OpportunityStatus.AVAILABLE,
        remaining_capacity=Money.of(297150),
        maximum_tax_saving_at_capacity=tax.tax_impact(Money.of(297150)).saving,
    )
    forged = replace(
        discovery,
        opportunities=tuple(
            forged_item if x.opportunity_id == item.opportunity_id else x
            for x in discovery.opportunities
        ),
    )
    forged = replace(forged, discovery_hash=sha256_hex(canonical_json(forged.material_dict())))
    with pytest.raises(ValueError, match="unknown shared usage"):
        bundled_allocation_policy(profile, tax, forged, production_catalog())


@pytest.mark.golden
def test_r2_d_governed_income_rate_and_prior_usage_capacity_contract() -> None:
    catalog = production_catalog().catalog
    definition = catalog.definition(opportunity_ids.THAI_ESG)
    rule = catalog.rule(definition.rule_ids[0])
    assert rule.parameters["cap"] == "300000.00"
    assert rule.parameters["assessable_income_rate"] == "0.30"
    profile = _profile(
        shared_limit_usage=(SharedLimitUsage(opportunity_ids.THAI_ESG_2026_POOL, Money.of(25000)),)
    )
    _, tax, discovery, _, _ = _case(profile)
    usage = profile.opportunity_facts.shared_limit_amount_used(definition.shared_limit_group)
    assert usage == Money.of(25000)
    governed = calculate_opportunity_capacity(
        definition,
        catalog,
        assessable_income=tax.income.assessable_income,
        shared_amount_used=usage,
    )
    assert governed.standalone_limit == Money.of(300000)
    assert governed.shared_limit == Money.of(297150)
    assert (
        governed.remaining_capacity == _thai_esg(discovery).remaining_capacity == Money.of(272150)
    )
