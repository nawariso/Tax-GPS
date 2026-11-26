"""C03-AC01–08: annual totals, named readiness gates, and settlement."""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, cast

import pytest

from tax_gps.calculation.annual_estimate import (
    AnnualEstimateInput,
    AnnualEstimateInputError,
    AnnualEstimateRights,
    EstimatePeriod,
    SettlementKind,
    calculate_annual_estimate,
)
from tax_gps.calculation.models import TaxStatus
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.profile.pvd import PvdFacts, PvdWageBasisError
from tax_gps.profile.rmf import (
    RmfFactConflictError,
    RmfFacts,
    RmfReportConfirmation,
    RmfReportingStatus,
)
from tests.acceptance.test_c02b_rmf import rmf_profile
from tests.support.policy import production_pack
from tests.support.profiles import complete_benefits

CUTOFF = date(2026, 10, 31)


def base_input() -> AnnualEstimateInput:
    benefits = complete_benefits()
    return AnnualEstimateInput(
        tax_year=TaxYear(2026),
        cutoff_date=CUTOFF,
        confirmed_for=CUTOFF,
        actual=EstimatePeriod(Money.of(600000), Money.of(40000), Money.of(45000), False),
        forecast=EstimatePeriod(Money.of(300500), Money.of(50000), Money.of(30000), False),
        rights=AnnualEstimateRights(
            parents=(),
            children=(),
            retirement_contributions=(),
            pvd=benefits.pvd,
            other_rights=benefits.other_rights,
            fund_history=benefits.fund_history,
            rmf=None,
            personal_eligible=True,
            social_security_paid=Money.zero(),
            mortgage_interest_paid=Money.zero(),
            mortgage_eligible=False,
        ),
        shared_limit_usage=(),
        pvd_forecast_single_employer=None,
    )


@pytest.mark.parametrize(
    ("bonus", "gross", "taxable", "pit"),
    [(50000, 990500, 830500, 81100), (70000, 1010500, 850500, 85100), (0, 940500, 780500, 71100)],
)
def test_c03_wage_and_bonus_aggregation_and_forecast_edit(
    bonus: int, gross: int, taxable: int, pit: int
) -> None:
    original = base_input()
    changed = replace(original, forecast=replace(original.forecast, bonus=Money.of(bonus)))
    result = calculate_annual_estimate(changed, production_pack())
    assert changed.actual == original.actual
    assert result.baseline.status is TaxStatus.READY
    assert result.tax is not None
    assert result.tax.income.gross_income == Money.of(gross)
    assert result.tax.taxable_income == Money.of(taxable)
    assert result.tax.pit == Money.of(pit)


@pytest.mark.parametrize("period", ["actual", "forecast"])
@pytest.mark.parametrize("field", ["wages", "bonus", "outside_coverage"])
def test_c03_unknown_income_is_not_explicit_zero(period: str, field: str) -> None:
    request = base_input()
    request = replace(request, **{period: replace(getattr(request, period), **{field: None})})
    result = calculate_annual_estimate(request, production_pack())
    assert result.baseline.status is result.settlement_status is TaxStatus.REQUIRES_INPUT
    assert f"{period}.{field}" in result.baseline.missing_fact_ids
    assert result.tax is None
    assert result.annual_withholding is result.settlement_amount is None


@pytest.mark.parametrize(
    ("actual", "forecast", "kind", "amount", "missing"),
    [
        (45000, None, None, None, ("forecast.withholding",)),
        (None, 30000, None, None, ("actual.withholding",)),
        (None, None, None, None, ("actual.withholding", "forecast.withholding")),
        (45000, 0, SettlementKind.PAY_MORE, 36100, ()),
        (45000, 30000, SettlementKind.PAY_MORE, 6100, ()),
        (45000, 36100, SettlementKind.BALANCED, 0, ()),
        (45000, 45000, SettlementKind.REFUND, 8900, ()),
    ],
)
def test_c03_withholding_status_and_exact_settlement(
    actual: int | None,
    forecast: int | None,
    kind: SettlementKind | None,
    amount: int | None,
    missing: tuple[str, ...],
) -> None:
    request = base_input()
    result = calculate_annual_estimate(
        replace(
            request,
            actual=replace(
                request.actual, withholding=None if actual is None else Money.of(actual)
            ),
            forecast=replace(
                request.forecast, withholding=None if forecast is None else Money.of(forecast)
            ),
        ),
        production_pack(),
    )
    assert result.tax is not None
    assert result.tax.pit == Money.of(81100)
    assert result.withholding_missing_fact_ids == missing
    assert result.settlement_kind is kind
    if actual is None or forecast is None:
        assert result.settlement_status is TaxStatus.REQUIRES_INPUT
        assert result.annual_withholding is result.settlement_amount is None
    else:
        assert amount is not None
        assert result.settlement_status is TaxStatus.READY
        assert result.annual_withholding == Money.of(actual + forecast)
        assert result.settlement_amount == Money.of(amount)


def pvd_input() -> AnnualEstimateInput:
    request = base_input()
    pvd = PvdFacts(
        Money.of(30000), Money.of(600000), "Test fund", True, True, True, True, True, True
    )
    return replace(
        request, rights=replace(request.rights, pvd=pvd), pvd_forecast_single_employer=True
    )


def rmf_input(paid: str = "100000") -> AnnualEstimateInput:
    request = base_input()
    benefits = rmf_profile(paid).benefits
    rmf = replace(cast(RmfFacts, benefits.rmf), assessment_date=CUTOFF)
    return replace(
        request, rights=replace(request.rights, rmf=rmf, other_rights=benefits.other_rights)
    )


def fractional_input() -> AnnualEstimateInput:
    request = rmf_input("297150.01")
    return replace(
        request,
        actual=replace(request.actual, withholding=Money.of(30000)),
        forecast=replace(
            request.forecast, wages=Money.of("300500.01"), withholding=Money.of("927.50")
        ),
        rights=replace(request.rights, social_security_paid=Money.of(10500)),
    )


def test_c03_fractional_settlement_is_preserved() -> None:
    result = calculate_annual_estimate(fractional_input(), production_pack())
    assert result.tax is not None
    assert result.tax.pit == Money(Decimal("30927.50105"))
    assert result.settlement_kind is SettlementKind.PAY_MORE
    assert result.settlement_amount == Money(Decimal("0.00105"))


def test_c03_rejects_source_money_finer_than_satang() -> None:
    request = base_input()
    modified = replace(request, actual=replace(request.actual, withholding=Money(Decimal("0.001"))))
    with pytest.raises(AnnualEstimateInputError) as error:
        calculate_annual_estimate(modified, production_pack())
    assert error.value.fact_id == "actual.withholding"
    assert "0.001" not in str(error.value)


@pytest.mark.parametrize("assumption", [True, False, None])
def test_c03_pvd_forecast_requires_explicit_single_employer(assumption: bool | None) -> None:
    request = replace(pvd_input(), pvd_forecast_single_employer=assumption)
    result = calculate_annual_estimate(request, production_pack())
    if assumption is True:
        assert result.tax is not None
        assert result.tax.pit == Money.of(75100)
    elif assumption is False:
        assert result.baseline.status is TaxStatus.UNSUPPORTED
        assert "PVD_SINGLE_EMPLOYER_UNSUPPORTED" in result.baseline.reason_codes
    else:
        assert result.baseline.status is TaxStatus.REQUIRES_INPUT
        assert "pvd_forecast_single_employer" in result.baseline.missing_fact_ids


@pytest.mark.parametrize("forecast_wages", [None, Money.of(300500)])
def test_c03_pvd_wage_basis_checked_against_actual(forecast_wages: Money | None) -> None:
    request = pvd_input()
    pvd = replace(cast(PvdFacts, request.rights.pvd), wage_basis=Money.of(640001))
    request = replace(
        request,
        rights=replace(request.rights, pvd=pvd),
        forecast=replace(request.forecast, wages=forecast_wages),
    )
    with pytest.raises(PvdWageBasisError, match=r"pvd\.wage_basis") as error:
        calculate_annual_estimate(request, production_pack())
    assert "640001" not in str(error.value)


def test_c03_rmf_conditions_use_cutoff_and_reject_conflicts() -> None:
    request = rmf_input()
    result = calculate_annual_estimate(request, production_pack())
    assert result.tax is not None
    assert result.tax.pit == Money.of(62075)
    assert result.tax.rmf_conditions is not None
    assert result.tax.rmf_conditions.assessment_date == CUTOFF
    assert result.tax.rmf_conditions.reporting_status is RmfReportingStatus.NOT_YET_DUE
    rmf = cast(RmfFacts, request.rights.rmf)
    for conflict, fact_id in (
        (replace(rmf, assessment_date=date(2026, 10, 30)), "rmf.assessment_date"),
        (
            replace(
                rmf,
                reporting_status=RmfReportingStatus.CONFIRMED_SUBMITTED,
                report_confirmation=RmfReportConfirmation(
                    rmf.fund_name or "", rmf.amc_name or "", TaxYear(2026), Money.of(100001), CUTOFF
                ),
            ),
            "rmf.report_confirmation",
        ),
    ):
        with pytest.raises(RmfFactConflictError) as error:
            calculate_annual_estimate(
                replace(request, rights=replace(request.rights, rmf=conflict)), production_pack()
            )
        assert error.value.fact_id == fact_id


@pytest.mark.parametrize("periods", [(), ("actual",), ("forecast",), ("actual", "forecast")])
def test_c03_rights_and_status_precedence(periods: tuple[str, ...]) -> None:
    request = pvd_input()
    request = replace(
        request,
        rights=replace(request.rights, other_rights=rmf_input().rights.other_rights),
        actual=replace(request.actual, bonus=None, outside_coverage="actual" in periods),
        forecast=replace(request.forecast, outside_coverage="forecast" in periods),
    )
    result = calculate_annual_estimate(request, production_pack())
    expected = TaxStatus.ADVANCED_TAX_PATH_REQUIRED if periods else TaxStatus.UNSUPPORTED
    assert result.baseline.status is expected
    assert "PVD_RMF_COMBINED_UNSUPPORTED" in result.baseline.reason_codes
    for period in periods:
        assert f"{period.upper()}_OUTSIDE_COVERAGE" in result.baseline.reason_codes
    assert "actual.bonus" in result.baseline.missing_fact_ids
    assert result.tax is None
    assert result.settlement_amount is None


@pytest.mark.parametrize(
    ("changes", "fact_id"),
    [
        ({"cutoff_date": None}, "cutoff_date"),
        ({"confirmed_for": None}, "confirmed_for"),
        ({"cutoff_date": date(2026, 11, 30)}, "confirmed_for"),
        ({"rights": replace(base_input().rights, pvd=None)}, "pvd.employee_paid"),
        ({"rights": replace(base_input().rights, social_security_paid=None)}, "social_security"),
        (
            {"rights": replace(base_input().rights, retirement_contributions=None)},
            "retirement_usage",
        ),
    ],
)
def test_c03_unconfirmed_or_missing_required_facts(changes: dict[str, Any], fact_id: str) -> None:
    result = calculate_annual_estimate(replace(base_input(), **changes), production_pack())
    assert result.baseline.status is TaxStatus.REQUIRES_INPUT
    assert fact_id in result.baseline.missing_fact_ids
    assert result.tax is None


@pytest.mark.parametrize(
    ("changes", "fact_id"),
    [
        ({"tax_year": TaxYear(2025)}, "tax_year"),
        ({"cutoff_date": date(2027, 1, 1)}, "cutoff_date"),
        ({"cutoff_date": datetime(2026, 10, 31, tzinfo=UTC)}, "cutoff_date"),
        ({"confirmed_for": date(2025, 10, 31)}, "confirmed_for"),
        ({"forecast": replace(base_input().forecast, wages=Money.of(-987654))}, "forecast.wages"),
        (
            {"rights": replace(base_input().rights, mortgage_interest_paid=Money.of(-987654))},
            "mortgage_interest",
        ),
    ],
)
def test_c03_cutoff_and_period_conflicts(changes: dict[str, Any], fact_id: str) -> None:
    with pytest.raises(AnnualEstimateInputError) as error:
        calculate_annual_estimate(replace(base_input(), **changes), production_pack())
    assert error.value.fact_id == fact_id
    assert "987654" not in str(error.value)


def year_end_input() -> AnnualEstimateInput:
    end = date(2026, 12, 31)
    return replace(
        base_input(),
        cutoff_date=end,
        confirmed_for=end,
        actual=EstimatePeriod(Money.of(900500), Money.of(90000), Money.of(75000), False),
        forecast=EstimatePeriod(Money.zero(), Money.zero(), Money.zero(), False),
    )


@pytest.mark.parametrize("field", ["wages", "bonus", "withholding"])
def test_c03_year_end_requires_explicit_zero_in_forecast_fields(field: str) -> None:
    request = year_end_input()
    complete = calculate_annual_estimate(request, production_pack())
    assert complete.tax is not None
    assert complete.tax.pit == Money.of(81100)
    assert complete.settlement_amount == Money.of(6100)
    missing = calculate_annual_estimate(
        replace(request, forecast=replace(request.forecast, **{field: None})),
        production_pack(),
    )
    assert missing.settlement_amount is None
    assert (missing.tax is not None) == (field == "withholding")
    positive_forecast: dict[str, Any] = {field: Money.of("0.01")}
    with pytest.raises(AnnualEstimateInputError) as error:
        calculate_annual_estimate(
            replace(request, forecast=replace(request.forecast, **positive_forecast)),
            production_pack(),
        )
    assert error.value.fact_id == f"forecast.{field}"
