"""Explicit purchase facts; no eligibility or reporting defaults."""

from dataclasses import dataclass, fields
from datetime import date
from enum import StrEnum

from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear


class RmfReportingStatus(StrEnum):
    NOT_YET_DUE = "NOT_YET_DUE"
    CONFIRMED_SUBMITTED = "CONFIRMED_SUBMITTED"
    DISCREPANCY_OR_CORRECTION = "DISCREPANCY_OR_CORRECTION"


_BOOL_FIELDS = (
    "ordinary_own_purchase_confirmed",
    "single_fund",
    "single_amc",
    "first_ever_purchase_in_tax_year",
    "paid_through_assessment_date",
    "declaration_completed",
    "no_distributions_or_borrowing",
    "no_known_reporting_problem",
    "future_obligations_acknowledged",
)


class RmfFactConflictError(InvalidValueError):
    """Only code-owned field IDs may leave the domain in error metadata."""

    def __init__(self, fact_id: str) -> None:
        allowed = {
            "rmf.own_purchase_paid",
            "rmf.first_purchase_date",
            "rmf.assessment_date",
            "rmf.report_confirmation",
            "rmf.reporting_status",
        }
        self.fact_id = fact_id if fact_id in allowed else "rmf.report_confirmation"
        super().__init__(self.fact_id + " conflicts with current facts")


def _name(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InvalidValueError("RMF identity must be nonblank text")


def _date(value: object) -> None:
    if type(value) is not date:
        raise InvalidValueError("RMF date must be a calendar date")


def _paid(value: object) -> None:
    if not isinstance(value, Money) or value.is_negative():
        raise InvalidValueError("RMF paid must be nonnegative Money")


@dataclass(frozen=True, slots=True)
class RmfReportConfirmation:
    fund_name: str
    amc_name: str
    tax_year: TaxYear
    cumulative_paid: Money
    confirmed_on: date

    def __post_init__(self) -> None:
        _name(self.fund_name)
        _name(self.amc_name)
        _paid(self.cumulative_paid)
        _date(self.confirmed_on)
        if not isinstance(self.tax_year, TaxYear):
            raise InvalidValueError("RMF confirmation tax year required")

    def to_dict(self) -> dict[str, object]:
        return {
            "fund_name": self.fund_name,
            "amc_name": self.amc_name,
            "tax_year": self.tax_year.gregorian,
            "cumulative_paid": self.cumulative_paid.canonical(),
            "confirmed_on": self.confirmed_on.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class RmfFacts:
    own_purchase_paid: Money | None = None
    fund_name: str | None = None
    amc_name: str | None = None
    first_purchase_date: date | None = None
    assessment_date: date | None = None
    reporting_status: RmfReportingStatus | None = None
    report_confirmation: RmfReportConfirmation | None = None
    ordinary_own_purchase_confirmed: bool | None = None
    single_fund: bool | None = None
    single_amc: bool | None = None
    first_ever_purchase_in_tax_year: bool | None = None
    paid_through_assessment_date: bool | None = None
    declaration_completed: bool | None = None
    no_distributions_or_borrowing: bool | None = None
    no_known_reporting_problem: bool | None = None
    future_obligations_acknowledged: bool | None = None

    def __post_init__(self) -> None:
        for name in _BOOL_FIELDS:
            value = getattr(self, name)
            if value is not None and type(value) is not bool:
                raise InvalidValueError("RMF condition must be boolean or null")
        for name in ("fund_name", "amc_name"):
            if (value := getattr(self, name)) is not None:
                _name(value)
        for name in ("first_purchase_date", "assessment_date"):
            if (value := getattr(self, name)) is not None:
                _date(value)
        if self.own_purchase_paid is not None:
            _paid(self.own_purchase_paid)
        if self.reporting_status is not None and not isinstance(
            self.reporting_status, RmfReportingStatus
        ):
            raise InvalidValueError("RMF reporting status must be a typed value")
        if self.report_confirmation is not None and not isinstance(
            self.report_confirmation, RmfReportConfirmation
        ):
            raise InvalidValueError("RMF report confirmation must be immutable")

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {f.name: getattr(self, f.name) for f in fields(self)}
        result["own_purchase_paid"] = (
            self.own_purchase_paid.canonical() if self.own_purchase_paid is not None else None
        )
        for name in ("first_purchase_date", "assessment_date"):
            value = getattr(self, name)
            result[name] = value.isoformat() if value is not None else None
        result["report_confirmation"] = (
            self.report_confirmation.to_dict() if self.report_confirmation is not None else None
        )
        return result
