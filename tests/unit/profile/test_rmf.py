"""AC01/09: typed immutable facts reject malformed inputs without reflecting them."""

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from typing import Any

import pytest

from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.profile.rmf import RmfFactConflictError, RmfFacts, RmfReportConfirmation


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fund_name": " "},
        {"amc_name": 3},
        {"own_purchase_paid": Money.of("-1")},
        {"own_purchase_paid": "123-private"},
        {"single_fund": 1},
        {"first_purchase_date": datetime(2026, 1, 1, tzinfo=UTC)},
        {"assessment_date": "2026-01-01"},
        {"reporting_status": "NOT_YET_DUE"},
        {"report_confirmation": {}},
    ],
)
def test_rmf_rejects_untyped_or_invalid_facts(kwargs: dict[str, Any]) -> None:
    with pytest.raises(InvalidValueError):
        RmfFacts(**kwargs)


def test_confirmation_year_and_immutability() -> None:
    with pytest.raises(InvalidValueError):
        RmfReportConfirmation("fund", "amc", 2026, Money.of("1"), date(2026, 1, 1))  # type: ignore[arg-type]
    facts = RmfFacts()
    assert all(value is None for value in facts.to_dict().values())
    with pytest.raises(FrozenInstanceError):
        facts.fund_name = "other"  # type: ignore[misc]
    assert "private" not in str(RmfFactConflictError("private"))
    receipt = RmfReportConfirmation("fund", "amc", TaxYear(2026), Money.of("1"), date(2026, 1, 1))
    assert receipt.to_dict()["tax_year"] == 2026
