"""C02A-AC01..05: explicit facts and reviewed normal PVD baseline."""

import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest

from tax_gps.calculation.models import TaxStatus
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import calculate_tax
from tax_gps.profile.models import ExistingTaxBenefits, IncomeProfile, OpportunityFacts, UserProfile
from tests.support.policy import production_pack


def test_c02a_missing_facts_are_not_zero() -> None:
    user = UserProfile(
        "unknown",
        "2",
        TaxYear(2026),
        IncomeProfile(Money.of(200000)),
        opportunity_facts=OpportunityFacts(shared_limit_usage=()),
    )
    state = calculate_tax(user, production_pack())
    assert state.status is TaxStatus.REQUIRES_INPUT
    assert state.pit is None
    assert state.taxable_income is None
    assert "pvd.employee_paid" in state.missing_fact_ids


def normal_profile(paid: str = "27000", wage: str = "180000") -> UserProfile:
    from tax_gps.profile.pvd import FundHistoryFacts, OtherRightsFacts, PvdFacts  # noqa: PLC0415

    return UserProfile(
        "normal",
        "2",
        TaxYear(2026),
        IncomeProfile(Money.of(wage)),
        ExistingTaxBenefits(
            pvd=PvdFacts(
                Money.of(paid), Money.of(wage), "Test fund", True, True, True, True, True, True
            ),
            other_rights=OtherRightsFacts(**{f.name: False for f in fields(OtherRightsFacts)}),
            fund_history=FundHistoryFacts(**{f.name: False for f in fields(FundHistoryFacts)}),
        ),
        OpportunityFacts(shared_limit_usage=()),
    )


def test_c02a_zero_does_not_add_employer_restrictions() -> None:
    user = normal_profile("0")
    assert user.benefits.pvd is not None
    user = replace(
        user,
        benefits=replace(
            user.benefits, pvd=replace(user.benefits.pvd, single_employer=False, single_fund=False)
        ),
    )
    assert calculate_tax(user, production_pack()).status is TaxStatus.READY


@pytest.mark.parametrize("group", ["other_rights", "fund_history"])
@pytest.mark.parametrize("value", [None, True])
def test_c02a_unknown_and_positive_inventory_precedence(group: str, value: bool | None) -> None:
    user = normal_profile("0")
    assert user.benefits.pvd is not None
    facts = getattr(user.benefits, group)
    for item in fields(facts):
        changed = replace(
            user, benefits=replace(user.benefits, **{group: replace(facts, **{item.name: value})})
        )
        state = calculate_tax(changed, production_pack())
        assert state.status is (
            TaxStatus.REQUIRES_INPUT if value is None else TaxStatus.UNSUPPORTED
        )
        assert state.pit is None
        assert state.taxable_income is None
        if value is None:
            assert f"{group}.{item.name}" in state.missing_fact_ids


@pytest.mark.parametrize(
    "name",
    [
        "registered_fund",
        "credited_in_tax_year",
        "single_employer",
        "single_fund",
        "ordinary_article_rate",
        "normal_remittance",
        "fund_name",
        "wage_basis",
    ],
)
def test_c02a_actual_credit_and_normal_remittance(name: str) -> None:
    user = normal_profile()
    assert user.benefits.pvd is not None
    state = calculate_tax(
        replace(
            user, benefits=replace(user.benefits, pvd=replace(user.benefits.pvd, **{name: None}))
        ),
        production_pack(),
    )
    assert state.status is TaxStatus.REQUIRES_INPUT
    assert f"pvd.{name}" in state.missing_fact_ids
    if name not in ("fund_name", "wage_basis"):
        cast_false: Any = False
        state = calculate_tax(
            replace(
                user,
                benefits=replace(
                    user.benefits, pvd=replace(user.benefits.pvd, **{name: cast_false})
                ),
            ),
            production_pack(),
        )
        assert state.status is TaxStatus.UNSUPPORTED
        assert f"PVD_{name.upper()}_UNSUPPORTED" in state.reason_codes


@pytest.mark.parametrize(
    ("paid", "status"),
    [
        ("3600", TaxStatus.READY),
        ("27000", TaxStatus.READY),
        ("3599", TaxStatus.UNSUPPORTED),
        ("27001", TaxStatus.UNSUPPORTED),
    ],
)
def test_c02a_normal_rate_and_conflicting_wage(paid: str, status: TaxStatus) -> None:
    assert calculate_tax(normal_profile(paid), production_pack()).status is status


CASES = json.loads(
    Path("docs/policy-evidence/2026-10-22/c02a-scope/normal-pvd-reference.json").read_text()
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_c02a_reference_split_and_order(case: dict[str, str]) -> None:
    user = normal_profile(case["employee_paid"], case["salary"])
    user = replace(
        user, benefits=replace(user.benefits, social_security_paid=Money.of(case["sso"]))
    )
    state = calculate_tax(user, production_pack())
    assert state.status is TaxStatus.READY
    assert state.pvd is not None
    for key in ("exemption", "allowance", "excess"):
        assert getattr(state.pvd, key) == Money.of(case[key])
    assert state.expenses.section_40_1 == Money.of(case["expense"])
    assert state.taxable_income == Money.of(case["taxable"])
    assert state.pit == Money.of(case["pit"])
