"""Unit tests for isolated guardrail decision boundaries (TGPS-P1-003 §28-38, §43)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.decisions import (
    NewCashInputs,
    assess_new_cash_opportunity,
    critical_debt_decision,
    emergency_floor_decision,
    existing_right_passthrough,
    financial_input_required,
    is_intrinsic_purpose,
    liquidity_ceiling_decision,
    not_applicable,
    with_protection_reason,
)
from tax_gps.financial.models import GuardrailDecision
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    activate_financial_policy,
    bundled_financial_policy,
)
from tax_gps.financial.profile import (
    Debt,
    FinancialPlanningContext,
    FinancialProfile,
    ProtectionProfile,
)
from tax_gps.financial.reason_codes import FinancialReasonCode
from tax_gps.financial.state import FinancialState, compute_financial_state
from tax_gps.opportunity.models import OpportunityCategory

PLANNING_DATE = date(2026, 6, 1)


def _policy() -> ActivatedFinancialPolicy:
    return activate_financial_policy(bundled_financial_policy(TaxYear(2026)))


def _state(
    *,
    liquid_assets: int,
    expenses: int,
    debts: tuple[Debt, ...] = (),
    protection: ProtectionProfile | None = None,
) -> FinancialState:
    profile = FinancialProfile(
        liquid_assets=Money.of(liquid_assets),
        monthly_essential_expenses=Money.of(expenses),
        debts=debts,
        protection=protection or ProtectionProfile(),
    )
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    return compute_financial_state(profile, _policy(), context)


def test_not_applicable_reason() -> None:
    assessment = not_applicable("opp-1")
    assert assessment.decision is GuardrailDecision.NOT_APPLICABLE
    assert FinancialReasonCode.UPSTREAM_NOT_AVAILABLE in assessment.reason_codes


def test_existing_right_passthrough_allows() -> None:
    assessment = existing_right_passthrough("right-1")
    assert assessment.decision is GuardrailDecision.ALLOW
    assert assessment.max_feasible_allocation is None


def test_financial_input_required_never_allows() -> None:
    assessment = financial_input_required("opp-1")
    assert assessment.decision is GuardrailDecision.REQUIRE_REVIEW


def test_is_intrinsic_purpose() -> None:
    assert is_intrinsic_purpose(OpportunityCategory.UTILITY_INVESTMENT)
    assert is_intrinsic_purpose(OpportunityCategory.LIFESTYLE_INTENT)
    assert not is_intrinsic_purpose(OpportunityCategory.INVESTMENT_TAX)


def test_critical_debt_decision_none_when_no_critical_debt() -> None:
    state = _state(liquid_assets=500000, expenses=50000)
    inputs = NewCashInputs(
        opportunity_id="opp",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=state,
    )
    assert critical_debt_decision(inputs) is None


def test_emergency_floor_decision_none_when_above_floor() -> None:
    state = _state(liquid_assets=500000, expenses=50000)
    inputs = NewCashInputs(
        opportunity_id="opp",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=state,
    )
    assert emergency_floor_decision(inputs) is None


def test_liquidity_ceiling_no_surplus_intrinsic_purpose_requires_review() -> None:
    # liquid == floor exactly -> spendable surplus is zero, no debt/floor breach.
    state = _state(liquid_assets=150000, expenses=50000)
    inputs = NewCashInputs(
        opportunity_id="solar",
        category=OpportunityCategory.UTILITY_INVESTMENT,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=state,
    )
    assessment = liquidity_ceiling_decision(inputs)
    assert assessment.decision is GuardrailDecision.REQUIRE_REVIEW
    assert FinancialReasonCode.NO_SPENDABLE_SURPLUS in assessment.reason_codes


def test_liquidity_ceiling_no_surplus_non_intrinsic_blocks() -> None:
    state = _state(liquid_assets=150000, expenses=50000)
    inputs = NewCashInputs(
        opportunity_id="thai-esg",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=state,
    )
    assessment = liquidity_ceiling_decision(inputs)
    assert assessment.decision is GuardrailDecision.BLOCK
    assert assessment.max_feasible_allocation == Money.zero()


def test_with_protection_reason_no_gap_known_leaves_assessment_unchanged() -> None:
    state = _state(
        liquid_assets=500000,
        expenses=50000,
        protection=ProtectionProfile(
            required_life_coverage=Money.of(1000000),
            existing_life_coverage=Money.of(1000000),
        ),
    )
    assert state.protection_gap == Money.zero()
    base = existing_right_passthrough("right-1")
    result = with_protection_reason(base, state)
    assert result is base


def test_assess_new_cash_opportunity_partial_state_requires_review() -> None:
    profile = FinancialProfile(liquid_assets=Money.of(100000), monthly_essential_expenses=None)
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.zero())
    state = compute_financial_state(profile, _policy(), context)
    inputs = NewCashInputs(
        opportunity_id="opp",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(50000),
        available_budget=Money.of(50000),
        state=state,
    )
    assessment = assess_new_cash_opportunity(inputs)
    assert assessment.decision is GuardrailDecision.REQUIRE_REVIEW
    assert FinancialReasonCode.FINANCIAL_INPUT_REQUIRED in assessment.reason_codes


# --- Defensive branches: these functions are exported and independently callable, so they --
# --- must fail closed even given a state shape that assess_new_cash_opportunity's PARTIAL ---
# --- routing would normally prevent from ever reaching them. -------------------------------


def test_emergency_floor_decision_defensive_none_when_liquid_assets_unknown() -> None:
    state = _state(liquid_assets=500000, expenses=50000)
    tampered_state = replace(state, liquid_assets=None)
    inputs = NewCashInputs(
        opportunity_id="opp",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=tampered_state,
    )
    assert emergency_floor_decision(inputs) is None


def test_emergency_floor_decision_defensive_none_when_reserve_floor_unknown() -> None:
    state = _state(liquid_assets=500000, expenses=50000)
    tampered_state = replace(state, emergency_reserve_floor=None)
    inputs = NewCashInputs(
        opportunity_id="opp",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=tampered_state,
    )
    assert emergency_floor_decision(inputs) is None


def test_liquidity_ceiling_decision_defensive_treats_unknown_surplus_as_zero() -> None:
    state = _state(liquid_assets=500000, expenses=50000)
    tampered_state = replace(state, spendable_surplus=None)
    inputs = NewCashInputs(
        opportunity_id="thai-esg",
        category=OpportunityCategory.INVESTMENT_TAX,
        remaining_capacity=Money.of(100000),
        available_budget=Money.of(100000),
        state=tampered_state,
    )
    assessment = liquidity_ceiling_decision(inputs)
    assert assessment.decision is GuardrailDecision.BLOCK
    assert assessment.max_feasible_allocation == Money.zero()
    assert FinancialReasonCode.NO_SPENDABLE_SURPLUS in assessment.reason_codes
