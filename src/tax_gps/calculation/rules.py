"""Pure calculations driven only by an activated policy pack."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from tax_gps.calculation.models import (
    CalculationStep,
    DeductionCapacity,
    ProgressivePitCalculation,
    TaxImpact,
)
from tax_gps.core.canonical import JsonValue
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage
from tax_gps.policy import rule_ids
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import LimitGroup, TaxBracket, TaxRule
from tax_gps.profile.models import Child, Parent


def _rule(pack: ActivatedRulePack, rule_id: str) -> TaxRule:
    return pack.pack.rule(rule_id)


def _params(rule: TaxRule) -> Mapping[str, JsonValue]:
    return cast(Mapping[str, JsonValue], rule.parameters)


def _money(params: Mapping[str, JsonValue], key: str) -> Money:
    value = params[key]
    if not isinstance(value, str | int) or isinstance(value, bool):
        raise InvalidValueError(f"policy parameter {key} must be decimal text")
    return Money.of(value)


def _percentage(params: Mapping[str, JsonValue], key: str) -> Percentage:
    value = params[key]
    if not isinstance(value, str | int) or isinstance(value, bool):
        raise InvalidValueError(f"policy parameter {key} must be decimal text")
    return Percentage.of(value)


def _source_id(rule: TaxRule) -> str:
    return cast(str, rule.source_id)


def _non_negative(amount: Money, field: str) -> None:
    if amount.is_negative():
        raise InvalidValueError(f"{field} cannot be negative")


def tax_brackets(pack: ActivatedRulePack) -> tuple[TaxBracket, ...]:
    rule = _rule(pack, rule_ids.PIT_RATE_SCHEDULE)
    raw = _params(rule)["brackets"]
    if not isinstance(raw, tuple):
        raise InvalidValueError("PIT brackets must be a list")
    lower = Money.zero()
    result: list[TaxBracket] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise InvalidValueError("PIT bracket must be an object")
        upper_value = item["upper"]
        upper = None if upper_value is None else Money.of(_decimal_value(upper_value, "upper"))
        rate = Percentage.of(_decimal_value(item["rate"], "rate"))
        result.append(TaxBracket(lower, upper, rate))
        if upper is not None:
            lower = upper
    return tuple(result)


def _decimal_value(value: JsonValue, field: str) -> str | int:
    if isinstance(value, bool) or not isinstance(value, str | int):
        raise InvalidValueError(f"{field} must be decimal text")
    return value


def calculate_progressive_pit(
    taxable_income: Money, pack: ActivatedRulePack
) -> ProgressivePitCalculation:
    _non_negative(taxable_income, "taxable income")
    rule = _rule(pack, rule_ids.PIT_RATE_SCHEDULE)
    steps: list[CalculationStep] = []
    tax = Money.zero()
    marginal = Percentage.zero()
    for index, bracket in enumerate(tax_brackets(pack), start=1):
        if taxable_income <= bracket.lower:
            break
        bracket_top = (
            taxable_income if bracket.upper is None else Money.min(taxable_income, bracket.upper)
        )
        amount_in_bracket = bracket_top - bracket.lower
        bracket_tax = amount_in_bracket * bracket.rate
        tax += bracket_tax
        marginal = bracket.rate
        steps.append(
            CalculationStep(
                step_id=f"pit-bracket-{index}",
                description="Progressive PIT bracket",
                rule_id=rule.rule_id,
                source_id=_source_id(rule),
                input_amount=amount_in_bracket,
                output_amount=bracket_tax,
                rate=bracket.rate,
            )
        )
    return ProgressivePitCalculation(tax, marginal, tuple(steps))


def calculate_section_40_1_expense(income: Money, pack: ActivatedRulePack) -> CalculationStep:
    _non_negative(income, "section 40(1) income")
    rule = _rule(pack, rule_ids.SECTION_40_1_EXPENSE)
    params = _params(rule)
    amount = Money.min(income * _percentage(params, "rate"), _money(params, "cap"))
    return CalculationStep(
        "section-40-1-expense",
        "Section 40(1) expense",
        rule.rule_id,
        _source_id(rule),
        income,
        amount,
        _percentage(params, "rate"),
    )


def calculate_section_33_contribution(wage: Money, pack: ActivatedRulePack) -> Money:
    _non_negative(wage, "monthly wage")
    if wage.is_zero():
        return Money.zero()
    params = _params(_rule(pack, rule_ids.SOCIAL_SECURITY_SECTION_33))
    basis = Money.min(
        Money.max(wage, _money(params, "monthly_wage_floor")),
        _money(params, "monthly_wage_ceiling"),
    )
    return Money.min(basis * _percentage(params, "rate"), _money(params, "monthly_maximum"))


def personal_allowance(eligible: bool, pack: ActivatedRulePack) -> Money:
    if not eligible:
        return Money.zero()
    return _money(_params(_rule(pack, rule_ids.PERSONAL_ALLOWANCE)), "amount")


def allowance_for_parents(parents: tuple[Parent, ...], pack: ActivatedRulePack) -> Money:
    amount = _money(_params(_rule(pack, rule_ids.PARENT_ALLOWANCE)), "amount_per_eligible_parent")
    return Money.sum(amount for parent in parents if parent.eligible)


def allowance_for_children(children: tuple[Child, ...], pack: ActivatedRulePack) -> Money:
    params = _params(_rule(pack, rule_ids.CHILD_ALLOWANCE))
    standard = _money(params, "standard")
    additional = _money(params, "additional_legal_child")
    min_order = params["additional_min_order"]
    min_birth_year = params["additional_min_birth_year"]
    if not isinstance(min_order, int) or isinstance(min_order, bool):
        raise InvalidValueError("additional_min_order must be an integer")
    if not isinstance(min_birth_year, int) or isinstance(min_birth_year, bool):
        raise InvalidValueError("additional_min_birth_year must be an integer")
    total = Money.zero()
    for child in children:
        if child.legally_eligible:
            total += standard
            if child.order >= min_order and child.birth_year >= min_birth_year:
                total += additional
    return total


def deductible_mortgage_interest(
    interest_paid: Money, eligible: bool, pack: ActivatedRulePack
) -> Money:
    _non_negative(interest_paid, "mortgage interest")
    if not eligible:
        return Money.zero()
    return Money.min(interest_paid, _money(_params(_rule(pack, rule_ids.MORTGAGE_INTEREST)), "cap"))


def limit_group(group_id: str, pack: ActivatedRulePack) -> LimitGroup:
    params = _params(_rule(pack, rule_ids.RETIREMENT_SHARED_LIMIT))
    configured_id = params["group_id"]
    if configured_id != group_id:
        raise InvalidValueError(f"unknown shared group: {group_id}")
    return LimitGroup(configured_id, _money(params, "cap"))


def calculate_deduction_capacity(
    *,
    category: str,
    standalone_limit: Money,
    amount_used: Money,
    shared_group: str | None,
    shared_amount_used: Money,
    pack: ActivatedRulePack,
) -> DeductionCapacity:
    _non_negative(standalone_limit, "standalone limit")
    _non_negative(amount_used, "amount used")
    _non_negative(shared_amount_used, "shared amount used")
    if amount_used > standalone_limit:
        raise InvalidValueError("amount used exceeds standalone limit")
    standalone_remaining = standalone_limit - amount_used
    if shared_group is None:
        if not shared_amount_used.is_zero():
            raise InvalidValueError("shared amount used requires a shared group")
        return DeductionCapacity(
            category,
            standalone_limit,
            amount_used,
            standalone_remaining,
            None,
            None,
            shared_amount_used,
            None,
            standalone_remaining,
        )
    group = limit_group(shared_group, pack)
    if shared_amount_used > group.cap:
        raise InvalidValueError("shared amount used exceeds shared limit")
    shared_remaining = group.cap - shared_amount_used
    return DeductionCapacity(
        category,
        standalone_limit,
        amount_used,
        standalone_remaining,
        group.group_id,
        group.cap,
        shared_amount_used,
        shared_remaining,
        Money.min(standalone_remaining, shared_remaining),
    )


def calculate_tax_saving(
    taxable_before: Money, additional_deduction: Money, pack: ActivatedRulePack
) -> TaxImpact:
    _non_negative(taxable_before, "taxable income")
    _non_negative(additional_deduction, "additional deduction")
    taxable_after = (taxable_before - additional_deduction).floor_at_zero()
    pit_before = calculate_progressive_pit(taxable_before, pack).tax
    pit_after = calculate_progressive_pit(taxable_after, pack).tax
    return TaxImpact(taxable_before, taxable_after, pit_before, pit_after, pit_before - pit_after)
