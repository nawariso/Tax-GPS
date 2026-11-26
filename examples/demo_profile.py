"""Validated local-demo inputs; no tax or financial policy is implemented here."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import cast

from examples.demo_errors import DemoInputError, field_label, input_scope, invalid_input
from examples.pvd_adapter import parse_pvd_profile
from examples.rmf_adapter import parse_rmf_profile
from tax_gps.calculation.annual_estimate import AnnualEstimateRights
from tax_gps.core.decimal_context import EXACT
from tax_gps.core.money import Money
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialProfile,
    ProtectionProfile,
)
from tax_gps.profile.models import (
    Child,
    ExistingTaxBenefits,
    Parent,
    RetirementContribution,
    parent_eligibility_fact_id,
)

SCALARS = frozenset(
    {
        "personal_eligible",
        "mortgage_interest",
        "mortgage_eligible",
        "required_coverage",
        "existing_coverage",
        "other_income",
        "retirement_usage",
    }
)
LISTS = frozenset({"parents", "children", "debts", "commitments"})


def amount(value: object, name: str) -> Money:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", value):
        raise invalid_input(name)
    return Money.of(value)


def _strings(value: object, fields: frozenset[str], name: str) -> dict[str, str]:
    if (
        not isinstance(value, dict)
        or set(value) != fields
        or not all(isinstance(v, str) for v in value.values())
    ):
        raise invalid_input(name)
    return cast(dict[str, str], value)


def _boolean(value: str, name: str) -> bool:
    if value not in {"true", "false"}:
        reason = (
            "PARENT_ELIGIBILITY_REQUIRED" if name.startswith("parent") else "ELIGIBILITY_REQUIRED"
        )
        raise DemoInputError(
            f"{field_label(name)}: ยังไม่ทราบสิทธิหรือข้อเท็จจริง จึงยังไม่เผยแพร่ผลคำนวณ",
            reason_codes=(reason,),
            missing_fact_ids=(name,),
        )
    return value == "true"


def optional_boolean(value: str, name: str) -> bool | None:
    if value in {"", "unknown"}:
        return None
    if value not in {"true", "false"}:
        raise invalid_input(name)
    return value == "true"


def optional_amount(value: str, name: str) -> Money | None:
    return None if value == "" else amount(value, name)


def _integer(value: str, name: str) -> int:
    if not re.fullmatch(r"[0-9]{1,4}", value):
        raise invalid_input(name)
    return int(value)


def _parents(items: list[object], *, allow_unknown: bool = False) -> tuple[Parent, ...]:
    result = []
    parse_eligible = optional_boolean if allow_unknown else _boolean
    for index, item in enumerate(items):
        row = f"parents[{index}]"
        with input_scope(row):
            entry = _strings(item, frozenset({"relationship", "eligible"}), f"parents[{index}]")
            result.append(
                Parent(
                    entry["relationship"],
                    parse_eligible(
                        entry["eligible"], parent_eligibility_fact_id(entry["relationship"], index)
                    ),
                )
            )
    return tuple(result)


def _children(items: list[object], *, unconfirmed: list[int] | None = None) -> tuple[Child, ...]:
    result = []
    for index, item in enumerate(items):
        row = f"children[{index}]"
        with input_scope(row):
            entry = _strings(
                item, frozenset({"child_id", "order", "birth_year", "legally_eligible"}), row
            )
            if unconfirmed is not None and entry["legally_eligible"] in {"unknown", ""}:
                unconfirmed.append(index)
                continue
            result.append(
                Child(
                    entry["child_id"],
                    _boolean(entry["legally_eligible"], f"{row}.legally_eligible"),
                    _integer(entry["birth_year"], f"{row}.birth_year"),
                    order=_integer(entry["order"], f"{row}.order"),
                )
            )
    return tuple(result)


def _debts(items: list[object]) -> tuple[Debt, ...]:
    result = []
    for index, item in enumerate(items):
        row = f"debts[{index}]"
        with input_scope(row):
            entry = _strings(
                item,
                frozenset(
                    {"debt_id", "category", "balance", "apr_percent", "minimum_payment", "secured"}
                ),
                row,
            )
            apr = entry["apr_percent"]
            if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,4})?", apr):
                raise invalid_input(f"{row}.apr_percent")
            result.append(
                Debt(
                    entry["debt_id"],
                    DebtCategory(entry["category"]),
                    amount(entry["balance"], f"{row}.balance"),
                    EXACT.divide(Decimal(apr), Decimal(100)),
                    amount(entry["minimum_payment"], f"{row}.minimum_payment"),
                    _boolean(entry["secured"], f"{row}.secured"),
                )
            )
    return tuple(result)


def _commitments(items: list[object]) -> tuple[CommittedCashNeed, ...]:
    result = []
    for index, item in enumerate(items):
        row = f"commitments[{index}]"
        with input_scope(row):
            entry = _strings(
                item,
                frozenset({"need_id", "amount", "due_date", "mandatory", "description"}),
                row,
            )
            result.append(
                CommittedCashNeed(
                    entry["need_id"],
                    amount(entry["amount"], f"{row}.amount"),
                    date.fromisoformat(entry["due_date"]),
                    _boolean(entry["mandatory"], f"{row}.mandatory"),
                    entry["description"],
                )
            )
    return tuple(result)


def _parse_profile(
    value: object,
    *,
    assets: Money | None,
    expenses: Money | None,
    social: Money,
    assessment_date: date,
) -> tuple[ExistingTaxBenefits, FinancialProfile]:
    groups = {"pvd", "other_rights", "fund_history", "rmf"}
    if not isinstance(value, dict) or set(value) - groups != SCALARS | LISTS:
        raise invalid_input("profile")
    scalars = _strings({key: value[key] for key in SCALARS}, SCALARS, "profile")
    if not all(isinstance(value[key], list) for key in LISTS):
        raise invalid_input("profile")
    lists = {key: cast(list[object], value[key]) for key in LISTS}
    unknown = {
        "other_income": ("OTHER_INCOME_INPUT_REQUIRED", "ยังไม่ทราบรายได้อื่น"),
        "retirement_usage": ("RETIREMENT_INPUT_REQUIRED", "ยังไม่ทราบเงินออมเกษียณ"),
    }
    blank = [name for name in unknown if scalars[name] == ""]
    if blank:
        raise DemoInputError(
            " · ".join(unknown[name][1] for name in blank) + " โปรดตรวจสอบรายการนอกขอบเขต",
            reason_codes=tuple(unknown[name][0] for name in blank),
            missing_fact_ids=tuple(blank),
        )
    if not amount(scalars["other_income"], "other_income").is_zero():
        raise DemoInputError(
            "ยังไม่รองรับรายได้ประเภทอื่น ไม่เผยแพร่ภาษีเฉพาะเงินเดือนที่ตกหล่นรายได้",
            code="BASELINE_NOT_READY",
            status="ADVANCED_TAX_PATH_REQUIRED",
            reason_codes=("UNSUPPORTED_INCOME",),
        )
    retirement = amount(scalars["retirement_usage"], "retirement_usage")

    pvd, other_rights, history = parse_pvd_profile(value)
    benefits = ExistingTaxBenefits(
        pvd=pvd,
        rmf=parse_rmf_profile(value.get("rmf"), assessment_date=assessment_date),
        other_rights=other_rights,
        fund_history=history,
        personal_eligible=_boolean(scalars["personal_eligible"], "personal_eligible"),
        social_security_paid=social,
        parents=_parents(lists["parents"]),
        children=_children(lists["children"]),
        mortgage_interest_paid=amount(scalars["mortgage_interest"], "mortgage_interest"),
        mortgage_eligible=_boolean(scalars["mortgage_eligible"], "mortgage_eligible"),
        retirement_contributions=(RetirementContribution("UNCLASSIFIED", retirement),)
        if retirement.is_positive()
        else (),
    )
    financial = FinancialProfile(
        liquid_assets=assets,
        monthly_essential_expenses=expenses,
        debts=_debts(lists["debts"]),
        committed_cash_needs=_commitments(lists["commitments"]),
        protection=ProtectionProfile(
            required_life_coverage=amount(scalars["required_coverage"], "required_coverage")
            if scalars["required_coverage"] != ""
            else None,
            existing_life_coverage=amount(scalars["existing_coverage"], "existing_coverage")
            if scalars["existing_coverage"] != ""
            else None,
        ),
    )
    return benefits, financial


def parse_profile(
    value: object,
    *,
    assets: Money | None,
    expenses: Money | None,
    social: Money,
    assessment_date: date,
) -> tuple[ExistingTaxBenefits, FinancialProfile]:
    with input_scope("profile"):
        return _parse_profile(
            value, assets=assets, expenses=expenses, social=social, assessment_date=assessment_date
        )


def parse_annual_rights(
    value: object, *, social: Money | None, cutoff: date | None
) -> AnnualEstimateRights:
    scalar_fields = SCALARS - {"required_coverage", "existing_coverage", "other_income"}
    groups = {"pvd", "other_rights", "fund_history", "rmf"}
    if not isinstance(value, dict) or set(value) - groups != scalar_fields | {
        "parents",
        "children",
    }:
        raise invalid_input("profile")
    scalars = _strings({key: value[key] for key in scalar_fields}, scalar_fields, "profile")
    parents, children = value["parents"], value["children"]
    if not isinstance(parents, list) or not isinstance(children, list):
        raise invalid_input("profile")
    pvd, other_rights, history = parse_pvd_profile(value)
    retirement = optional_amount(scalars["retirement_usage"], "retirement_usage")
    retirement_contributions = None
    if retirement is not None:
        retirement_contributions = (
            (RetirementContribution("UNCLASSIFIED", retirement),)
            if retirement.is_positive()
            else ()
        )
    unconfirmed_children: list[int] = []
    parsed_children = _children(children, unconfirmed=unconfirmed_children)
    return AnnualEstimateRights(
        parents=_parents(parents, allow_unknown=True),
        retirement_contributions=retirement_contributions,
        pvd=pvd,
        other_rights=other_rights,
        fund_history=history,
        rmf=parse_rmf_profile(value.get("rmf"), assessment_date=cutoff),
        children=parsed_children,
        personal_eligible=optional_boolean(scalars["personal_eligible"], "personal_eligible"),
        social_security_paid=social,
        mortgage_interest_paid=optional_amount(scalars["mortgage_interest"], "mortgage_interest"),
        mortgage_eligible=optional_boolean(scalars["mortgage_eligible"], "mortgage_eligible"),
        unconfirmed_children=tuple(unconfirmed_children),
    )
