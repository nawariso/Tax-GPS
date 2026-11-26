"""Deterministic annual estimate and withholding reconciliation."""

from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum
from typing import cast

from tax_gps.calculation.models import TaxState, TaxStatus
from tax_gps.calculation.readiness import BaselineReadiness, BaselineRights, assess_coverage
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import calculate_tax
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import (
    Child,
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    RetirementContribution,
    SharedLimitUsage,
    UserProfile,
)
from tax_gps.profile.rmf import RmfFactConflictError


class AnnualEstimateInputError(InvalidValueError):
    def __init__(self, fact_id: str) -> None:
        self.fact_id = fact_id
        super().__init__(f"invalid annual estimate field: {fact_id}")


@dataclass(frozen=True, slots=True)
class EstimatePeriod:
    wages: Money | None
    bonus: Money | None
    withholding: Money | None
    outside_coverage: bool | None

    def income(self) -> Money | None:
        if self.wages is None or self.bonus is None:
            return None
        return self.wages + self.bonus


@dataclass(frozen=True, slots=True)
class AnnualEstimateRights(BaselineRights):
    children: tuple[Child, ...]
    personal_eligible: bool | None
    social_security_paid: Money | None
    mortgage_interest_paid: Money | None
    mortgage_eligible: bool | None
    unconfirmed_children: tuple[int, ...] = ()

    def confirmed_benefits(self) -> ExistingTaxBenefits:
        # Call only after annual and baseline missing-fact checks.
        return ExistingTaxBenefits(
            personal_eligible=cast(bool, self.personal_eligible),
            social_security_paid=cast(Money, self.social_security_paid),
            parents=self.parents,
            children=self.children,
            mortgage_interest_paid=cast(Money, self.mortgage_interest_paid),
            mortgage_eligible=cast(bool, self.mortgage_eligible),
            retirement_contributions=cast(
                tuple[RetirementContribution, ...], self.retirement_contributions
            ),
            pvd=self.pvd,
            other_rights=self.other_rights,
            fund_history=self.fund_history,
            rmf=self.rmf,
        )


@dataclass(frozen=True, slots=True)
class AnnualEstimateInput:
    tax_year: TaxYear
    cutoff_date: date | None
    confirmed_for: date | None
    actual: EstimatePeriod
    forecast: EstimatePeriod
    rights: AnnualEstimateRights
    shared_limit_usage: tuple[SharedLimitUsage, ...] | None
    pvd_forecast_single_employer: bool | None


class SettlementKind(StrEnum):
    PAY_MORE = "PAY_MORE"
    REFUND = "REFUND"
    BALANCED = "BALANCED"


@dataclass(frozen=True, slots=True)
class AnnualEstimateResult:
    baseline: BaselineReadiness
    tax: TaxState | None
    settlement_status: TaxStatus
    withholding_missing_fact_ids: tuple[str, ...]
    annual_withholding: Money | None = None
    settlement_kind: SettlementKind | None = None
    settlement_amount: Money | None = None


def _check_money(value: Money | None, fact_id: str, *, must_be_zero: bool = False) -> None:
    if value is not None and (
        value.is_negative() or not value.is_whole_satang() or (must_be_zero and value.is_positive())
    ):
        raise AnnualEstimateInputError(fact_id)


def _validate_dates(inputs: AnnualEstimateInput, pack: ActivatedRulePack) -> bool:
    year = inputs.tax_year
    if year.gregorian != 2026 or year != pack.pack.tax_year:
        raise AnnualEstimateInputError("tax_year")
    for fact_id, value in (
        ("cutoff_date", inputs.cutoff_date),
        ("confirmed_for", inputs.confirmed_for),
    ):
        if value is not None and (type(value) is not date or value.year != year.gregorian):
            raise AnnualEstimateInputError(fact_id)
    return inputs.cutoff_date == date(year.gregorian, 12, 31)


def _annual_facts(
    inputs: AnnualEstimateInput, *, year_end: bool
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    missing: list[str] = []
    outside: list[str] = []
    withholding_missing: list[str] = []
    if inputs.cutoff_date is None:
        missing.append("cutoff_date")
    elif inputs.confirmed_for != inputs.cutoff_date:
        missing.append("confirmed_for")
    for name, period in (("actual", inputs.actual), ("forecast", inputs.forecast)):
        for field, amount in (
            ("wages", period.wages),
            ("bonus", period.bonus),
            ("withholding", period.withholding),
        ):
            fact_id = f"{name}.{field}"
            _check_money(amount, fact_id, must_be_zero=year_end and name == "forecast")
            if amount is None:
                (withholding_missing if field == "withholding" else missing).append(fact_id)
        if period.outside_coverage is None:
            missing.append(f"{name}.outside_coverage")
        elif period.outside_coverage:
            outside.append(f"{name.upper()}_OUTSIDE_COVERAGE")
    rights = inputs.rights
    _check_money(rights.social_security_paid, "social_security")
    _check_money(rights.mortgage_interest_paid, "mortgage_interest")
    for fact_id, value in (
        ("social_security", rights.social_security_paid),
        ("mortgage_interest", rights.mortgage_interest_paid),
        ("personal_eligible", rights.personal_eligible),
        ("mortgage_eligible", rights.mortgage_eligible),
    ):
        if value is None:
            missing.append(fact_id)
    missing.extend(f"children[{index}].legally_eligible" for index in rights.unconfirmed_children)
    return tuple(missing), tuple(outside), tuple(withholding_missing)


def _covered_rights(
    inputs: AnnualEstimateInput, *, year_end: bool
) -> tuple[AnnualEstimateRights, tuple[str, ...]]:
    rights = inputs.rights
    rmf = rights.rmf
    pvd = rights.pvd
    if pvd is not None:
        _check_money(pvd.employee_paid, "pvd.employee_paid")
        _check_money(pvd.wage_basis, "pvd.wage_basis")
    if rmf is not None:
        _check_money(rmf.own_purchase_paid, "rmf.own_purchase_paid")
        if rmf.report_confirmation is not None:
            _check_money(rmf.report_confirmation.cumulative_paid, "rmf.report_confirmation")
    for item in rights.retirement_contributions or ():
        _check_money(item.amount_used, "retirement_usage")
    for usage in inputs.shared_limit_usage or ():
        _check_money(usage.amount_used, "shared_usage")
    if (
        rmf is not None
        and rmf.assessment_date is not None
        and inputs.cutoff_date is not None
        and rmf.assessment_date != inputs.cutoff_date
    ):
        raise RmfFactConflictError("rmf.assessment_date")
    if year_end or pvd is None or pvd.employee_paid is None or pvd.employee_paid.is_zero():
        return rights, ()
    forecast_employer = inputs.pvd_forecast_single_employer
    if forecast_employer is False:
        return replace(rights, pvd=replace(pvd, single_employer=False)), ()
    missing = ("pvd_forecast_single_employer",) if forecast_employer is None else ()
    return rights, missing


def calculate_annual_estimate(
    inputs: AnnualEstimateInput, pack: ActivatedRulePack
) -> AnnualEstimateResult:
    year_end = _validate_dates(inputs, pack)
    missing, outside, withholding_missing = _annual_facts(inputs, year_end=year_end)
    rights, employer_missing = _covered_rights(inputs, year_end=year_end)
    actual = inputs.actual.income()
    baseline = assess_coverage(
        rights,
        tax_year=inputs.tax_year,
        usage=inputs.shared_limit_usage,
        pvd_income=actual,
        unsupported_income=bool(outside),
        pack=pack,
        extra_missing=missing + employer_missing,
        extra_reasons=outside,
    )
    if baseline.status is not TaxStatus.READY:
        return AnnualEstimateResult(baseline, None, baseline.status, withholding_missing)

    profile = UserProfile(
        profile_id="annual-estimate",
        version="1",
        tax_year=inputs.tax_year,
        income=IncomeProfile(cast(Money, actual) + cast(Money, inputs.forecast.income())),
        benefits=rights.confirmed_benefits(),
        opportunity_facts=OpportunityFacts(shared_limit_usage=inputs.shared_limit_usage),
    )
    tax = calculate_tax(profile, pack)
    if tax.pit is None:
        raise AssertionError("unreachable: annual and baseline readiness disagree")
    if withholding_missing:
        return AnnualEstimateResult(baseline, tax, TaxStatus.REQUIRES_INPUT, withholding_missing)

    withholding = cast(Money, inputs.actual.withholding) + cast(Money, inputs.forecast.withholding)
    difference = tax.pit - withholding
    if difference.is_negative():
        kind, amount = SettlementKind.REFUND, Money.zero() - difference
    else:
        kind = SettlementKind.BALANCED if difference.is_zero() else SettlementKind.PAY_MORE
        amount = difference
    return AnnualEstimateResult(baseline, tax, TaxStatus.READY, (), withholding, kind, amount)
