"""TGPS-P1-004: deterministic feasible allocations, outcomes, and fail-closed replay."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.calculation.models import TaxState
from tax_gps.candidate.activation import activate_allocation_policy, bundled_allocation_policy
from tax_gps.candidate.audit import create_candidate_snapshot, replay_candidates
from tax_gps.candidate.engine import _construct_candidates, build_candidates
from tax_gps.candidate.models import (
    AllocationPolicy,
    CandidateResult,
    DeductionSemantics,
    OpportunityTreatment,
    SharedLimit,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.engine import calculate_tax
from tax_gps.financial.engine import evaluate_guardrails
from tax_gps.financial.models import GuardrailDecision, GuardrailResult
from tax_gps.financial.policy import activate_financial_policy, bundled_financial_policy
from tax_gps.financial.profile import FinancialPlanningContext, FinancialProfile, ProtectionProfile
from tax_gps.financial.reason_codes import FinancialReasonCode
from tax_gps.financial.state import FinancialState, compute_financial_state
from tax_gps.opportunity import opportunity_ids
from tax_gps.profile.models import ExistingTaxBenefits, IncomeProfile, OpportunityFacts, UserProfile
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack


def _inputs(
    *, budget: str = "100000", assets: str | None = "500000", salary: int = 990500
) -> tuple[TaxState, DiscoveryResult, FinancialState, GuardrailResult, AllocationPolicy]:
    profile = UserProfile(
        profile_id="employee",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(salary)),
        benefits=ExistingTaxBenefits(social_security_paid=Money.of(10500)),
        opportunity_facts=OpportunityFacts(shared_limit_usage=()),
    )
    tax = calculate_tax(profile, production_pack())
    discovery = discover_opportunities(
        profile,
        tax,
        production_pack(),
        production_catalog(),
        DiscoveryContext(TaxYear(2026), date(2026, 6, 1)),
    )
    context = FinancialPlanningContext(date(2026, 6, 1), Money.of(budget))
    financial_policy = activate_financial_policy(bundled_financial_policy(TaxYear(2026)))
    financial = compute_financial_state(
        FinancialProfile(
            liquid_assets=Money.of(assets) if assets is not None else None,
            monthly_essential_expenses=Money.of(50000),
            debts=(),
            committed_cash_needs=(),
            protection=ProtectionProfile(),
        ),
        financial_policy,
        context,
    )
    guardrails = evaluate_guardrails(discovery, financial, financial_policy, context)
    policy = bundled_allocation_policy(tax, discovery, production_catalog())
    return tax, discovery, financial, guardrails, policy


def _build(
    inputs: tuple[TaxState, DiscoveryResult, FinancialState, GuardrailResult, AllocationPolicy],
) -> CandidateResult:
    tax, discovery, financial, guards, raw = inputs
    active = activate_allocation_policy(raw, tax, discovery, production_catalog())
    return build_candidates(tax, discovery, financial, guards, active)


def _build_synthetic(
    inputs: tuple[TaxState, DiscoveryResult, FinancialState, GuardrailResult, AllocationPolicy],
) -> CandidateResult:
    """Exercise boundary mechanics only; this cannot activate production authority."""
    return _construct_candidates(*inputs)


@pytest.mark.negative
def test_r1_raw_allocation_policy_cannot_enter_production_engine() -> None:
    tax, discovery, financial, guards, raw = _inputs()
    with pytest.raises(ValueError, match="activated allocation policy"):
        build_candidates(tax, discovery, financial, guards, raw)  # type: ignore[arg-type]


@pytest.mark.golden
def test_employee_baseline_and_full_deduction_exact_outcomes() -> None:
    result = _build(_inputs())
    assert [item.total_allocation.canonical() for item in result.candidates] == [
        "0.00",
        "100000.00",
    ]
    baseline, allocated = result.candidates
    assert baseline.allocations == ()
    assert baseline.reason_codes == ("NO_ACTION_BASELINE",)
    assert baseline.tax_before == baseline.tax_after == Money.of(79000)
    assert baseline.cash_outflow == Money.zero()
    assert baseline.unused_budget == Money.of(100000)
    assert baseline.spendable_surplus_after == Money.of(350000)
    assert allocated.deductible_amount == Money.of(100000)
    assert allocated.tax_before == Money.of(79000)
    assert allocated.tax_after == Money.of(60500)
    assert allocated.tax_saved == Money.of(18500)
    assert allocated.cash_outflow == Money.of(100000)
    assert allocated.unused_budget == Money.zero()
    assert allocated.spendable_surplus_after == Money.of(250000)
    assert allocated.protection_gap is None
    assert allocated.candidate_id == sha256_hex(canonical_json(allocated.allocation_dict()))


@pytest.mark.boundary
def test_zero_budget_and_guardrail_cap() -> None:
    assert len(_build(_inputs(budget="0")).candidates) == 1
    tax, discovery, financial, guardrails, policy = _inputs(assets="200000")
    assert (
        next(
            a for a in guardrails.assessments if a.opportunity_id == opportunity_ids.THAI_ESG
        ).decision
        is GuardrailDecision.CAP
    )
    result = _build((tax, discovery, financial, guardrails, policy))
    assert [c.total_allocation.canonical() for c in result.candidates] == ["0.00", "50000.00"]
    assert result.candidates[1].spendable_surplus_after == Money.zero()
    assert "GUARDRAIL_CAP_APPLIED" in result.candidates[1].reason_codes


@pytest.mark.golden
def test_zero_tax_benefit_still_reduces_surplus() -> None:
    result = _build(_inputs(salary=200000))
    assert result.candidates[-1].tax_saved == Money.zero()
    assert result.candidates[-1].cash_outflow == Money.of(60000)
    assert result.candidates[-1].spendable_surplus_after == Money.of(290000)


@pytest.mark.negative
def test_partial_state_preserves_unknown_and_emits_baseline_only() -> None:
    result = _build(_inputs(budget="0", assets=None))
    assert len(result.candidates) == 1
    assert result.candidates[0].spendable_surplus_after is None
    assert "PARTIAL_FINANCIAL_STATE" in result.candidates[0].reason_codes


@pytest.mark.negative
def test_inconsistent_budget_and_tampered_inputs_fail_closed() -> None:
    inputs = _inputs()
    with pytest.raises(ValueError, match="integrity mismatch"):
        _build((*inputs[:3], replace(inputs[3], available_budget=Money.of(100001)), inputs[4]))
    with pytest.raises(ValueError, match="tax state"):
        _build((replace(inputs[0], pit=Money.zero()), *inputs[1:]))
    with pytest.raises(ValueError, match="discovery integrity"):
        _build((*inputs[:1], replace(inputs[1], discovery_hash="wrong"), *inputs[2:]))


@pytest.mark.replay
def test_reordered_upstream_collections_keep_allocations_ids_and_outcomes() -> None:
    tax, discovery, financial, guardrails, policy = _inputs()
    reordered = replace(discovery, opportunities=tuple(reversed(discovery.opportunities)))
    reordered = replace(
        reordered, discovery_hash=sha256_hex(canonical_json(reordered.material_dict()))
    )
    guards = replace(
        guardrails,
        discovery_hash=reordered.discovery_hash,
        assessments=tuple(reversed(guardrails.assessments)),
    )
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    left = _build((tax, discovery, financial, guardrails, policy))
    right = _build((tax, reordered, financial, guards, policy))
    assert [c.allocation_dict() for c in left.candidates] == [
        c.allocation_dict() for c in right.candidates
    ]
    assert [c.candidate_id for c in left.candidates] == [c.candidate_id for c in right.candidates]
    assert [c.tax_saved for c in left.candidates] == [c.tax_saved for c in right.candidates]


def _two_opportunities(
    *, same_group: bool = True
) -> tuple[TaxState, DiscoveryResult, FinancialState, GuardrailResult, AllocationPolicy]:
    tax, discovery, financial, guards, policy = _inputs(budget="150000")
    original = next(
        o for o in discovery.opportunities if o.opportunity_id == opportunity_ids.THAI_ESG
    )
    extra = replace(
        original,
        opportunity_id="TEST-SECOND",
        name="Synthetic governed allocation",
        shared_limit_group=original.shared_limit_group if same_group else None,
    )
    discovery = replace(discovery, opportunities=(*discovery.opportunities, extra))
    discovery = replace(
        discovery, discovery_hash=sha256_hex(canonical_json(discovery.material_dict()))
    )
    first = next(a for a in guards.assessments if a.opportunity_id == opportunity_ids.THAI_ESG)
    guards = replace(
        guards,
        discovery_hash=discovery.discovery_hash,
        assessments=(*guards.assessments, replace(first, opportunity_id="TEST-SECOND")),
    )
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    policy = replace(
        policy,
        treatments=(
            *policy.treatments,
            OpportunityTreatment("TEST-SECOND", DeductionSemantics.FULL_ALLOCATION_DEDUCTION),
        ),
        shared_limits=(SharedLimit(opportunity_ids.THAI_ESG_2026_POOL, Money.of(100000)),),
    )
    return tax, discovery, financial, guards, policy


@pytest.mark.golden
@pytest.mark.boundary
def test_shared_limit_collision_and_full_deduction() -> None:
    result = _build_synthetic(_two_opportunities())
    assert [c.total_allocation.canonical() for c in result.candidates] == [
        "0.00",
        "100000.00",
        "100000.00",
    ]
    assert all(c.total_allocation <= Money.of(100000) for c in result.candidates)
    allocated = next(
        c
        for c in result.candidates
        if c.allocations and c.allocations[0].opportunity_id == "TEST-SECOND"
    )
    assert allocated.deductible_amount == Money.of(100000)
    assert allocated.tax_saved == Money.of(18500)
    assert "SHARED_LIMIT_APPLIED" in allocated.reason_codes
    assert len({c.candidate_id for c in result.candidates}) == 3


@pytest.mark.golden
def test_multiple_opportunities_with_budget_enforcement() -> None:
    result = _build_synthetic(_two_opportunities(same_group=False))
    assert sorted(c.total_allocation.canonical() for c in result.candidates) == [
        "0.00",
        "100000.00",
        "150000.00",
        "150000.00",
        "50000.00",
    ]
    assert all(c.unused_budget >= Money.zero() for c in result.candidates)
    unrelated = next(
        c
        for c in result.candidates
        if len(c.allocations) == 1
        and c.allocations[0].opportunity_id == "TEST-SECOND"
        and c.total_allocation == Money.of(150000)
    )
    assert "SHARED_LIMIT_APPLIED" not in unrelated.reason_codes
    tax, discovery, financial, guards, policy = _two_opportunities(same_group=False)
    policy = replace(
        policy, shared_limits=(SharedLimit(opportunity_ids.THAI_ESG_2026_POOL, Money.of(150000)),)
    )
    guards = replace(
        guards,
        assessments=tuple(
            replace(a, max_feasible_allocation=Money.of(100000))
            if a.opportunity_id in (opportunity_ids.THAI_ESG, "TEST-SECOND")
            else a
            for a in guards.assessments
        ),
    )
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    combined = next(
        c
        for c in _build_synthetic((tax, discovery, financial, guards, policy)).candidates
        if len(c.allocations) == 2 and c.total_allocation == Money.of(150000)
    )
    assert "SHARED_LIMIT_APPLIED" not in combined.reason_codes


@pytest.mark.negative
def test_candidate_bound_overflow_fails_closed() -> None:
    inputs = _two_opportunities()
    with pytest.raises(ValueError, match="maximum exceeded"):
        _build_synthetic((*inputs[:4], replace(inputs[4], max_candidates=2)))


@pytest.mark.negative
def test_product_space_over_eight_allocatable_opportunities_fails_before_expansion() -> None:
    tax, discovery, financial, guards, policy = _inputs()
    original = next(
        o for o in discovery.opportunities if o.opportunity_id == opportunity_ids.THAI_ESG
    )
    first = next(a for a in guards.assessments if a.opportunity_id == opportunity_ids.THAI_ESG)
    extras = tuple(replace(original, opportunity_id=f"TEST-{index}") for index in range(8))
    discovery = replace(discovery, opportunities=(*discovery.opportunities, *extras))
    discovery = replace(
        discovery, discovery_hash=sha256_hex(canonical_json(discovery.material_dict()))
    )
    guards = replace(
        guards,
        discovery_hash=discovery.discovery_hash,
        assessments=(
            *guards.assessments,
            *(replace(first, opportunity_id=item.opportunity_id) for item in extras),
        ),
    )
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    policy = replace(
        policy,
        treatments=(
            *policy.treatments,
            *(
                OpportunityTreatment(
                    item.opportunity_id, DeductionSemantics.FULL_ALLOCATION_DEDUCTION
                )
                for item in extras
            ),
        ),
    )
    with pytest.raises(ValueError, match="opportunity maximum"):
        _build_synthetic((tax, discovery, financial, guards, policy))


@pytest.mark.negative
def test_policy_maximum_cannot_disable_engine_hard_bound() -> None:
    inputs = _inputs()
    with pytest.raises(ValueError, match="maximum"):
        _build((*inputs[:4], replace(inputs[4], max_candidates=257)))


@pytest.mark.negative
@pytest.mark.parametrize("bad", ["", "duplicate", "shared-duplicate", "zero", "boolean"])
def test_allocation_policy_rejects_malformed_constraints(bad: str) -> None:
    policy = _inputs()[-1]
    if bad == "":
        with pytest.raises(ValueError, match="invalid allocation policy"):
            replace(policy, policy_id="")
    elif bad == "duplicate":
        with pytest.raises(ValueError, match="duplicate opportunity treatment"):
            replace(policy, treatments=(*policy.treatments, *policy.treatments))
    elif bad == "shared-duplicate":
        with pytest.raises(ValueError, match="duplicate shared allocation limit"):
            replace(policy, shared_limits=(*policy.shared_limits, *policy.shared_limits))
    elif bad == "zero":
        with pytest.raises(ValueError, match="invalid allocation policy"):
            replace(policy, max_candidates=0)
    else:
        with pytest.raises(ValueError, match="invalid allocation policy"):
            replace(policy, max_candidates=True)


@pytest.mark.negative
def test_deduction_treatment_rejects_unsupported_semantics() -> None:
    with pytest.raises(ValueError, match="FULL_ALLOCATION_DEDUCTION"):
        OpportunityTreatment("TEST", DeductionSemantics.PERCENTAGE_OF_ALLOCATION)
    with pytest.raises(TypeError, match="positional"):
        OpportunityTreatment("TEST", DeductionSemantics.FULL_ALLOCATION_DEDUCTION, "0.5")  # type: ignore[call-arg]


@pytest.mark.negative
def test_missing_treatment_or_shared_limit_fails_closed() -> None:
    inputs = _inputs()
    with pytest.raises(ValueError, match="omits treatment"):
        _build((*inputs[:4], replace(inputs[4], treatments=())))
    with pytest.raises(ValueError, match="omits shared group"):
        _build((*inputs[:4], replace(inputs[4], shared_limits=())))


@pytest.mark.negative
def test_inconsistent_guardrail_cap_and_duplicate_assessment_refused() -> None:
    tax, discovery, financial, guards, policy = _inputs()
    guards = replace(guards, assessments=(*guards.assessments, guards.assessments[-1]))
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    with pytest.raises(ValueError, match="assessments must match"):
        _build((tax, discovery, financial, guards, policy))
    guards = _inputs()[3]
    assessments = tuple(
        replace(a, max_feasible_allocation=Money.of(200000))
        if a.opportunity_id == opportunity_ids.THAI_ESG
        else a
        for a in guards.assessments
    )
    guards = replace(guards, assessments=assessments)
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    with pytest.raises(ValueError, match="invalid allocatable"):
        _build((tax, discovery, financial, guards, policy))


@pytest.mark.negative
def test_consistent_hashes_still_reject_mismatched_upstream_identity() -> None:
    tax, discovery, financial, guards, policy = _inputs()
    guards = replace(guards, financial_state_hash="different")
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    with pytest.raises(ValueError, match="identities or readiness"):
        _build((tax, discovery, financial, guards, policy))


@pytest.mark.boundary
def test_future_opportunity_without_shared_group_uses_own_ceiling() -> None:
    tax, discovery, financial, guards, policy = _two_opportunities(same_group=False)
    discovery = replace(
        discovery,
        opportunities=tuple(
            replace(item, shared_limit_group=None)
            if item.opportunity_id == opportunity_ids.THAI_ESG
            else item
            for item in discovery.opportunities
        ),
    )
    discovery = replace(
        discovery, discovery_hash=sha256_hex(canonical_json(discovery.material_dict()))
    )
    guards = replace(guards, discovery_hash=discovery.discovery_hash)
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    result = _build_synthetic((tax, discovery, financial, guards, policy))
    assert len(result.candidates) >= 3
    assert all(c.total_allocation <= guards.available_budget for c in result.candidates)


@pytest.mark.negative
def test_tax_impact_requires_matching_authoritative_baseline() -> None:
    tax, discovery, financial, guards, policy = _inputs()
    tax = replace(tax, pit=Money.zero())
    tax = replace(tax, output_hash=sha256_hex(canonical_json(tax.material_dict())))
    discovery = replace(discovery, tax_state_hash=tax.output_hash)
    discovery = replace(
        discovery, discovery_hash=sha256_hex(canonical_json(discovery.material_dict()))
    )
    guards = replace(guards, discovery_hash=discovery.discovery_hash)
    guards = replace(guards, guardrail_hash=sha256_hex(canonical_json(guards.material_dict())))
    with pytest.raises(ValueError, match="tax baseline differs"):
        _build((tax, discovery, financial, guards, policy))


@pytest.mark.negative
def test_shared_limit_and_treatment_contract_reject_bad_values() -> None:
    with pytest.raises(ValueError, match="FULL_ALLOCATION_DEDUCTION"):
        OpportunityTreatment("TEST", "UNRECOGNIZED")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid shared"):
        SharedLimit("", Money.zero())
    with pytest.raises(ValueError, match="invalid shared"):
        SharedLimit("POOL", Money.of(-1))
    with pytest.raises(ValueError, match="FULL_ALLOCATION_DEDUCTION"):
        OpportunityTreatment("", DeductionSemantics.FULL_ALLOCATION_DEDUCTION)
    policy = _inputs()[-1]
    treatments = list(policy.treatments)
    shared = list(policy.shared_limits)
    frozen = replace(policy, treatments=treatments, shared_limits=shared)  # type: ignore[arg-type]
    treatments.clear()
    shared.clear()
    assert frozen.treatments == policy.treatments
    assert frozen.shared_limits == policy.shared_limits


@pytest.mark.golden
def test_no_action_only_when_guardrail_blocks_new_cash() -> None:
    tax, discovery, _, _, policy = _inputs(budget="50000")
    context = FinancialPlanningContext(date(2026, 6, 1), Money.of(50000))
    financial_policy = activate_financial_policy(bundled_financial_policy(TaxYear(2026)))
    financial = compute_financial_state(
        FinancialProfile(
            liquid_assets=Money.of(100000),
            monthly_essential_expenses=Money.of(50000),
            debts=(),
            committed_cash_needs=(),
            protection=ProtectionProfile(),
        ),
        financial_policy,
        context,
    )
    guards = evaluate_guardrails(discovery, financial, financial_policy, context)
    result = _build((tax, discovery, financial, guards, policy))
    assert [c.total_allocation.canonical() for c in result.candidates] == ["0.00"]
    assert result.candidates[0].tax_before == result.candidates[0].tax_after
    assert FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR in financial.reason_codes


@pytest.mark.boundary
@pytest.mark.parametrize("budget", ["99999.99", "100000.00", "100000.01"])
def test_satang_budget_boundaries(budget: str) -> None:
    result = _build(_inputs(budget=budget))
    assert result.candidates[-1].total_allocation == Money.of(budget)
    assert result.candidates[-1].unused_budget == Money.zero()
    assert all(c.total_allocation <= Money.of(budget) for c in result.candidates)


@pytest.mark.golden
def test_known_protection_gap_propagates_without_estimate() -> None:
    tax, discovery, _, _, policy = _inputs()
    financial_policy = activate_financial_policy(bundled_financial_policy(TaxYear(2026)))
    context = FinancialPlanningContext(date(2026, 6, 1), Money.of(100000))
    state = compute_financial_state(
        FinancialProfile(
            liquid_assets=Money.of(500000),
            monthly_essential_expenses=Money.of(50000),
            debts=(),
            committed_cash_needs=(),
            protection=ProtectionProfile(Money.of(3000000), Money.of(1000000)),
        ),
        financial_policy,
        context,
    )
    guards = evaluate_guardrails(discovery, state, financial_policy, context)
    result = _build((tax, discovery, state, guards, policy))
    assert [c.protection_gap for c in result.candidates] == [Money.of(2000000)] * 2


@pytest.mark.replay
def test_policy_tuple_order_does_not_change_hash_or_outcomes() -> None:
    inputs = _two_opportunities()
    policy = inputs[-1]
    reordered = replace(policy, treatments=tuple(reversed(policy.treatments)))
    assert reordered.content_hash() == policy.content_hash()
    assert (
        _build_synthetic((*inputs[:4], reordered)).to_dict() == _build_synthetic(inputs).to_dict()
    )


@pytest.mark.replay
def test_snapshot_serialization_and_replay() -> None:
    inputs = _inputs()
    result = _build(inputs)
    snapshot = create_candidate_snapshot(result)
    tax, discovery, financial, guards, raw = inputs
    active = activate_allocation_policy(raw, tax, discovery, production_catalog())
    assert (
        replay_candidates(snapshot, tax, discovery, financial, guards, active).to_dict()
        == result.to_dict()
    )
    with pytest.raises(ValueError, match="replay"):
        replay_candidates(
            replace(snapshot, result_hash="bad"), tax, discovery, financial, guards, active
        )


@pytest.mark.negative
@pytest.mark.parametrize(
    "variant", ["tax_policy", "discovery_hash", "missing_treatment", "missing_group"]
)
def test_synthetic_constructor_rejects_invalid_upstream_or_policy(variant: str) -> None:
    tax, discovery, financial, guards, policy = _inputs()
    if variant == "tax_policy":
        tax = replace(tax, rule_pack_version="forged")
        tax = replace(tax, output_hash=sha256_hex(canonical_json(tax.material_dict())))
    elif variant == "discovery_hash":
        discovery = replace(discovery, discovery_hash="forged")
    elif variant == "missing_treatment":
        policy = replace(policy, treatments=())
    else:
        policy = replace(policy, shared_limits=())
    with pytest.raises(ValueError, match=r"integrity|deduction treatment|common remaining limit"):
        _build_synthetic((tax, discovery, financial, guards, policy))
