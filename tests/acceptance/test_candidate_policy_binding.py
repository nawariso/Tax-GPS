"""R1 policy authority, upstream tax consistency, and shared-capacity refusal."""

from dataclasses import replace

import pytest

from tax_gps.calculation.models import TaxState
from tax_gps.candidate.activation import (
    _shared_groups,
    activate_allocation_policy,
    bundled_allocation_policy,
)
from tax_gps.candidate.audit import create_candidate_snapshot, replay_candidates
from tax_gps.candidate.engine import build_candidates
from tax_gps.candidate.models import (
    AllocationPolicy,
    DeductionSemantics,
    OpportunityTreatment,
    SharedLimit,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.financial.models import GuardrailResult
from tax_gps.financial.state import FinancialState
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.opportunity.models import OpportunityStatus
from tax_gps.policy.models import RuleStatus
from tests.acceptance.test_candidates import _inputs
from tests.support.catalog import production_catalog


def _accepted() -> tuple[
    TaxState,
    DiscoveryResult,
    FinancialState,
    GuardrailResult,
    ActivatedOpportunityCatalog,
    AllocationPolicy,
]:
    tax, discovery, financial, guardrails, _ = _inputs()
    catalog = production_catalog()
    raw = bundled_allocation_policy(tax, discovery, catalog)
    return tax, discovery, financial, guardrails, catalog, raw


@pytest.mark.negative
def test_r1_a_raw_policy_is_never_a_production_engine_input() -> None:
    tax, discovery, financial, guards, _, raw = _accepted()
    with pytest.raises(ValueError, match="activated allocation policy"):
        build_candidates(tax, discovery, financial, guards, raw)  # type: ignore[arg-type]


@pytest.mark.negative
def test_r1_b_percentage_deduction_is_not_supported() -> None:
    _, _, _, _, _, raw = _accepted()
    with pytest.raises(ValueError, match="FULL_ALLOCATION_DEDUCTION"):
        replace(
            raw,
            treatments=(
                OpportunityTreatment(
                    opportunity_ids.THAI_ESG, DeductionSemantics.PERCENTAGE_OF_ALLOCATION
                ),
            ),
        )


@pytest.mark.negative
def test_r1_c_catalog_hash_mismatch_fails_activation() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    with pytest.raises(ValueError, match="catalog hash"):
        activate_allocation_policy(replace(raw, catalog_hash="wrong"), tax, discovery, catalog)


@pytest.mark.negative
def test_r1_d_unknown_treatment_fails_activation() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    treatment = OpportunityTreatment("TEST-UNKNOWN", DeductionSemantics.FULL_ALLOCATION_DEDUCTION)
    with pytest.raises(ValueError, match="unknown opportunity"):
        activate_allocation_policy(
            replace(raw, treatments=(*raw.treatments, treatment)), tax, discovery, catalog
        )


@pytest.mark.negative
def test_r1_e_extraneous_shared_group_fails_activation() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    with pytest.raises(ValueError, match="unknown shared group"):
        activate_allocation_policy(
            replace(
                raw,
                shared_limits=(*raw.shared_limits, SharedLimit("TEST-UNKNOWN", Money.of(100000))),
            ),
            tax,
            discovery,
            catalog,
        )


@pytest.mark.negative
def test_r1_f_self_consistently_hashed_upstream_tax_semantic_mismatch_fails() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    items = tuple(
        replace(item, maximum_tax_saving_at_capacity=Money.zero())
        if item.opportunity_id == opportunity_ids.THAI_ESG
        else item
        for item in discovery.opportunities
    )
    discovery = replace(discovery, opportunities=items)
    discovery = replace(
        discovery, discovery_hash=sha256_hex(canonical_json(discovery.material_dict()))
    )
    with pytest.raises(ValueError, match="P1-002 tax semantics"):
        activate_allocation_policy(raw, tax, discovery, catalog)


@pytest.mark.golden
def test_r1_g_activated_full_deduction_preserves_golden_outcome_and_provenance() -> None:
    tax, discovery, financial, guards, catalog, raw = _accepted()
    active = activate_allocation_policy(raw, tax, discovery, catalog)
    result = build_candidates(tax, discovery, financial, guards, active)
    baseline, allocated = result.candidates
    assert baseline.tax_before == baseline.tax_after == Money.of(79000)
    assert allocated.tax_saved == Money.of(18500)
    assert allocated.deductible_amount == allocated.total_allocation == Money.of(100000)
    assert active.rule_ids == (opportunity_ids.THAI_ESG_RULE,)
    assert active.source_ids == ("SEC-THAI-ESG-2026",)
    assert active.catalog_hash == discovery.opportunity_catalog_hash
    assert allocated.policy_hash == active.content_hash


@pytest.mark.negative
def test_r1_h_synthetic_policy_cannot_masquerade_as_production() -> None:
    tax, discovery, financial, guards, catalog, raw = _accepted()
    synthetic = replace(raw, policy_id="TEST-SYNTHETIC/1")
    with pytest.raises(ValueError, match="policy identity"):
        activate_allocation_policy(synthetic, tax, discovery, catalog)
    with pytest.raises(ValueError, match="activated allocation policy"):
        build_candidates(tax, discovery, financial, guards, synthetic)  # type: ignore[arg-type]


@pytest.mark.negative
@pytest.mark.parametrize(
    ("year", "status", "version"),
    [
        (2025, RuleStatus.EFFECTIVE, "1.0.0"),
        (2026, RuleStatus.DRAFT, "1.0.0"),
        (2026, RuleStatus.EFFECTIVE, "2.0.0"),
    ],
)
def test_r1_policy_year_status_version_fail_closed(
    year: int, status: RuleStatus, version: str
) -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    with pytest.raises(ValueError, match=r"policy identity|effective"):
        activate_allocation_policy(
            replace(raw, tax_year=year, status=status, version=version), tax, discovery, catalog
        )


@pytest.mark.negative
def test_r1_wrong_group_or_remaining_fails_activation() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    with pytest.raises(ValueError, match="shared group"):
        activate_allocation_policy(replace(raw, shared_limits=()), tax, discovery, catalog)
    with pytest.raises(ValueError, match="shared remaining"):
        activate_allocation_policy(
            replace(
                raw,
                shared_limits=(SharedLimit(opportunity_ids.THAI_ESG_2026_POOL, Money.of(200000)),),
            ),
            tax,
            discovery,
            catalog,
        )


@pytest.mark.negative
def test_r1_missing_allocatable_treatment_fails_activation() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    with pytest.raises(ValueError, match="omits treatment"):
        activate_allocation_policy(replace(raw, treatments=()), tax, discovery, catalog)


@pytest.mark.replay
def test_r1_i_activated_replay_is_exact() -> None:
    tax, discovery, financial, guards, catalog, raw = _accepted()
    active = activate_allocation_policy(raw, tax, discovery, catalog)
    result = build_candidates(tax, discovery, financial, guards, active)
    snapshot = create_candidate_snapshot(result)
    assert replay_candidates(snapshot, tax, discovery, financial, guards, active) == result


@pytest.mark.negative
@pytest.mark.parametrize(
    "variant",
    [
        "catalog",
        "discovery_catalog",
        "tax",
        "tax_binding",
        "duplicate",
        "unknown",
        "provenance",
        "draft",
        "missing_capacity",
    ],
)
def test_r1_activation_refuses_forged_upstream_material(variant: str) -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    if variant == "catalog":
        catalog = replace(catalog, content_hash="forged")
    elif variant == "discovery_catalog":
        discovery = replace(discovery, opportunity_catalog_hash="forged")
    elif variant == "tax":
        tax = replace(tax, output_hash="forged")
    elif variant == "tax_binding":
        discovery = replace(discovery, tax_state_hash="forged")
    elif variant == "duplicate":
        discovery = replace(
            discovery, opportunities=(*discovery.opportunities, discovery.opportunities[0])
        )
    elif variant == "unknown":
        discovery = replace(
            discovery,
            opportunities=(
                *discovery.opportunities,
                replace(discovery.opportunities[0], opportunity_id="TEST-UNKNOWN"),
            ),
        )
    else:
        opportunities = tuple(
            replace(item, rule_ids=("TEST-UNKNOWN",))
            if variant == "provenance"
            else replace(item, status=OpportunityStatus.AVAILABLE)
            if variant == "draft"
            else replace(item, remaining_capacity=None)
            if variant == "missing_capacity"
            else item
            for item in discovery.opportunities
            if item.opportunity_id
            == (opportunity_ids.ARTWORK if variant == "draft" else opportunity_ids.THAI_ESG)
        )
        original = {item.opportunity_id: item for item in opportunities}
        discovery = replace(
            discovery,
            opportunities=tuple(
                original.get(item.opportunity_id, item) for item in discovery.opportunities
            ),
        )
    if variant in {
        "discovery_catalog",
        "tax_binding",
        "duplicate",
        "unknown",
        "provenance",
        "draft",
        "missing_capacity",
    }:
        discovery = replace(
            discovery, discovery_hash=sha256_hex(canonical_json(discovery.material_dict()))
        )
    with pytest.raises(
        ValueError, match=r"catalog|integrity|inputs|duplicate|unknown|provenance|ready|incomplete"
    ):
        activate_allocation_policy(raw, tax, discovery, catalog)


@pytest.mark.negative
def test_r1_activated_policy_rejects_self_consistent_but_unaccepted_maximum() -> None:
    tax, discovery, _, _, catalog, raw = _accepted()
    with pytest.raises(ValueError, match="accepted production contract"):
        activate_allocation_policy(replace(raw, max_candidates=31), tax, discovery, catalog)


@pytest.mark.negative
def test_r1_forged_activated_wrapper_fails_at_publication() -> None:
    tax, discovery, financial, guards, catalog, raw = _accepted()
    active = activate_allocation_policy(raw, tax, discovery, catalog)
    with pytest.raises(ValueError, match="activated allocation policy integrity"):
        build_candidates(tax, discovery, financial, guards, replace(active, content_hash="forged"))


@pytest.mark.negative
def test_r1_only_one_accepted_opportunity_per_shared_group() -> None:
    with pytest.raises(ValueError, match="multi-opportunity shared group"):
        _shared_groups((("ONE", "GROUP", Money.of(100)), ("TWO", "GROUP", Money.of(100))))
    assert _shared_groups((("ONE", None, Money.of(100)),)) == ()
