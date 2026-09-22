"""Unit tests for FinancialProfile structural validation (TGPS-P1-003 §8-15).

``Unknown != zero != false``: every negative test asserts the specific InvalidValueError
condition, not merely that an exception was raised.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialPlanningContext,
    FinancialProfile,
    ProtectionProfile,
    canonical_apr,
)


def _valid_debt() -> Debt:
    return Debt(
        debt_id="cc-1",
        category=DebtCategory.CREDIT_CARD,
        outstanding_balance=Money.of(10000),
        annual_percentage_rate=Decimal("0.18"),
        minimum_monthly_payment=Money.of(500),
        secured=False,
    )


def _valid_need() -> CommittedCashNeed:
    return CommittedCashNeed(
        need_id="tuition",
        amount=Money.of(10000),
        due_date=date(2026, 9, 1),
        mandatory=True,
        description="tuition",
    )


class TestDebt:
    def test_valid_debt_round_trips_to_dict(self) -> None:
        as_dict = _valid_debt().to_dict()
        assert as_dict["debt_id"] == "cc-1"
        assert as_dict["annual_percentage_rate"] == "0.1800"

    def test_blank_debt_id_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="debt id must be named"):
            replace(_valid_debt(), debt_id="   ")

    def test_negative_outstanding_balance_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="outstanding balance cannot be negative"):
            replace(_valid_debt(), outstanding_balance=Money.of(-1))

    def test_negative_minimum_monthly_payment_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="minimum monthly payment cannot be negative"):
            replace(_valid_debt(), minimum_monthly_payment=Money.of(-1))

    def test_negative_apr_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="annual percentage rate cannot be negative"):
            replace(_valid_debt(), annual_percentage_rate=Decimal("-0.01"))

    def test_non_bool_secured_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="secured must be a boolean"):
            Debt(
                debt_id="cc-1",
                category=DebtCategory.CREDIT_CARD,
                outstanding_balance=Money.of(10000),
                annual_percentage_rate=Decimal("0.18"),
                minimum_monthly_payment=Money.of(500),
                secured=1,  # type: ignore[arg-type]
            )

    def test_zero_apr_is_accepted(self) -> None:
        debt = replace(_valid_debt(), annual_percentage_rate=Decimal("0"))
        assert debt.annual_percentage_rate == Decimal("0")


class TestCanonicalApr:
    def test_zero_normalizes_without_negative_zero(self) -> None:
        assert canonical_apr(Decimal("0")) == "0.0000"
        assert canonical_apr(Decimal("-0")) == "0.0000"

    def test_preserves_precision_beyond_four_places(self) -> None:
        assert canonical_apr(Decimal("0.123456")) == "0.123456"

    def test_pads_to_minimum_four_places(self) -> None:
        assert canonical_apr(Decimal("0.18")) == "0.1800"


class TestCommittedCashNeed:
    def test_valid_need_round_trips_to_dict(self) -> None:
        as_dict = _valid_need().to_dict()
        assert as_dict["need_id"] == "tuition"
        assert as_dict["due_date"] == "2026-09-01"

    def test_blank_need_id_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="need id must be named"):
            replace(_valid_need(), need_id="")

    def test_negative_amount_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="amount cannot be negative"):
            replace(_valid_need(), amount=Money.of(-1))

    def test_non_bool_mandatory_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="mandatory must be a boolean"):
            CommittedCashNeed(
                need_id="tuition",
                amount=Money.of(10000),
                due_date=date(2026, 9, 1),
                mandatory=1,  # type: ignore[arg-type]
                description="tuition",
            )


class TestProtectionProfile:
    def test_defaults_are_unknown_not_zero(self) -> None:
        protection = ProtectionProfile()
        assert protection.required_life_coverage is None
        assert protection.existing_life_coverage is None
        assert protection.protection_gap is None

    def test_negative_required_life_coverage_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="required life coverage cannot be negative"):
            ProtectionProfile(required_life_coverage=Money.of(-1))

    def test_negative_existing_life_coverage_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="existing life coverage cannot be negative"):
            ProtectionProfile(existing_life_coverage=Money.of(-1))

    def test_gap_is_unknown_when_only_required_is_known(self) -> None:
        protection = ProtectionProfile(required_life_coverage=Money.of(1000000))
        assert protection.protection_gap is None

    def test_gap_is_unknown_when_only_existing_is_known(self) -> None:
        protection = ProtectionProfile(existing_life_coverage=Money.of(1000000))
        assert protection.protection_gap is None

    def test_gap_floors_at_zero_when_covered_exceeds_required(self) -> None:
        protection = ProtectionProfile(
            required_life_coverage=Money.of(1000000), existing_life_coverage=Money.of(2000000)
        )
        assert protection.protection_gap == Money.zero()

    def test_to_dict_serializes_unknown_as_null(self) -> None:
        assert ProtectionProfile().to_dict() == {
            "required_life_coverage": None,
            "existing_life_coverage": None,
        }


class TestFinancialProfile:
    def test_defaults_are_unknown_not_zero(self) -> None:
        profile = FinancialProfile()
        assert profile.liquid_assets is None
        assert profile.monthly_essential_expenses is None
        assert profile.debts == ()
        assert profile.committed_cash_needs == ()

    def test_negative_liquid_assets_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="liquid assets cannot be negative"):
            FinancialProfile(liquid_assets=Money.of(-1))

    def test_negative_monthly_essential_expenses_is_rejected(self) -> None:
        with pytest.raises(
            InvalidValueError, match="monthly essential expenses cannot be negative"
        ):
            FinancialProfile(monthly_essential_expenses=Money.of(-1))

    def test_duplicate_debt_ids_are_rejected(self) -> None:
        debt_a = _valid_debt()
        debt_b = replace(_valid_debt(), outstanding_balance=Money.of(1))
        with pytest.raises(InvalidValueError, match="duplicate debt id"):
            FinancialProfile(debts=(debt_a, debt_b))

    def test_duplicate_debt_ids_case_and_whitespace_insensitive(self) -> None:
        debt_a = replace(_valid_debt(), debt_id="CC-1")
        debt_b = replace(_valid_debt(), debt_id=" cc-1 ")
        with pytest.raises(InvalidValueError, match="duplicate debt id"):
            FinancialProfile(debts=(debt_a, debt_b))

    def test_duplicate_committed_cash_need_ids_are_rejected(self) -> None:
        need_a = _valid_need()
        need_b = replace(_valid_need(), amount=Money.of(1))
        with pytest.raises(InvalidValueError, match="duplicate committed cash need id"):
            FinancialProfile(committed_cash_needs=(need_a, need_b))

    def test_distinct_debt_and_need_ids_are_accepted(self) -> None:
        debt_a = _valid_debt()
        debt_b = replace(_valid_debt(), debt_id="cc-2")
        need_a = _valid_need()
        need_b = replace(_valid_need(), need_id="rent")
        profile = FinancialProfile(debts=(debt_a, debt_b), committed_cash_needs=(need_a, need_b))
        assert len(profile.debts) == 2
        assert len(profile.committed_cash_needs) == 2

    def test_to_dict_serializes_all_sections(self) -> None:
        profile = FinancialProfile(
            liquid_assets=Money.of(100000),
            monthly_essential_expenses=Money.of(20000),
            debts=(_valid_debt(),),
            committed_cash_needs=(_valid_need(),),
        )
        as_dict = profile.to_dict()
        assert as_dict["liquid_assets"] == "100000.00"
        debts = as_dict["debts"]
        needs = as_dict["committed_cash_needs"]
        assert isinstance(debts, list)
        assert isinstance(needs, list)
        assert len(debts) == 1
        assert len(needs) == 1
        assert as_dict["protection"] == {
            "required_life_coverage": None,
            "existing_life_coverage": None,
        }


class TestFinancialPlanningContext:
    def test_negative_available_budget_is_rejected(self) -> None:
        with pytest.raises(InvalidValueError, match="available budget cannot be negative"):
            FinancialPlanningContext(planning_date=date(2026, 6, 1), available_budget=Money.of(-1))

    def test_zero_available_budget_is_accepted(self) -> None:
        context = FinancialPlanningContext(
            planning_date=date(2026, 6, 1), available_budget=Money.zero()
        )
        assert context.to_dict()["available_budget"] == "0.00"
