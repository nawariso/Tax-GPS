"""Pack-driven RMF arithmetic and dated current-fact readiness."""

from dataclasses import dataclass, fields
from datetime import date

from tax_gps.calculation.pvd import pvd_parameter
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage
from tax_gps.core.tax_year import TaxYear
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.rmf import (
    RmfFactConflictError,
    RmfFacts,
    RmfReportConfirmation,
    RmfReportingStatus,
)


@dataclass(frozen=True, slots=True)
class RmfCalculation:
    own_purchase_paid: Money
    qualifying_paid: Money
    percentage_cap: Money
    claimed: Money
    excess: Money

    def to_dict(self) -> dict[str, object]:
        return {f.name: getattr(self, f.name).canonical() for f in fields(self)}


def calculate_rmf(
    own_purchase_paid: Money, taxable_assessable_income: Money, pack: ActivatedRulePack
) -> RmfCalculation:
    if own_purchase_paid.is_negative() or taxable_assessable_income.is_negative():
        raise InvalidValueError("RMF calculation inputs must be nonnegative")
    cap = taxable_assessable_income * Percentage.of(
        pvd_parameter(pack, "RMF_DEDUCTION", "percentage")
    )
    claimed = Money.min(
        own_purchase_paid, Money.min(cap, Money.of(pvd_parameter(pack, "RMF_DEDUCTION", "maximum")))
    )
    return RmfCalculation(
        own_purchase_paid, own_purchase_paid, cap, claimed, own_purchase_paid - claimed
    )


def reporting_due_date(year: TaxYear, pack: ActivatedRulePack) -> date:
    return date(
        year.gregorian + 1,
        int(pvd_parameter(pack, "RMF_REPORTING", "month")),
        int(pvd_parameter(pack, "RMF_REPORTING", "day")),
    )


def assess_rmf(  # noqa: PLR0912 — explicit finite current-fact checks
    presence: bool | None, facts: RmfFacts | None, year: TaxYear, pack: ActivatedRulePack
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return named unsupported/missing facts; contradictions are private errors."""
    if (
        facts is not None
        and facts.own_purchase_paid is not None
        and (
            (presence is False and facts.own_purchase_paid.is_positive())
            or (presence is True and facts.own_purchase_paid == Money.zero())
        )
    ):
        raise RmfFactConflictError("rmf.own_purchase_paid")
    if presence is not True:
        return (), ()
    if facts is None:
        return (), ("rmf",)
    missing: list[str] = []
    reasons: list[str] = []
    for f in fields(facts):
        if f.name == "report_confirmation":
            continue
        value = getattr(facts, f.name)
        if value is None:
            missing.append("rmf." + f.name)
        elif value is False:
            reasons.append("RMF_" + f.name.upper() + "_UNSUPPORTED")
    first, assessment = facts.first_purchase_date, facts.assessment_date
    status = facts.reporting_status
    if (
        status is RmfReportingStatus.NOT_YET_DUE
        and assessment is not None
        and assessment >= reporting_due_date(year, pack)
    ):
        raise RmfFactConflictError("rmf.reporting_status")
    if first is not None and first.year != year.gregorian:
        raise RmfFactConflictError("rmf.first_purchase_date")
    if assessment is not None and assessment.year != year.gregorian:
        raise RmfFactConflictError("rmf.assessment_date")
    if first is not None and assessment is not None and first > assessment:
        raise RmfFactConflictError("rmf.first_purchase_date")
    status, receipt = facts.reporting_status, facts.report_confirmation
    if receipt is not None and status is not RmfReportingStatus.CONFIRMED_SUBMITTED:
        raise RmfFactConflictError("rmf.report_confirmation")
    if status is RmfReportingStatus.DISCREPANCY_OR_CORRECTION:
        reasons.append("RMF_REPORTING_DISCREPANCY_UNSUPPORTED")
    if status is RmfReportingStatus.CONFIRMED_SUBMITTED:
        if receipt is None:
            missing.append("rmf.report_confirmation")
        elif (
            receipt.fund_name != facts.fund_name
            or receipt.amc_name != facts.amc_name
            or receipt.tax_year != year
            or receipt.cumulative_paid != facts.own_purchase_paid
            or (first is not None and receipt.confirmed_on < first)
            or (assessment is not None and receipt.confirmed_on > assessment)
        ):
            raise RmfFactConflictError("rmf.report_confirmation")
    return tuple(reasons), tuple(missing)


@dataclass(frozen=True, slots=True)
class RmfConditions:
    first_purchase_date: date
    assessment_date: date
    acknowledged: bool
    reporting_status: RmfReportingStatus
    report_confirmation: RmfReportConfirmation | None
    reporting_due_date: date
    minimum_holding_years: int
    minimum_redemption_age: int
    maximum_purchase_gap_years: int
    obligation_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "first_purchase_date": self.first_purchase_date.isoformat(),
            "assessment_date": self.assessment_date.isoformat(),
            "acknowledged": self.acknowledged,
            "reporting_status": self.reporting_status.value,
            "report_confirmation": self.report_confirmation.to_dict()
            if self.report_confirmation is not None
            else None,
            "reporting_due_date": self.reporting_due_date.isoformat(),
            "minimum_holding_years": self.minimum_holding_years,
            "minimum_redemption_age": self.minimum_redemption_age,
            "maximum_purchase_gap_years": self.maximum_purchase_gap_years,
            "obligation_codes": list(self.obligation_codes),
        }


def build_rmf_conditions(
    facts: RmfFacts, tax_year: TaxYear, pack: ActivatedRulePack
) -> RmfConditions:
    if (
        facts.first_purchase_date is None
        or facts.assessment_date is None
        or facts.reporting_status is None
        or facts.future_obligations_acknowledged is not True
    ):
        raise InvalidValueError("RMF conditions require a ready baseline")
    codes: tuple[str, ...] = (
        "RMF_CONTINUITY_REQUIRED",
        "RMF_HOLDING_REDEMPTION_REQUIRED",
        "RMF_NO_DISTRIBUTIONS_REQUIRED",
        "RMF_NO_BORROWING_WITHDRAWAL_REQUIRED",
    )
    if facts.reporting_status is RmfReportingStatus.NOT_YET_DUE:
        codes += ("RMF_AMC_REPORTING_PENDING",)
    return RmfConditions(
        facts.first_purchase_date,
        facts.assessment_date,
        facts.future_obligations_acknowledged,
        facts.reporting_status,
        facts.report_confirmation,
        reporting_due_date(tax_year, pack),
        int(pvd_parameter(pack, "RMF_CONTINUING_CONDITIONS", "minimum_holding_years")),
        int(pvd_parameter(pack, "RMF_CONTINUING_CONDITIONS", "minimum_redemption_age")),
        int(pvd_parameter(pack, "RMF_CONTINUING_CONDITIONS", "maximum_purchase_gap_years")),
        codes,
    )
