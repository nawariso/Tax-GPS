"""C04A: one user-chosen Thai ESG amount evaluated on top of the C03 annual estimate.

The service reuses existing authorities only: C03 readiness, the bundled opportunity
catalog capacity rule, the financial guardrail decision chain and the progressive PIT
saving function. It does not rank, recommend or choose an amount.
"""

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import cast

from tax_gps.calculation.annual_estimate import (
    AnnualEstimateInput,
    AnnualEstimateResult,
    SettlementKind,
    calculate_annual_estimate,
    settle,
)
from tax_gps.calculation.availability import PlanningAvailability
from tax_gps.calculation.models import TaxImpact, TaxState
from tax_gps.calculation.rules import calculate_tax_saving
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.discovery.capacity import OpportunityCapacity, calculate_opportunity_capacity
from tax_gps.financial.decisions import NewCashInputs, assess_new_cash_opportunity
from tax_gps.financial.models import GuardrailAssessment
from tax_gps.financial.policy import ActivatedFinancialPolicy
from tax_gps.financial.profile import FinancialPlanningContext, FinancialProfile
from tax_gps.financial.state import FinancialState, compute_financial_state
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog, activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.opportunity.models import EvidenceRequirement, LockupMetadata
from tax_gps.opportunity.opportunity_ids import THAI_ESG
from tax_gps.policy.activation import ActivatedRulePack

AMOUNT_FACT_ID = "thai_esg_what_if.amount"
EXCEEDS_TAX_CAPACITY_REASON = "THAI_ESG_AMOUNT_EXCEEDS_TAX_CAPACITY"
_OPEN_AVAILABILITY = (PlanningAvailability.AVAILABLE, PlanningAvailability.PVD_BASELINE_ONLY)


class ThaiEsgWhatIfInputError(InvalidValueError):
    def __init__(self, fact_id: str) -> None:
        self.fact_id = fact_id
        super().__init__(f"invalid Thai ESG what-if field: {fact_id}")


class WhatIfStatus(StrEnum):
    BASELINE_NOT_READY = "BASELINE_NOT_READY"
    UNSUPPORTED = "UNSUPPORTED"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    EXCEEDS_TAX_CAPACITY = "EXCEEDS_TAX_CAPACITY"
    GUARDRAIL_LIMITED = "GUARDRAIL_LIMITED"
    READY = "READY"


class CapacityBasis(StrEnum):
    """Which income base the 30% capacity used (D7)."""

    ASSESSABLE_INCOME = "ASSESSABLE_INCOME"
    CONSERVATIVE_AFTER_PVD_EXEMPTION = "CONSERVATIVE_AFTER_PVD_EXEMPTION"


@dataclass(frozen=True, slots=True)
class ThaiEsgWhatIfInput:
    amount: Money | None
    financial: FinancialProfile


@dataclass(frozen=True, slots=True)
class ThaiEsgWhatIfResult:
    estimate: AnnualEstimateResult
    status: WhatIfStatus
    reason_codes: tuple[str, ...]
    missing_fact_ids: tuple[str, ...]
    amount: Money | None = None
    capacity: OpportunityCapacity | None = None
    capacity_basis: CapacityBasis | None = None
    financial_state: FinancialState | None = None
    guardrail: GuardrailAssessment | None = None
    impact: TaxImpact | None = None
    settlement_after_kind: SettlementKind | None = None
    settlement_after_amount: Money | None = None
    lockup: LockupMetadata | None = None
    evidence_requirements: tuple[EvidenceRequirement, ...] = ()


def _require_bundled(catalog: ActivatedOpportunityCatalog) -> None:
    bundled = activate_catalog(load_bundled_catalog())
    if catalog.content_hash != bundled.content_hash or catalog != bundled:
        raise ValueError("Thai ESG what-if requires the accepted bundled catalog")


def _missing(inputs: ThaiEsgWhatIfInput) -> tuple[str, ...]:
    amount = inputs.amount
    if amount is not None and (amount.is_negative() or not amount.is_whole_satang()):
        raise ThaiEsgWhatIfInputError(AMOUNT_FACT_ID)
    financial = inputs.financial
    return tuple(
        fact_id
        for fact_id, value in (
            (AMOUNT_FACT_ID, amount),
            ("financial.liquid_assets", financial.liquid_assets),
            ("financial.monthly_essential_expenses", financial.monthly_essential_expenses),
        )
        if value is None
    )


def evaluate_thai_esg_what_if(
    estimate_input: AnnualEstimateInput,
    inputs: ThaiEsgWhatIfInput,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    financial_policy: ActivatedFinancialPolicy,
) -> ThaiEsgWhatIfResult:
    _require_bundled(catalog)
    estimate = calculate_annual_estimate(estimate_input, pack)
    tax = estimate.tax
    if tax is None:
        baseline = estimate.baseline
        return ThaiEsgWhatIfResult(
            estimate,
            WhatIfStatus.BASELINE_NOT_READY,
            baseline.reason_codes,
            baseline.missing_fact_ids,
        )
    if tax.planning_availability not in _OPEN_AVAILABILITY:
        return ThaiEsgWhatIfResult(
            estimate, WhatIfStatus.UNSUPPORTED, (tax.planning_availability.value,), ()
        )
    missing = _missing(inputs)
    if missing:
        return ThaiEsgWhatIfResult(
            estimate, WhatIfStatus.REQUIRES_INPUT, (), missing, amount=inputs.amount
        )
    return _evaluate_amount(
        estimate,
        tax=tax,
        estimate_input=estimate_input,
        inputs=inputs,
        catalog=catalog,
        financial_policy=financial_policy,
        amount=cast(Money, inputs.amount),
    )


def _evaluate_amount(
    estimate: AnnualEstimateResult,
    *,
    tax: TaxState,
    estimate_input: AnnualEstimateInput,
    inputs: ThaiEsgWhatIfInput,
    catalog: ActivatedOpportunityCatalog,
    financial_policy: ActivatedFinancialPolicy,
    amount: Money,
) -> ThaiEsgWhatIfResult:
    definition = catalog.catalog.definition(THAI_ESG)
    used = Money.sum(
        item.amount_used
        for item in estimate_input.shared_limit_usage or ()
        if item.group_id == definition.shared_limit_group
    )
    capacity = calculate_opportunity_capacity(
        definition,
        catalog.catalog,
        assessable_income=tax.income.assessable_income,
        shared_amount_used=used,
    )
    basis = (
        CapacityBasis.CONSERVATIVE_AFTER_PVD_EXEMPTION
        if tax.income.pvd_exemption.is_positive()
        else CapacityBasis.ASSESSABLE_INCOME
    )
    remaining = capacity.remaining_capacity
    cutoff = estimate_input.cutoff_date
    if cutoff is None:
        raise AssertionError("unreachable: a READY estimate has a cutoff date")
    # The guardrail budget cannot exceed known liquid assets (financial-state fail-closed rule).
    budget = Money.min(remaining, cast(Money, inputs.financial.liquid_assets))
    state = compute_financial_state(
        inputs.financial, financial_policy, FinancialPlanningContext(cutoff, budget)
    )
    guardrail = assess_new_cash_opportunity(
        NewCashInputs(THAI_ESG, definition.category, remaining, budget, state)
    )
    evaluated = ThaiEsgWhatIfResult(
        estimate,
        WhatIfStatus.READY,
        (),
        (),
        amount=amount,
        capacity=capacity,
        capacity_basis=basis,
        financial_state=state,
        guardrail=guardrail,
        lockup=definition.lockup_metadata,
        evidence_requirements=definition.evidence_requirements,
    )
    if amount > remaining:
        return replace(
            evaluated,
            status=WhatIfStatus.EXCEEDS_TAX_CAPACITY,
            reason_codes=(EXCEEDS_TAX_CAPACITY_REASON,),
        )
    limit = guardrail.max_feasible_allocation
    if limit is None or amount > limit:
        return replace(
            evaluated,
            status=WhatIfStatus.GUARDRAIL_LIMITED,
            reason_codes=tuple(reason.value for reason in guardrail.reason_codes),
        )
    impact = calculate_tax_saving(cast(Money, tax.taxable_income), amount, tax._activated_pack)
    if impact.pit_before != tax.pit:
        raise AssertionError("unreachable: what-if baseline differs from the C03 PIT")
    if estimate.annual_withholding is None:
        return replace(evaluated, impact=impact)
    kind, settled = settle(impact.pit_after, estimate.annual_withholding)
    return replace(
        evaluated, impact=impact, settlement_after_kind=kind, settlement_after_amount=settled
    )
