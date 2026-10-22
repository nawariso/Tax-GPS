"""Validated local-demo inputs; no tax or financial policy is implemented here."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import cast

from examples.demo_errors import DemoInputError, field_label, input_scope, invalid_input
from examples.pvd_adapter import parse_pvd_profile
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


def _integer(value: str, name: str) -> int:
    if not re.fullmatch(r"[0-9]{1,4}", value):
        raise invalid_input(name)
    return int(value)


def _parents(items: list[object]) -> tuple[Parent, ...]:
    result = []
    for index, item in enumerate(items):
        row = f"parents[{index}]"
        with input_scope(row):
            entry = _strings(item, frozenset({"relationship", "eligible"}), f"parents[{index}]")
            result.append(
                Parent(
                    entry["relationship"],
                    _boolean(
                        entry["eligible"], parent_eligibility_fact_id(entry["relationship"], index)
                    ),
                )
            )
    return tuple(result)


def _children(items: list[object]) -> tuple[Child, ...]:
    result = []
    for index, item in enumerate(items):
        row = f"children[{index}]"
        with input_scope(row):
            entry = _strings(
                item, frozenset({"child_id", "order", "birth_year", "legally_eligible"}), row
            )
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
    value: object, *, assets: Money | None, expenses: Money | None, social: Money
) -> tuple[ExistingTaxBenefits, FinancialProfile]:
    groups = {"pvd", "other_rights", "fund_history"}
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
    value: object, *, assets: Money | None, expenses: Money | None, social: Money
) -> tuple[ExistingTaxBenefits, FinancialProfile]:
    with input_scope("profile"):
        return _parse_profile(value, assets=assets, expenses=expenses, social=social)
