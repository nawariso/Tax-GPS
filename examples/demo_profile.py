"""Validated local-demo inputs; no tax or financial policy is implemented here."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import cast

from tax_gps.core.decimal_context import EXACT
from tax_gps.core.money import Money
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialProfile,
    ProtectionProfile,
)
from tax_gps.profile.models import Child, ExistingTaxBenefits, Parent

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
        raise ValueError(f"{name}: enter a known nonnegative THB amount with at most two decimals")
    return Money.of(value)


def _strings(value: object, fields: frozenset[str], name: str) -> dict[str, str]:
    if (
        not isinstance(value, dict)
        or set(value) != fields
        or not all(isinstance(v, str) for v in value.values())
    ):
        raise ValueError(f"{name}: supply exactly the documented string fields")
    return cast(dict[str, str], value)


def _boolean(value: str, name: str) -> bool:
    if value not in {"true", "false"}:
        raise ValueError(f"{name}: ยังไม่ทราบสิทธิหรือข้อเท็จจริง จึงยังไม่เผยแพร่ผลคำนวณ")
    return value == "true"


def _integer(value: str, name: str) -> int:
    if not re.fullmatch(r"[0-9]{1,4}", value):
        raise ValueError(f"{name}: use an explicit integer")
    return int(value)


def _parents(items: list[object]) -> tuple[Parent, ...]:
    result = []
    for item in items:
        entry = _strings(item, frozenset({"relationship", "eligible"}), "parent")
        result.append(
            Parent(entry["relationship"], _boolean(entry["eligible"], "parent eligibility"))
        )
    return tuple(result)


def _children(items: list[object]) -> tuple[Child, ...]:
    result = []
    for item in items:
        entry = _strings(
            item, frozenset({"child_id", "order", "birth_year", "legally_eligible"}), "child"
        )
        result.append(
            Child(
                entry["child_id"],
                _boolean(entry["legally_eligible"], "child eligibility"),
                _integer(entry["birth_year"], "birth year"),
                order=_integer(entry["order"], "legal child order"),
            )
        )
    return tuple(result)


def _debts(items: list[object]) -> tuple[Debt, ...]:
    result = []
    for item in items:
        entry = _strings(
            item,
            frozenset(
                {"debt_id", "category", "balance", "apr_percent", "minimum_payment", "secured"}
            ),
            "debt",
        )
        apr = entry["apr_percent"]
        if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,4})?", apr):
            raise ValueError(
                "debt APR: enter a known nonnegative percentage, at most four decimals"
            )
        result.append(
            Debt(
                entry["debt_id"],
                DebtCategory(entry["category"]),
                amount(entry["balance"], "debt balance"),
                EXACT.divide(Decimal(apr), Decimal(100)),
                amount(entry["minimum_payment"], "minimum payment"),
                _boolean(entry["secured"], "secured debt"),
            )
        )
    return tuple(result)


def _commitments(items: list[object]) -> tuple[CommittedCashNeed, ...]:
    result = []
    for item in items:
        entry = _strings(
            item,
            frozenset({"need_id", "amount", "due_date", "mandatory", "description"}),
            "commitment",
        )
        result.append(
            CommittedCashNeed(
                entry["need_id"],
                amount(entry["amount"], "committed cash"),
                date.fromisoformat(entry["due_date"]),
                _boolean(entry["mandatory"], "mandatory payment"),
                entry["description"],
            )
        )
    return tuple(result)


def parse_profile(
    value: object, *, assets: Money | None, expenses: Money | None, social: Money
) -> tuple[ExistingTaxBenefits, FinancialProfile]:
    if not isinstance(value, dict) or set(value) != SCALARS | LISTS:
        raise ValueError("Supply exactly the documented extended profile fields")
    scalars = _strings({key: value[key] for key in SCALARS}, SCALARS, "profile")
    if not all(isinstance(value[key], list) for key in LISTS):
        raise ValueError("Profile record collections must be explicit lists; [] means no records")
    lists = {key: cast(list[object], value[key]) for key in LISTS}
    if not amount(scalars["other_income"], "other income").is_zero():
        raise ValueError("ยังไม่รองรับรายได้ประเภทอื่น ไม่เผยแพร่ภาษีเฉพาะเงินเดือนที่ตกหล่นรายได้")
    if not amount(scalars["retirement_usage"], "retirement contributions").is_zero():
        raise ValueError("ยังไม่รองรับโปรไฟล์ที่มีเงินออมเกษียณ: core ยังไม่หักรายการนี้จากฐานภาษี")
    benefits = ExistingTaxBenefits(
        personal_eligible=_boolean(scalars["personal_eligible"], "personal eligibility"),
        social_security_paid=social,
        parents=_parents(lists["parents"]),
        children=_children(lists["children"]),
        mortgage_interest_paid=amount(scalars["mortgage_interest"], "mortgage interest"),
        mortgage_eligible=_boolean(scalars["mortgage_eligible"], "mortgage eligibility"),
    )
    financial = FinancialProfile(
        liquid_assets=assets,
        monthly_essential_expenses=expenses,
        debts=_debts(lists["debts"]),
        committed_cash_needs=_commitments(lists["commitments"]),
        protection=ProtectionProfile(
            required_life_coverage=amount(scalars["required_coverage"], "required coverage")
            if scalars["required_coverage"] != ""
            else None,
            existing_life_coverage=amount(scalars["existing_coverage"], "existing coverage")
            if scalars["existing_coverage"] != ""
            else None,
        ),
    )
    return benefits, financial
