"""TGPS-P1-003 FIN-01..05: deterministic Financial State computation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    activate_financial_policy,
    bundled_financial_policy,
)
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialPlanningContext,
    FinancialProfile,
    ProtectionProfile,
)
from tax_gps.financial.reason_codes import FinancialReasonCode
from tax_gps.financial.state import (
    FinancialStateStatus,
    FinancialValidationError,
    _emergency_fund_months,
    compute_financial_state,
)

PLANNING_DATE = date(2026, 6, 1)


def _policy() -> ActivatedFinancialPolicy:
    return activate_financial_policy(bundled_financial_policy(TaxYear(2026)))


def _context(budget: int, planning_date: date = PLANNING_DATE) -> FinancialPlanningContext:
    return FinancialPlanningContext(planning_date=planning_date, available_budget=Money.of(budget))


@pytest.mark.mandatory
def test_fin_01_emergency_fund_months_and_floor_target() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(300000), monthly_essential_expenses=Money.of(50000)
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.emergency_fund_months == "6.00"
    assert state.emergency_reserve_floor == Money.of(150000)
    assert state.emergency_reserve_target == Money.of(300000)


@pytest.mark.mandatory
def test_fin_02_protected_liquidity_and_spendable_surplus() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(300000),
        monthly_essential_expenses=Money.of(50000),
        committed_cash_needs=(
            CommittedCashNeed(
                need_id="tuition",
                amount=Money.of(100000),
                due_date=date(2026, 9, 1),
                mandatory=True,
                description="tuition",
            ),
        ),
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.emergency_reserve_floor == Money.of(150000)
    assert state.protected_liquidity == Money.of(250000)
    assert state.spendable_surplus == Money.of(50000)


@pytest.mark.mandatory
def test_fin_03_spendable_surplus_never_negative() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(100000),
        monthly_essential_expenses=Money.of(100000),
    )
    # liquid = 100,000; floor = 3 * 100,000 = 300,000 > liquid -> spendable surplus floors at zero.
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.protected_liquidity == Money.of(300000)
    assert state.spendable_surplus == Money.zero()


@pytest.mark.mandatory
def test_fin_04_critical_debt_balance_and_ids() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(500000),
        monthly_essential_expenses=Money.of(50000),
        debts=(
            Debt(
                debt_id="cc-1",
                category=DebtCategory.CREDIT_CARD,
                outstanding_balance=Money.of(100000),
                annual_percentage_rate=Decimal("0.18"),
                minimum_monthly_payment=Money.of(3000),
                secured=False,
            ),
        ),
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.critical_debt_balance == Money.of(100000)
    assert state.critical_debt_ids == ("cc-1",)


@pytest.mark.mandatory
@pytest.mark.negative
def test_fin_05_debt_below_threshold_is_not_classified_critical() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(500000),
        monthly_essential_expenses=Money.of(50000),
        debts=(
            Debt(
                debt_id="loan-1",
                category=DebtCategory.PERSONAL_LOAN,
                outstanding_balance=Money.of(100000),
                annual_percentage_rate=Decimal("0.10"),
                minimum_monthly_payment=Money.of(3000),
                secured=False,
            ),
        ),
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.critical_debt_balance == Money.zero()
    assert state.critical_debt_ids == ()


@pytest.mark.mandatory
@pytest.mark.boundary
def test_debt_at_exactly_the_critical_apr_threshold_is_classified_critical() -> None:
    """Boundary: APR == policy.critical_debt_apr (15.00%) must be >= critical, not just >."""
    profile = FinancialProfile(
        liquid_assets=Money.of(500000),
        monthly_essential_expenses=Money.of(50000),
        debts=(
            Debt(
                debt_id="boundary-1",
                category=DebtCategory.CREDIT_CARD,
                outstanding_balance=Money.of(100000),
                annual_percentage_rate=Decimal("0.15"),
                minimum_monthly_payment=Money.of(3000),
                secured=False,
            ),
        ),
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.critical_debt_balance == Money.of(100000)
    assert state.critical_debt_ids == ("boundary-1",)


@pytest.mark.mandatory
@pytest.mark.boundary
def test_debt_just_below_the_critical_apr_threshold_is_not_classified_critical() -> None:
    """Boundary: APR == 14.99% must fall on the non-critical side of the >= 15.00% threshold."""
    profile = FinancialProfile(
        liquid_assets=Money.of(500000),
        monthly_essential_expenses=Money.of(50000),
        debts=(
            Debt(
                debt_id="boundary-2",
                category=DebtCategory.CREDIT_CARD,
                outstanding_balance=Money.of(100000),
                annual_percentage_rate=Decimal("0.1499"),
                minimum_monthly_payment=Money.of(3000),
                secured=False,
            ),
        ),
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.critical_debt_balance == Money.zero()
    assert state.critical_debt_ids == ()


@pytest.mark.negative
def test_zero_essential_expenses_do_not_divide_by_zero() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(100000), monthly_essential_expenses=Money.zero()
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.emergency_fund_months is None
    assert FinancialReasonCode.ZERO_ESSENTIAL_EXPENSE_BASE in state.reason_codes


@pytest.mark.negative
def test_missing_expenses_yields_partial_status_and_input_required_reason() -> None:
    profile = FinancialProfile(liquid_assets=Money.of(100000), monthly_essential_expenses=None)
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.status is FinancialStateStatus.PARTIAL
    assert FinancialReasonCode.FINANCIAL_INPUT_REQUIRED in state.reason_codes
    assert state.emergency_reserve_floor is None
    assert state.spendable_surplus is None


@pytest.mark.negative
def test_budget_exceeding_liquid_assets_fails_closed() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(10000), monthly_essential_expenses=Money.of(5000)
    )
    with pytest.raises(FinancialValidationError):
        compute_financial_state(profile, _policy(), _context(20000))


@pytest.mark.negative
def test_budget_without_known_liquid_assets_fails_closed() -> None:
    profile = FinancialProfile(liquid_assets=None, monthly_essential_expenses=Money.of(5000))
    with pytest.raises(FinancialValidationError):
        compute_financial_state(profile, _policy(), _context(0))


def test_protection_gap_computed_when_both_known() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(500000),
        monthly_essential_expenses=Money.of(50000),
        protection=ProtectionProfile(
            required_life_coverage=Money.of(3000000), existing_life_coverage=Money.of(1000000)
        ),
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.protection_gap == Money.of(2000000)


def test_protection_gap_unknown_when_required_coverage_unknown() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(500000), monthly_essential_expenses=Money.of(50000)
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    assert state.protection_gap is None
    assert FinancialReasonCode.PROTECTION_NEED_UNKNOWN in state.reason_codes


@pytest.mark.replay
def test_financial_state_hash_is_deterministic() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(300000), monthly_essential_expenses=Money.of(50000)
    )
    policy = _policy()
    state_a = compute_financial_state(profile, policy, _context(0))
    state_b = compute_financial_state(profile, policy, _context(0))
    assert state_a.state_hash == state_b.state_hash
    assert state_a.state_hash != ""


@pytest.mark.replay
def test_financial_state_hash_changes_with_material_input() -> None:
    policy = _policy()
    base = FinancialProfile(
        liquid_assets=Money.of(300000), monthly_essential_expenses=Money.of(50000)
    )
    mutated = FinancialProfile(
        liquid_assets=Money.of(300001), monthly_essential_expenses=Money.of(50000)
    )
    state_a = compute_financial_state(base, policy, _context(0))
    state_b = compute_financial_state(mutated, policy, _context(0))
    assert state_a.state_hash != state_b.state_hash


def test_financial_state_to_dict_includes_state_hash() -> None:
    profile = FinancialProfile(
        liquid_assets=Money.of(300000), monthly_essential_expenses=Money.of(50000)
    )
    state = compute_financial_state(profile, _policy(), _context(0))
    as_dict = state.to_dict()
    assert as_dict["state_hash"] == state.state_hash


@pytest.mark.negative
def test_emergency_fund_months_none_when_expenses_zero_directly() -> None:
    assert _emergency_fund_months(Money.of(100), Money.zero()) is None
