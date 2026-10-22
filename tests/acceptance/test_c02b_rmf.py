"""C02B AC01–07,09: explicit dated RMF facts and independent reference amounts."""

import json
from dataclasses import fields, replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from tax_gps.calculation.models import TaxStatus
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import calculate_tax
from tax_gps.profile.models import UserProfile
from tax_gps.profile.pvd import OtherRightsFacts
from tax_gps.profile.rmf import (
    RmfFactConflictError,
    RmfFacts,
    RmfReportConfirmation,
    RmfReportingStatus,
)
from tests.acceptance.test_c02a_pvd import normal_profile
from tests.support.policy import production_pack


def rmf_profile(paid: str = "100000") -> UserProfile:
    profile = normal_profile(paid="0")
    facts = RmfFacts(
        own_purchase_paid=Money.of(paid),
        fund_name="กองทุนทดสอบ",
        amc_name="บลจ.ทดสอบ",
        first_purchase_date=date(2026, 1, 2),
        assessment_date=date(2026, 10, 22),
        reporting_status=RmfReportingStatus.NOT_YET_DUE,
        ordinary_own_purchase_confirmed=True,
        single_fund=True,
        single_amc=True,
        first_ever_purchase_in_tax_year=True,
        paid_through_assessment_date=True,
        declaration_completed=True,
        no_distributions_or_borrowing=True,
        no_known_reporting_problem=True,
        future_obligations_acknowledged=True,
    )
    return replace(
        profile,
        benefits=replace(
            profile.benefits,
            rmf=facts,
            other_rights=replace(cast(OtherRightsFacts, profile.benefits.other_rights), rmf=True),
        ),
    )


def test_c02b_presence_and_missing_facts() -> None:
    p = rmf_profile()
    pack = production_pack()
    assert calculate_tax(p, pack).status is TaxStatus.READY
    assert (
        calculate_tax(replace(p, benefits=replace(p.benefits, rmf=None)), pack).status
        is TaxStatus.REQUIRES_INPUT
    )
    for present in (True, False):
        paid = "0" if present else "1"
        q = replace(
            p,
            benefits=replace(
                p.benefits,
                other_rights=replace(cast(OtherRightsFacts, p.benefits.other_rights), rmf=present),
                rmf=replace(cast(RmfFacts, p.benefits.rmf), own_purchase_paid=Money.of(paid)),
            ),
        )
        with pytest.raises(RmfFactConflictError):
            calculate_tax(q, pack)
    q = replace(
        p,
        benefits=replace(
            p.benefits,
            other_rights=replace(cast(OtherRightsFacts, p.benefits.other_rights), rmf=None),
        ),
    )
    assert "other_rights.rmf" in calculate_tax(q, pack).missing_fact_ids
    q = replace(p, benefits=replace(p.benefits, rmf=None, pvd=normal_profile().benefits.pvd))
    assert calculate_tax(q, pack).status is TaxStatus.UNSUPPORTED


@pytest.mark.parametrize(
    "field", [f.name for f in fields(RmfFacts) if f.name != "report_confirmation"]
)
def test_c02b_unknown_conditions(field: str) -> None:
    p = rmf_profile()
    p = replace(
        p,
        benefits=replace(p.benefits, rmf=replace(cast(RmfFacts, p.benefits.rmf), **{field: None})),
    )
    state = calculate_tax(p, production_pack())
    assert state.status is TaxStatus.REQUIRES_INPUT
    assert f"rmf.{field}" in state.missing_fact_ids
    assert state.pit is None
    assert state.rmf is None


@pytest.mark.parametrize(
    "field",
    [
        "ordinary_own_purchase_confirmed",
        "single_fund",
        "single_amc",
        "first_ever_purchase_in_tax_year",
        "paid_through_assessment_date",
        "declaration_completed",
        "no_distributions_or_borrowing",
        "no_known_reporting_problem",
        "future_obligations_acknowledged",
    ],
)
def test_c02b_false_conditions(field: str) -> None:
    p = rmf_profile()
    p = replace(
        p,
        benefits=replace(
            p.benefits,
            rmf=replace(cast(RmfFacts, p.benefits.rmf), **cast(dict[str, Any], {field: False})),
        ),
    )
    assert calculate_tax(p, production_pack()).status is TaxStatus.UNSUPPORTED


def test_c02b_dates_and_report_confirmation() -> None:
    p = rmf_profile()
    f = p.benefits.rmf
    assert f is not None
    assert f.fund_name is not None
    assert f.amc_name is not None
    assert f.own_purchase_paid is not None
    pack = production_pack()
    receipt = RmfReportConfirmation(
        f.fund_name, f.amc_name, TaxYear(2026), f.own_purchase_paid, date(2026, 10, 1)
    )
    confirmed = replace(
        f, reporting_status=RmfReportingStatus.CONFIRMED_SUBMITTED, report_confirmation=receipt
    )
    state = calculate_tax(replace(p, benefits=replace(p.benefits, rmf=confirmed)), pack)
    assert state.rmf_conditions is not None
    assert state.rmf_conditions.report_confirmation == receipt
    assert "RMF_AMC_REPORTING_PENDING" not in state.rmf_conditions.obligation_codes
    for name, value in [
        ("fund_name", "other"),
        ("amc_name", "other"),
        ("tax_year", TaxYear(2025)),
        ("cumulative_paid", Money.of("1")),
        ("confirmed_on", date(2026, 12, 1)),
    ]:
        bad = replace(
            confirmed, report_confirmation=replace(receipt, **cast(dict[str, Any], {name: value}))
        )
        with pytest.raises(RmfFactConflictError):
            calculate_tax(replace(p, benefits=replace(p.benefits, rmf=bad)), pack)
    for bad in (
        replace(f, report_confirmation=receipt),
        replace(f, first_purchase_date=date(2025, 1, 1)),
        replace(f, first_purchase_date=date(2026, 12, 1)),
        replace(f, assessment_date=date(2027, 1, 1)),
    ):
        with pytest.raises(RmfFactConflictError):
            calculate_tax(replace(p, benefits=replace(p.benefits, rmf=bad)), pack)
    state = calculate_tax(p, pack)
    assert state.rmf_conditions is not None
    assert len(state.rmf_conditions.obligation_codes) == 5
    assert (
        state.output_hash
        != calculate_tax(
            replace(
                p, benefits=replace(p.benefits, rmf=replace(f, assessment_date=date(2026, 10, 23)))
            ),
            pack,
        ).output_hash
    )


@pytest.mark.parametrize(
    "case",
    json.loads(
        Path("docs/policy-evidence/2026-10-22/c02b-scope/rmf-reference.json").read_text(
            encoding="utf-8"
        )
    )["cases"],
)
def test_c02b_reference(case: dict[str, str]) -> None:
    p = rmf_profile(case["paid"])
    zero = Money.of(case["paid"]) == Money.zero()
    p = replace(
        p,
        income=replace(p.income, section_40_1=Money.of(case["salary"])),
        benefits=replace(
            p.benefits,
            social_security_paid=Money.of(case["sso"]),
            other_rights=replace(cast(OtherRightsFacts, p.benefits.other_rights), rmf=not zero),
        ),
    )
    s = calculate_tax(p, production_pack())
    assert s.status is TaxStatus.READY
    assert s.expenses.section_40_1 == Money(Decimal(case["expense"]))
    assert s.taxable_income == Money(Decimal(case["taxable"]))
    assert s.pit == Money(Decimal(case["pit"]))
    if not zero:
        assert s.rmf is not None
        for name in ("percentage_cap", "claimed", "excess"):
            assert getattr(s.rmf, name) == Money(Decimal(case[name]))
        assert s.rmf.qualifying_paid == Money.of(case["paid"])
    else:
        assert s.rmf is None
        assert s.rmf_conditions is None
