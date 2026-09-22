"""Guardrail Engine: evaluates a DiscoveryResult against FinancialState (TGPS-P1-003 §43).

Precedence (must match exactly, see docs/requirements/TGPS-P1-003.md §43):

1. Upstream discovery availability
2. Financial policy readiness
3. Required financial input completeness
4. Critical high-cost debt
5. Emergency-fund floor
6. Mandatory liquidity commitments (folded into the liquidity ceiling, step 7)
7. Allocation ceiling / CAP
8. Protection informational warnings
9. ALLOW
"""

from __future__ import annotations

from dataclasses import replace

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.discovery.models import DiscoveryResult, DiscoveryStatus
from tax_gps.financial.decisions import (
    NewCashInputs,
    assess_new_cash_opportunity,
    existing_right_passthrough,
    missing_capacity,
    not_applicable,
)
from tax_gps.financial.models import (
    GuardrailAssessment,
    GuardrailResult,
    GuardrailResultStatus,
)
from tax_gps.financial.policy import ActivatedFinancialPolicy
from tax_gps.financial.profile import FinancialPlanningContext
from tax_gps.financial.state import FinancialState
from tax_gps.opportunity.models import OpportunityStatus

GUARDRAIL_ENGINE_VERSION = "tax-gps-guardrails/0.1.0"


def _assess_new_cash(
    discovery: DiscoveryResult,
    state: FinancialState,
    context: FinancialPlanningContext,
) -> tuple[GuardrailAssessment, ...]:
    assessments: list[GuardrailAssessment] = []
    for item in discovery.opportunities:
        if item.status is not OpportunityStatus.AVAILABLE:
            # Fail-closed allowlist: only an explicitly AVAILABLE opportunity may reach the
            # new-cash guardrail chain. Any other status (including one added to
            # OpportunityStatus in the future) is NOT_APPLICABLE by default, never promoted.
            assessments.append(not_applicable(item.opportunity_id))
            continue
        remaining_capacity = item.remaining_capacity
        if remaining_capacity is None:
            # Fail-closed: an AVAILABLE opportunity must carry known tax capacity. Unknown
            # upstream capacity must never be silently treated as the available budget (§4,
            # §31, R1-04) -- that would let unbounded new cash pass through as "capped" by
            # a figure that was never actually validated as a tax-capacity ceiling.
            assessments.append(missing_capacity(item.opportunity_id))
            continue
        assessments.append(
            assess_new_cash_opportunity(
                NewCashInputs(
                    opportunity_id=item.opportunity_id,
                    category=item.category,
                    remaining_capacity=remaining_capacity,
                    available_budget=context.available_budget,
                    state=state,
                )
            )
        )
    return tuple(assessments)


def evaluate_guardrails(
    discovery: DiscoveryResult,
    state: FinancialState,
    activated_policy: ActivatedFinancialPolicy,
    context: FinancialPlanningContext,
    *,
    engine_version: str = GUARDRAIL_ENGINE_VERSION,
) -> GuardrailResult:
    """Evaluate every discovered opportunity, preserving Discovery ordering (§48)."""
    if state.planning_date != context.planning_date:
        raise ValueError("financial state does not match planning context")
    if state.policy_id != activated_policy.policy_id or (
        state.policy_hash != activated_policy.content_hash
    ):
        raise ValueError("financial state does not match activated financial policy")

    right_assessments = tuple(
        existing_right_passthrough(item.right_id) for item in discovery.existing_rights
    )
    new_cash_assessments = (
        _assess_new_cash(discovery, state, context)
        if discovery.status is DiscoveryStatus.READY
        else tuple(not_applicable(item.opportunity_id) for item in discovery.opportunities)
    )
    assessments = right_assessments + new_cash_assessments

    if discovery.status is not DiscoveryStatus.READY:
        status = GuardrailResultStatus.UNSUPPORTED
    elif state.status.value == "PARTIAL":
        status = GuardrailResultStatus.PARTIAL
    else:
        status = GuardrailResultStatus.READY

    result = GuardrailResult(
        status=status,
        profile_hash=discovery.profile_hash,
        discovery_hash=discovery.discovery_hash,
        financial_state_hash=state.state_hash,
        financial_policy_hash=activated_policy.content_hash,
        planning_date=context.planning_date,
        available_budget=context.available_budget,
        assessments=assessments,
        policy_version=activated_policy.version,
        engine_version=engine_version,
        guardrail_hash="",
    )
    return _with_hash(result)


def _with_hash(result: GuardrailResult) -> GuardrailResult:
    return replace(result, guardrail_hash=sha256_hex(canonical_json(result.material_dict())))
