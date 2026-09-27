"""Fail-closed bounded candidate construction using existing tax and financial outcomes."""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum
from typing import cast

from tax_gps.calculation.models import TaxState, TaxStatus
from tax_gps.candidate.models import (
    Allocation,
    AllocationPolicy,
    CandidateOutcome,
    CandidateResult,
    DeductionSemantics,
    OpportunityTreatment,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.discovery.models import DiscoveredOpportunity, DiscoveryResult, DiscoveryStatus
from tax_gps.financial.models import GuardrailDecision, GuardrailResult, GuardrailResultStatus
from tax_gps.financial.state import (
    FinancialState,
    FinancialStateStatus,
    verify_financial_state_integrity,
)
from tax_gps.opportunity.models import OpportunityStatus, OpportunityType

CANDIDATE_ENGINE_VERSION = "tax-gps-candidates/0.1.0"
MAX_ALLOCATABLE_OPPORTUNITIES = 8


class CandidateReasonCode(StrEnum):
    NO_ACTION_BASELINE = "NO_ACTION_BASELINE"
    BUDGET_BOUND = "BUDGET_BOUND"
    GUARDRAIL_CAP_APPLIED = "GUARDRAIL_CAP_APPLIED"
    SHARED_LIMIT_APPLIED = "SHARED_LIMIT_APPLIED"
    FULL_ALLOCATION_DEDUCTION = "FULL_ALLOCATION_DEDUCTION"
    PARTIAL_FINANCIAL_STATE = "PARTIAL_FINANCIAL_STATE"


def _verify_inputs(
    tax: TaxState,
    discovery: DiscoveryResult,
    financial: FinancialState,
    guardrails: GuardrailResult,
    policy: AllocationPolicy,
) -> None:
    verify_financial_state_integrity(financial)
    if tax.output_hash != sha256_hex(canonical_json(tax.material_dict())) or (
        tax._activated_pack.content_hash != discovery.rule_pack_hash
        or tax.rule_pack != tax._activated_pack.rule_pack_id
        or tax.rule_pack_version != tax._activated_pack.version
    ):
        raise ValueError("tax state or policy integrity mismatch")
    if discovery.discovery_hash != sha256_hex(canonical_json(discovery.material_dict())):
        raise ValueError("discovery integrity mismatch")
    if guardrails.guardrail_hash != sha256_hex(canonical_json(guardrails.material_dict())):
        raise ValueError("guardrail integrity mismatch")
    if (
        tax.status is not TaxStatus.READY
        or discovery.status is not DiscoveryStatus.READY
        or tax.taxable_income is None
        or tax.pit is None
        or discovery.tax_state_hash != tax.output_hash
        or discovery.tax_year != tax.tax_year.gregorian
        or discovery.opportunity_catalog_hash != policy.catalog_hash
        or guardrails.discovery_hash != discovery.discovery_hash
        or guardrails.profile_hash != discovery.profile_hash
        or guardrails.financial_state_hash != financial.state_hash
        or guardrails.financial_policy_hash != financial.policy_hash
        or guardrails.planning_date != financial.planning_date
        or guardrails.available_budget.is_negative()
        or (
            financial.liquid_assets is not None
            and guardrails.available_budget > financial.liquid_assets
        )
        or (
            financial.status is FinancialStateStatus.PARTIAL
            and guardrails.status is not GuardrailResultStatus.PARTIAL
        )
        or (
            financial.status is FinancialStateStatus.READY
            and guardrails.status is not GuardrailResultStatus.READY
        )
    ):
        raise ValueError("candidate input identities or readiness mismatch")
    ids = [item.right_id for item in discovery.existing_rights] + [
        item.opportunity_id for item in discovery.opportunities
    ]
    assessed = [item.opportunity_id for item in guardrails.assessments]
    if len(set(ids)) != len(ids) or sorted(ids) != sorted(assessed):
        raise ValueError("discovery and guardrail assessments must match uniquely")
    for item in discovery.opportunities:
        assessment = next(
            a for a in guardrails.assessments if a.opportunity_id == item.opportunity_id
        )
        if assessment.decision in (GuardrailDecision.ALLOW, GuardrailDecision.CAP) and (
            item.status is not OpportunityStatus.AVAILABLE
            or item.opportunity_type is not OpportunityType.NEW_CASH
            or not item.requires_new_cash
            or item.remaining_capacity is None
            or assessment.max_feasible_allocation is None
            or assessment.max_feasible_allocation.is_negative()
            or assessment.max_feasible_allocation > item.remaining_capacity
            or assessment.max_feasible_allocation > guardrails.available_budget
            or financial.spendable_surplus is None
            or assessment.max_feasible_allocation > financial.spendable_surplus
        ):
            raise ValueError("invalid allocatable guardrail ceiling")


def _allocatable(
    discovery: DiscoveryResult, guardrails: GuardrailResult, policy: AllocationPolicy
) -> tuple[tuple[DiscoveredOpportunity, OpportunityTreatment, Money], ...]:
    treatments = {item.opportunity_id: item for item in policy.treatments}
    groups = {item.group_id: item.remaining for item in policy.shared_limits}
    available: list[tuple[DiscoveredOpportunity, OpportunityTreatment, Money]] = []
    for item in sorted(discovery.opportunities, key=lambda i: i.opportunity_id):
        assessment = next(
            a for a in guardrails.assessments if a.opportunity_id == item.opportunity_id
        )
        if assessment.decision not in (GuardrailDecision.ALLOW, GuardrailDecision.CAP):
            continue
        treatment = treatments.get(item.opportunity_id)
        if treatment is None:
            raise ValueError("allocatable opportunity has no explicit deduction treatment")
        if item.shared_limit_group is not None and item.shared_limit_group not in groups:
            raise ValueError("shared opportunity has no governed common remaining limit")
        ceiling = assessment.max_feasible_allocation
        if ceiling is None:  # pragma: no cover - checked by _verify_inputs
            raise ValueError("unreachable: allocatable ceiling absent")
        if ceiling.is_positive():
            available.append((item, treatment, ceiling))
    return tuple(available)


def _outcome(
    allocations: tuple[Allocation, ...],
    *,
    treatments: dict[str, OpportunityTreatment],
    groups: dict[str, Money],
    opportunities: dict[str, DiscoveredOpportunity],
    tax: TaxState,
    financial: FinancialState,
    guardrails: GuardrailResult,
    input_hash: str,
    policy_hash: str,
    engine_version: str,
) -> CandidateOutcome:
    total = Money.sum(allocation.amount for allocation in allocations)
    deductible = Money.zero()
    reasons: list[str] = []
    if not allocations:
        reasons.append(CandidateReasonCode.NO_ACTION_BASELINE)
    for allocation in allocations:
        treatment = treatments[allocation.opportunity_id]
        if treatment.semantics is DeductionSemantics.FULL_ALLOCATION_DEDUCTION:
            deductible += allocation.amount
            reasons.append(CandidateReasonCode.FULL_ALLOCATION_DEDUCTION)
        else:
            rate = treatment.rate
            if rate is None:  # pragma: no cover - enforced in OpportunityTreatment
                raise ValueError("unreachable: missing governed deduction rate")
            deductible += allocation.amount * rate
        item = opportunities[allocation.opportunity_id]
        assessment = next(
            a for a in guardrails.assessments if a.opportunity_id == allocation.opportunity_id
        )
        if assessment.decision is GuardrailDecision.CAP:
            reasons.append(CandidateReasonCode.GUARDRAIL_CAP_APPLIED)
        if item.shared_limit_group is not None and (
            Money.sum(
                a.amount
                for a in allocations
                if opportunities[a.opportunity_id].shared_limit_group == item.shared_limit_group
            )
            >= groups[item.shared_limit_group]
        ):
            reasons.append(CandidateReasonCode.SHARED_LIMIT_APPLIED)
    if total == guardrails.available_budget and total.is_positive():
        reasons.append(CandidateReasonCode.BUDGET_BOUND)
    if financial.status is FinancialStateStatus.PARTIAL:
        reasons.append(CandidateReasonCode.PARTIAL_FINANCIAL_STATE)
    impact = tax.tax_impact(deductible)
    if tax.pit != impact.pit_before:
        raise ValueError("tax baseline differs from progressive tax core")
    return CandidateOutcome(
        candidate_id=sha256_hex(
            canonical_json({"allocations": [a.to_dict() for a in allocations]})
        ),
        allocations=allocations,
        total_allocation=total,
        deductible_amount=deductible,
        tax_before=impact.pit_before,
        tax_after=impact.pit_after,
        tax_saved=impact.saving,
        cash_outflow=total,
        unused_budget=guardrails.available_budget - total,
        spendable_surplus_after=(
            financial.spendable_surplus - total if financial.spendable_surplus is not None else None
        ),
        protection_gap=financial.protection_gap,
        reason_codes=tuple(dict.fromkeys(reasons)),
        input_hash=input_hash,
        policy_hash=policy_hash,
        tax_rule_pack_hash=tax._activated_pack.content_hash,
        guardrail_hash=guardrails.guardrail_hash,
        engine_version=engine_version,
    )


def build_candidates(
    tax: TaxState,
    discovery: DiscoveryResult,
    financial: FinancialState,
    guardrails: GuardrailResult,
    policy: AllocationPolicy,
    *,
    engine_version: str = CANDIDATE_ENGINE_VERSION,
) -> CandidateResult:
    """Enumerate zero and governed boundary amounts; fail rather than truncate on overflow."""
    _verify_inputs(tax, discovery, financial, guardrails, policy)
    available = _allocatable(discovery, guardrails, policy)
    if len(available) > MAX_ALLOCATABLE_OPPORTUNITIES:
        raise ValueError("allocatable opportunity maximum exceeded; no expansion")
    groups = {item.group_id: item.remaining for item in policy.shared_limits}
    treatments = {item.opportunity_id: item for item in policy.treatments}
    opportunities = {item.opportunity_id: item for item in discovery.opportunities}
    input_hash = sha256_hex(
        canonical_json(
            {
                "tax": tax.output_hash,
                "discovery": discovery.discovery_hash,
                "financial": financial.state_hash,
                "guardrails": guardrails.guardrail_hash,
                "budget": guardrails.available_budget.canonical(),
            }
        )
    )
    policy_hash = policy.content_hash()
    # A key is an allocation composition, not a path through construction.
    compositions: dict[bytes, tuple[Allocation, ...]] = {}

    def walk(
        index: int, current: tuple[Allocation, ...], total: Money, used: dict[str, Money]
    ) -> None:
        if index == len(available):
            key = canonical_json({"allocations": [a.to_dict() for a in current]})
            compositions[key] = current
            if len(compositions) > policy.max_candidates:
                raise ValueError("candidate policy maximum exceeded; no partial output")
            return
        item, _, ceiling = available[index]
        remaining = Money.min(
            guardrails.available_budget - total,
            cast(Money, financial.spendable_surplus) - total,
        )
        if item.shared_limit_group is not None:
            remaining = Money.min(
                remaining,
                groups[item.shared_limit_group] - used.get(item.shared_limit_group, Money.zero()),
            )
        high = Money.min(ceiling, remaining)
        # No invented increments: only zero and the intersection of policy, budget,
        # financial, and shared-limit boundaries at this point in canonical ID order.
        walk(index + 1, current, total, used)
        # Positive boundaries also include the residual needed to fund a later
        # opportunity at its own governed ceiling. No arbitrary increments.
        choices = {high}
        for future, _, future_ceiling in available[index + 1 :]:
            future_bound = future_ceiling
            if future.shared_limit_group is not None:
                future_bound = Money.min(
                    future_bound,
                    groups[future.shared_limit_group]
                    - used.get(future.shared_limit_group, Money.zero()),
                )
            residual = remaining - future_bound
            if residual.is_positive() and residual < high:
                choices.add(residual)
        for amount in sorted(choices):
            if not amount.is_positive():
                continue
            next_used = dict(used)
            if item.shared_limit_group is not None:
                next_used[item.shared_limit_group] = (
                    next_used.get(item.shared_limit_group, Money.zero()) + amount
                )
            walk(
                index + 1,
                (*current, Allocation(item.opportunity_id, amount)),
                total + amount,
                next_used,
            )

    walk(0, (), Money.zero(), {})
    # Baseline first; then allocation identity, never financial desirability.
    ordered = sorted(compositions.items(), key=lambda pair: (bool(pair[1]), pair[0]))
    candidates = tuple(
        _outcome(
            composition,
            treatments=treatments,
            groups=groups,
            opportunities=opportunities,
            tax=tax,
            financial=financial,
            guardrails=guardrails,
            input_hash=input_hash,
            policy_hash=policy_hash,
            engine_version=engine_version,
        )
        for _, composition in ordered
    )
    result = CandidateResult(candidates, input_hash, policy_hash, engine_version, "")
    return replace(result, result_hash=sha256_hex(canonical_json(result.material_dict())))
