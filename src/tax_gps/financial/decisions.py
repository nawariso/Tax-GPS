"""Isolated DMN-aligned guardrail decision boundaries (TGPS-P1-003 §28-38, §43).

Each function is a single explicit decision boundary so the guardrail precedence can be
unit-tested in isolation, mirroring ``tax_gps.discovery`` decision modules.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from tax_gps.core.money import Money
from tax_gps.financial.models import GuardrailAssessment, GuardrailDecision
from tax_gps.financial.reason_codes import FinancialReasonCode
from tax_gps.financial.state import FinancialState, FinancialStateStatus
from tax_gps.opportunity.models import OpportunityCategory

_INTRINSIC_CATEGORIES = frozenset(
    {OpportunityCategory.UTILITY_INVESTMENT, OpportunityCategory.LIFESTYLE_INTENT}
)


def not_applicable(opportunity_id: str) -> GuardrailAssessment:
    return GuardrailAssessment(
        opportunity_id=opportunity_id,
        decision=GuardrailDecision.NOT_APPLICABLE,
        max_feasible_allocation=None,
        reason_codes=(FinancialReasonCode.UPSTREAM_NOT_AVAILABLE,),
    )


def missing_capacity(opportunity_id: str) -> GuardrailAssessment:
    """Fail-closed: an AVAILABLE opportunity carrying no known tax capacity (§4, §31, R1-04).

    Unknown legal/tax capacity must never become permission to allocate cash: a producer
    bug or an inconsistently constructed ``DiscoveredOpportunity`` (AVAILABLE with
    ``remaining_capacity=None``) must not fall through to ``available_budget`` as a
    substitute ceiling.
    """
    return GuardrailAssessment(
        opportunity_id=opportunity_id,
        decision=GuardrailDecision.NOT_APPLICABLE,
        max_feasible_allocation=None,
        reason_codes=(FinancialReasonCode.DISCOVERY_CAPACITY_MISSING,),
    )


def existing_right_passthrough(opportunity_id: str) -> GuardrailAssessment:
    """Decision: existing rights require no new spending and are never blocked (§30)."""
    return GuardrailAssessment(
        opportunity_id=opportunity_id,
        decision=GuardrailDecision.ALLOW,
        max_feasible_allocation=None,
        reason_codes=(FinancialReasonCode.EXISTING_RIGHT_PASSTHROUGH,),
    )


def financial_input_required(opportunity_id: str) -> GuardrailAssessment:
    """Decision 3: missing financial inputs must never yield ALLOW for new cash (§41, GR-10)."""
    return GuardrailAssessment(
        opportunity_id=opportunity_id,
        decision=GuardrailDecision.REQUIRE_REVIEW,
        max_feasible_allocation=None,
        reason_codes=(FinancialReasonCode.FINANCIAL_INPUT_REQUIRED,),
    )


def is_intrinsic_purpose(category: OpportunityCategory) -> bool:
    return category in _INTRINSIC_CATEGORIES


@dataclass(frozen=True, slots=True)
class NewCashInputs:
    opportunity_id: str
    category: OpportunityCategory
    remaining_capacity: Money
    available_budget: Money
    state: FinancialState


def critical_debt_decision(inputs: NewCashInputs) -> GuardrailAssessment | None:
    """Decision 4 (§32-33): critical high-cost debt blocks tax-motivated new cash."""
    if inputs.state.critical_debt_balance.is_zero():
        return None
    if is_intrinsic_purpose(inputs.category):
        return GuardrailAssessment(
            opportunity_id=inputs.opportunity_id,
            decision=GuardrailDecision.REQUIRE_REVIEW,
            max_feasible_allocation=None,
            reason_codes=(FinancialReasonCode.CRITICAL_DEBT_PRESENT,),
        )
    return GuardrailAssessment(
        opportunity_id=inputs.opportunity_id,
        decision=GuardrailDecision.BLOCK,
        max_feasible_allocation=Money.zero(),
        reason_codes=(FinancialReasonCode.CRITICAL_DEBT_PRESENT,),
    )


def emergency_floor_decision(inputs: NewCashInputs) -> GuardrailAssessment | None:
    """Decision 5 (§34-35): liquid assets below the emergency reserve floor.

    Defensive: normally unreachable via ``assess_new_cash_opportunity`` because a PARTIAL
    state (liquid_assets or emergency_reserve_floor unknown) is routed to
    ``financial_input_required`` before this decision runs. This function is exported and
    independently callable, so it fails closed rather than trusting that invariant (tested
    directly in test_decisions.py).
    """
    state = inputs.state
    if state.liquid_assets is None or state.emergency_reserve_floor is None:
        return None
    if state.liquid_assets >= state.emergency_reserve_floor:
        return None
    if is_intrinsic_purpose(inputs.category):
        return GuardrailAssessment(
            opportunity_id=inputs.opportunity_id,
            decision=GuardrailDecision.REQUIRE_REVIEW,
            max_feasible_allocation=None,
            reason_codes=(FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR,),
        )
    return GuardrailAssessment(
        opportunity_id=inputs.opportunity_id,
        decision=GuardrailDecision.BLOCK,
        max_feasible_allocation=Money.zero(),
        reason_codes=(FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR,),
    )


def liquidity_ceiling_decision(inputs: NewCashInputs) -> GuardrailAssessment:
    """Decisions 7 (§36-38): no-surplus, capped, or healthy allocation ceiling.

    Defensive: ``surplus is None`` is normally unreachable via ``assess_new_cash_opportunity``
    (PARTIAL states are routed to ``financial_input_required`` first); this function is
    exported and independently callable, so an unknown surplus fails closed to zero rather
    than trusting that invariant (tested directly in test_decisions.py).
    """
    surplus = inputs.state.spendable_surplus
    if surplus is None:
        surplus = Money.zero()
    ceiling = Money.min(inputs.remaining_capacity, inputs.available_budget)
    if surplus.is_zero():
        if is_intrinsic_purpose(inputs.category):
            return GuardrailAssessment(
                opportunity_id=inputs.opportunity_id,
                decision=GuardrailDecision.REQUIRE_REVIEW,
                max_feasible_allocation=None,
                reason_codes=(FinancialReasonCode.NO_SPENDABLE_SURPLUS,),
            )
        return GuardrailAssessment(
            opportunity_id=inputs.opportunity_id,
            decision=GuardrailDecision.BLOCK,
            max_feasible_allocation=Money.zero(),
            reason_codes=(FinancialReasonCode.NO_SPENDABLE_SURPLUS,),
        )
    if surplus < ceiling:
        return GuardrailAssessment(
            opportunity_id=inputs.opportunity_id,
            decision=GuardrailDecision.CAP,
            max_feasible_allocation=surplus,
            reason_codes=(FinancialReasonCode.ALLOCATION_CAPPED_BY_LIQUIDITY,),
        )
    return GuardrailAssessment(
        opportunity_id=inputs.opportunity_id,
        decision=GuardrailDecision.ALLOW,
        max_feasible_allocation=Money.min(ceiling, surplus),
        reason_codes=(),
    )


def with_protection_reason(
    assessment: GuardrailAssessment, state: FinancialState
) -> GuardrailAssessment:
    """Decision 8 (§39-40, §12 in matrix): protection is informational only, never blocking."""
    reason: FinancialReasonCode | None = None
    if state.protection_gap is not None and state.protection_gap.is_positive():
        reason = FinancialReasonCode.PROTECTION_GAP
    elif state.protection_gap is None and FinancialReasonCode.PROTECTION_NEED_UNKNOWN in (
        state.reason_codes
    ):
        reason = FinancialReasonCode.PROTECTION_NEED_UNKNOWN
    if reason is None or reason in assessment.reason_codes:
        return assessment
    return replace(assessment, reason_codes=(*assessment.reason_codes, reason))


def assess_new_cash_opportunity(inputs: NewCashInputs) -> GuardrailAssessment:
    """Full precedence chain for one AVAILABLE new-cash opportunity (§43 steps 4-9)."""
    if inputs.state.status is FinancialStateStatus.PARTIAL:
        return financial_input_required(inputs.opportunity_id)
    decision = critical_debt_decision(inputs) or emergency_floor_decision(inputs)
    if decision is None:
        decision = liquidity_ceiling_decision(inputs)
    return with_protection_reason(decision, inputs.state)
