"""Application service orchestrating the supported deterministic salary-only path."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from tax_gps.calculation.models import (
    AllowanceCalculation,
    CalculationStep,
    CalculationTrace,
    DeductionCapacity,
    ExistingRight,
    ExpenseCalculation,
    IncomeCalculation,
    TaxState,
    TaxStatus,
)
from tax_gps.calculation.rules import (
    allowance_for_children,
    allowance_for_parents,
    calculate_deduction_capacity,
    calculate_progressive_pit,
    calculate_section_40_1_expense,
    deductible_mortgage_interest,
    limit_group,
    personal_allowance,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.policy import rule_ids
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import RuleSource
from tax_gps.profile.models import UserProfile

ENGINE_VERSION = "tax-gps-core/0.1.0"


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
    source_ids = {pack.pack.rule(rule_id).source_id for rule_id in rule_ids_used}
    return tuple(source for source in pack.pack.sources if source.source_id in source_ids)


def calculate_tax(
    profile: UserProfile, pack: ActivatedRulePack, *, engine_version: str = ENGINE_VERSION
) -> TaxState:
    if profile.tax_year != pack.pack.tax_year:
        raise ValueError("profile tax year must match the activated rule pack")
    material_unsupported = tuple(
        item for item in profile.income.unsupported if item.amount.is_positive()
    )
    if material_unsupported:
        reasons = tuple(
            f"material unsupported income: {item.category}" for item in material_unsupported
        )
        state = TaxState(
            TaxStatus.ADVANCED_TAX_PATH_REQUIRED,
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
    retirement_capacities: tuple[DeductionCapacity, ...] = ()
    retirement_rule_ids: tuple[str, ...] = ()
    retirement_trace: tuple[CalculationStep, ...] = ()
    if benefits.retirement_contributions:
        retirement_used = Money.sum(item.amount_used for item in benefits.retirement_contributions)
        retirement_group = limit_group("RETIREMENT", pack)
        retirement_capacity = calculate_deduction_capacity(
            category="RETIREMENT_SHARED_GROUP",
            standalone_limit=retirement_group.cap,
            amount_used=retirement_used,
            shared_group=retirement_group.group_id,
            shared_amount_used=retirement_used,
            pack=pack,
        )
        retirement_capacities = (retirement_capacity,)
        retirement_rule_ids = (rule_ids.RETIREMENT_SHARED_LIMIT,)
        retirement_trace = (
            _step(
                step_id="retirement-shared-capacity",
                description="Remaining shared retirement deduction capacity",
                rule_id=rule_ids.RETIREMENT_SHARED_LIMIT,
                input_amount=retirement_used,
                output_amount=retirement_capacity.usable_amount,
                pack=pack,
            ),
        )
    used = (
        rule_ids.SECTION_40_1_EXPENSE,
        rule_ids.PERSONAL_ALLOWANCE,
        rule_ids.SOCIAL_SECURITY_SECTION_33,
        rule_ids.PARENT_ALLOWANCE,
        rule_ids.CHILD_ALLOWANCE,
        rule_ids.MORTGAGE_INTEREST,
        rule_ids.PIT_RATE_SCHEDULE,
        *retirement_rule_ids,
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
        *retirement_trace,
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
    rights.extend(
        ExistingRight(
            category=item.category,
            eligible=True,
            input_amount=item.amount_used,
            deductible_amount=item.amount_used,
            rule_id=rule_ids.RETIREMENT_SHARED_LIMIT,
        )
        for item in benefits.retirement_contributions
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
        retirement_capacities,
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
