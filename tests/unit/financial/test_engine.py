"""Unit tests for the guardrail engine's precedence-order validation (TGPS-P1-003 §43)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.discovery.models import DiscoveryStatus
from tax_gps.engine import calculate_tax
from tax_gps.financial.engine import evaluate_guardrails
from tax_gps.financial.models import GuardrailDecision, GuardrailResultStatus
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    activate_financial_policy,
    bundled_financial_policy,
)
from tax_gps.financial.profile import FinancialPlanningContext, FinancialProfile
from tax_gps.financial.state import compute_financial_state
from tax_gps.profile.models import (
    IncomeProfile,
    UnsupportedIncome,
)
from tests.acceptance.test_guardrails import _discovery, _tax_profile
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack

PLANNING_DATE = date(2026, 6, 1)


def _policy() -> ActivatedFinancialPolicy:
    return activate_financial_policy(bundled_financial_policy(TaxYear(2026)))


def test_mismatched_planning_date_is_rejected() -> None:
    discovery = _discovery(_tax_profile(500000))
    profile = FinancialProfile(
        liquid_assets=Money.of(500000), monthly_essential_expenses=Money.of(50000)
    )
    policy = _policy()
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    state = compute_financial_state(profile, policy, context)
    other_context = replace(context, planning_date=date(2026, 7, 1))
    with pytest.raises(ValueError, match="planning context"):
        evaluate_guardrails(discovery, state, policy, other_context)


def test_mismatched_financial_policy_is_rejected() -> None:
    discovery = _discovery(_tax_profile(500000))
    profile = FinancialProfile(
        liquid_assets=Money.of(500000), monthly_essential_expenses=Money.of(50000)
    )
    policy = _policy()
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    state = compute_financial_state(profile, policy, context)
    stale_state = replace(state, policy_hash="deadbeef")
    with pytest.raises(ValueError, match="activated financial policy"):
        evaluate_guardrails(discovery, stale_state, policy, context)


def test_unsupported_discovery_yields_unsupported_guardrail_result() -> None:
    user = replace(
        _tax_profile(300000),
        income=IncomeProfile(
            section_40_1=Money.of(300000), unsupported=(UnsupportedIncome("40(8)", Money.of(1)),)
        ),
    )
    state = calculate_tax(user, production_pack())
    discovery = discover_opportunities(
        user,
        state,
        production_pack(),
        production_catalog(),
        DiscoveryContext(user.tax_year, PLANNING_DATE),
    )
    assert discovery.status is DiscoveryStatus.UNSUPPORTED
    profile = FinancialProfile(liquid_assets=Money.of(0), monthly_essential_expenses=Money.of(0))
    policy = _policy()
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    fin_state = compute_financial_state(profile, policy, context)
    result = evaluate_guardrails(discovery, fin_state, policy, context)
    assert result.status is GuardrailResultStatus.UNSUPPORTED


def test_ready_discovery_with_partial_financial_state_yields_partial_result() -> None:
    discovery = _discovery(_tax_profile(800000))
    profile = FinancialProfile(liquid_assets=Money.of(500000), monthly_essential_expenses=None)
    policy = _policy()
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    fin_state = compute_financial_state(profile, policy, context)
    result = evaluate_guardrails(discovery, fin_state, policy, context)
    assert result.status is GuardrailResultStatus.PARTIAL


def test_existing_right_still_allows_even_when_discovery_is_unsupported() -> None:
    """Existing rights bypass the upstream-availability gate entirely (§30): even under a

    defensively-constructed UNSUPPORTED discovery result carrying a stale existing right,
    the right is ALLOW, never demoted to NOT_APPLICABLE alongside the new-cash opportunities.
    Production discovery never emits existing_rights under UNSUPPORTED (see
    discovery/engine.py's UNSUPPORTED branch, which always sets existing_rights=()); this test
    exercises the guardrail engine's own contract in isolation regardless of that upstream
    guarantee.
    """
    ready_discovery = _discovery(_tax_profile(800000))
    assert ready_discovery.existing_rights, "fixture must carry at least one existing right"
    unsupported_discovery = replace(ready_discovery, status=DiscoveryStatus.UNSUPPORTED)
    profile = FinancialProfile(
        liquid_assets=Money.of(500000), monthly_essential_expenses=Money.of(50000)
    )
    policy = _policy()
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    fin_state = compute_financial_state(profile, policy, context)
    result = evaluate_guardrails(unsupported_discovery, fin_state, policy, context)
    assert result.status is GuardrailResultStatus.UNSUPPORTED
    right_ids = {right.right_id for right in unsupported_discovery.existing_rights}
    right_assessments = [a for a in result.assessments if a.opportunity_id in right_ids]
    assert right_assessments
    assert all(a.decision is GuardrailDecision.ALLOW for a in right_assessments)
    opportunity_ids = {item.opportunity_id for item in unsupported_discovery.opportunities}
    opportunity_assessments = [a for a in result.assessments if a.opportunity_id in opportunity_ids]
    assert opportunity_assessments
    assert all(a.decision is GuardrailDecision.NOT_APPLICABLE for a in opportunity_assessments)
