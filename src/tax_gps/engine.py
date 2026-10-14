"""Application service orchestrating the supported deterministic salary-only path."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from tax_gps.calculation.models import (
    AllowanceCalculation,
    CalculationStep,
    CalculationTrace,
    ExistingRight,
    ExpenseCalculation,
    IncomeCalculation,
    TaxState,
    TaxStatus,
)
from tax_gps.calculation.readiness import assess_baseline
from tax_gps.calculation.rules import (
    allowance_for_children,
    allowance_for_parents,
    calculate_progressive_pit,
    calculate_section_40_1_expense,
    deductible_mortgage_interest,
    personal_allowance,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.policy import rule_ids
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import RuleSource
from tax_gps.profile.models import UserProfile

ENGINE_VERSION = "tax-gps-core/0.2.0"


def _step(
    *,
    step_id: str,
    description: str,
    rule_id: str,
    input_amount: Money,
    output_amount: Money,
    pack: ActivatedRulePack,
) -> CalculationStep:
    source_id = cast(str, pack.pack.rule(rule_id).source_id)
    return CalculationStep(step_id, description, rule_id, source_id, input_amount, output_amount)


def _sources(rule_ids_used: tuple[str, ...], pack: ActivatedRulePack) -> tuple[RuleSource, ...]:
    """Resolve applied-rule sources in first-reference order.

    Each rule contributes its primary source followed by supplementary sources in Rule Pack
    order. ``seen`` is used only for membership checks; serialized order never depends on set
    iteration.
    """
    sources_by_id = {source.source_id: source for source in pack.pack.sources}
    seen: set[str] = set()
    ordered: list[RuleSource] = []
    for rule_id in rule_ids_used:
        rule = pack.pack.rule(rule_id)
        source_ids = (cast(str, rule.source_id), *rule.supplementary_source_ids)
        for source_id in source_ids:
            if source_id not in seen:
                ordered.append(sources_by_id[source_id])
                seen.add(source_id)
    return tuple(ordered)


def calculate_tax(
    profile: UserProfile, pack: ActivatedRulePack, *, engine_version: str = ENGINE_VERSION
) -> TaxState:
    if engine_version != ENGINE_VERSION:
        raise ValueError("engine version is not implemented by this artifact")
    if profile.tax_year != pack.pack.tax_year:
        raise ValueError("profile tax year must match the activated rule pack")
    material_unsupported = tuple(
        item for item in profile.income.unsupported if item.amount.is_positive()
    )
    readiness = assess_baseline(profile)
    if readiness.status is not TaxStatus.READY:
        reasons = tuple(
            f"material unsupported income: {item.category}" for item in material_unsupported
        )
        state = TaxState(
            readiness.status,
            profile.tax_year,
            IncomeCalculation(profile.income.section_40_1),
            ExpenseCalculation(Money.zero()),
            AllowanceCalculation(
                Money.zero(), Money.zero(), Money.zero(), Money.zero(), Money.zero()
            ),
            None,
            None,
            None,
            (),
            (),
            CalculationTrace(()),
            (),
            (),
            pack.rule_pack_id,
            pack.version,
            engine_version,
            reasons,
            "",
            pack,
            reason_codes=readiness.reason_codes,
            missing_fact_ids=readiness.missing_fact_ids,
        )
        return _with_hash(state)

    income = profile.income.section_40_1
    expense_step = calculate_section_40_1_expense(income, pack)
    benefits = profile.benefits
    personal = personal_allowance(benefits.personal_eligible, pack)
    parents = allowance_for_parents(benefits.parents, pack)
    children = allowance_for_children(benefits.children, pack)
    mortgage = deductible_mortgage_interest(
        benefits.mortgage_interest_paid, benefits.mortgage_eligible, pack
    )
    allowances = AllowanceCalculation(
        personal, benefits.social_security_paid, parents, children, mortgage
    )
    taxable_income = (income - expense_step.output_amount - allowances.total).floor_at_zero()
    pit = calculate_progressive_pit(taxable_income, pack)
    used = (
        rule_ids.SECTION_40_1_EXPENSE,
        rule_ids.PERSONAL_ALLOWANCE,
        rule_ids.SOCIAL_SECURITY_SECTION_33,
        rule_ids.PARENT_ALLOWANCE,
        rule_ids.CHILD_ALLOWANCE,
        rule_ids.MORTGAGE_INTEREST,
        rule_ids.PIT_RATE_SCHEDULE,
    )
    trace = (
        _step(
            step_id="assessable-income",
            description="Assessable Section 40(1) employment income",
            rule_id=rule_ids.SECTION_40_1_EXPENSE,
            input_amount=income,
            output_amount=income,
            pack=pack,
        ),
        expense_step,
        _step(
            step_id="personal-allowance",
            description="Personal allowance",
            rule_id=rule_ids.PERSONAL_ALLOWANCE,
            input_amount=income,
            output_amount=personal,
            pack=pack,
        ),
        _step(
            step_id="social-security",
            description="Actual Section 33 contribution paid",
            rule_id=rule_ids.SOCIAL_SECURITY_SECTION_33,
            input_amount=benefits.social_security_paid,
            output_amount=benefits.social_security_paid,
            pack=pack,
        ),
        _step(
            step_id="parent-allowance",
            description="Eligible parent allowances",
            rule_id=rule_ids.PARENT_ALLOWANCE,
            input_amount=Money.zero(),
            output_amount=parents,
            pack=pack,
        ),
        _step(
            step_id="child-allowance",
            description="Eligible child allowances",
            rule_id=rule_ids.CHILD_ALLOWANCE,
            input_amount=Money.zero(),
            output_amount=children,
            pack=pack,
        ),
        _step(
            step_id="mortgage-interest",
            description="Eligible mortgage interest",
            rule_id=rule_ids.MORTGAGE_INTEREST,
            input_amount=benefits.mortgage_interest_paid,
            output_amount=mortgage,
            pack=pack,
        ),
        _step(
            step_id="net-taxable-income",
            description="Net taxable income",
            rule_id=rule_ids.PIT_RATE_SCHEDULE,
            input_amount=income,
            output_amount=taxable_income,
            pack=pack,
        ),
        *pit.steps,
    )
    rights: list[ExistingRight] = []
    if benefits.parents:
        rights.append(
            ExistingRight(
                category="parent",
                eligible=parents.is_positive(),
                input_amount=Money.zero(),
                deductible_amount=parents,
                rule_id=rule_ids.PARENT_ALLOWANCE,
            )
        )
    if benefits.children:
        rights.append(
            ExistingRight(
                category="child",
                eligible=children.is_positive(),
                input_amount=Money.zero(),
                deductible_amount=children,
                rule_id=rule_ids.CHILD_ALLOWANCE,
            )
        )
    if benefits.mortgage_eligible or benefits.mortgage_interest_paid.is_positive():
        rights.append(
            ExistingRight(
                category="mortgage_interest",
                eligible=benefits.mortgage_eligible,
                input_amount=benefits.mortgage_interest_paid,
                deductible_amount=mortgage,
                rule_id=rule_ids.MORTGAGE_INTEREST,
            )
        )
    state = TaxState(
        TaxStatus.READY,
        profile.tax_year,
        IncomeCalculation(income),
        ExpenseCalculation(expense_step.output_amount),
        allowances,
        taxable_income,
        pit.tax,
        pit.marginal_rate,
        tuple(rights),
        (),
        CalculationTrace(trace),
        used,
        _sources(used, pack),
        pack.rule_pack_id,
        pack.version,
        engine_version,
        (),
        "",
        pack,
    )
    return _with_hash(state)


def _with_hash(state: TaxState) -> TaxState:
    return replace(state, output_hash=sha256_hex(canonical_json(state.material_dict())))
