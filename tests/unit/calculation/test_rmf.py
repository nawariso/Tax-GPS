"""AC05–07: independent missing/discrepant reporting and unsafe helper calls."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.calculation.rmf import assess_rmf, build_rmf_conditions, calculate_rmf
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.profile.rmf import (
    RmfFactConflictError,
    RmfFacts,
    RmfReportConfirmation,
    RmfReportingStatus,
)
from tests.acceptance.test_c02b_rmf import rmf_profile
from tests.support.policy import production_pack


@pytest.mark.parametrize(("paid", "income"), [("-1", "0"), ("0", "-1")])
def test_negative_calculation(paid: str, income: str) -> None:
    with pytest.raises(InvalidValueError):
        calculate_rmf(Money.of(paid), Money.of(income), production_pack())


def test_reporting_and_conditions_guards() -> None:
    pack = production_pack()
    year = TaxYear(2026)
    f = rmf_profile().benefits.rmf
    assert f is not None
    with pytest.raises(InvalidValueError):
        build_rmf_conditions(RmfFacts(), year, pack)
    assert assess_rmf(
        True, replace(f, reporting_status=RmfReportingStatus.DISCREPANCY_OR_CORRECTION), year, pack
    )[0] == ("RMF_REPORTING_DISCREPANCY_UNSUPPORTED",)
    assert assess_rmf(
        True, replace(f, reporting_status=RmfReportingStatus.CONFIRMED_SUBMITTED), year, pack
    )[1] == ("rmf.report_confirmation",)
    with pytest.raises(RmfFactConflictError):
        assess_rmf(True, replace(f, assessment_date=date(2027, 1, 15)), year, pack)
    receipt = RmfReportConfirmation(
        "กองทุนทดสอบ", "บลจ.ทดสอบ", year, Money.of("100000"), date(2026, 1, 1)
    )
    with pytest.raises(RmfFactConflictError):
        assess_rmf(
            True,
            replace(
                f,
                reporting_status=RmfReportingStatus.CONFIRMED_SUBMITTED,
                report_confirmation=receipt,
            ),
            year,
            pack,
        )
