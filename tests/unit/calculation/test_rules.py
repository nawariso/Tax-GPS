"""Pure calculation rules and mandatory boundary acceptance tests."""

from dataclasses import replace

import pytest

from tax_gps.calculation.rules import (
    allowance_for_children,
    allowance_for_parents,
    calculate_deduction_capacity,
    calculate_progressive_pit,
    calculate_section_33_contribution,
    calculate_section_40_1_expense,
    calculate_tax_saving,
    deductible_mortgage_interest,
    personal_allowance,
)
from tax_gps.core.canonical import freeze
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import Child, Parent
from tests.support.policy import production_pack


def _pack_with_parameters(rule_id: str, parameters: object) -> ActivatedRulePack:
    pack = production_pack()
    rules = tuple(
        replace(rule, parameters=freeze(parameters)) if rule.rule_id == rule_id else rule
        for rule in pack.pack.rules
    )
    return replace(pack, pack=replace(pack.pack, rules=rules))


@pytest.mark.mandatory
@pytest.mark.boundary
@pytest.mark.parametrize(
    ("income", "tax"),
    [
        (0, 0),
        (150000, 0),
        (300000, 7500),
        (500000, 27500),
        (750000, 65000),
        (1000000, 115000),
        (2000000, 365000),
        (5000000, 1265000),
        (6000000, 1615000),
    ],
)
def test_pit_boundaries(income: int, tax: int) -> None:
    assert calculate_progressive_pit(Money.of(income), production_pack()).tax == Money.of(tax)


def test_pit_trace_has_a_step_for_each_used_bracket() -> None:
    result = calculate_progressive_pit(Money.of(820000), production_pack())
    assert result.tax == Money.of(79000)
    assert [step.output_amount for step in result.steps] == [
        Money.of(0),
        Money.of(7500),
        Money.of(20000),
        Money.of(37500),
        Money.of(14000),
    ]
    assert all(step.rule_id and step.source_id for step in result.steps)


@pytest.mark.negative
def test_negative_taxable_income_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="negative"):
        calculate_progressive_pit(Money.of(-1), production_pack())


@pytest.mark.mandatory
@pytest.mark.parametrize(("income", "expense"), [(100000, 50000), (300000, 100000)])
def test_section_40_1_expense(income: int, expense: int) -> None:
    assert calculate_section_40_1_expense(Money.of(income), production_pack()).amount == Money.of(
        expense
    )


@pytest.mark.negative
def test_negative_employment_income_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="negative"):
        calculate_section_40_1_expense(Money.of(-1), production_pack())


@pytest.mark.mandatory
@pytest.mark.parametrize(("wage", "contribution"), [(20000, 875), (10000, 500)])
def test_monthly_social_security(wage: int, contribution: int) -> None:
    assert calculate_section_33_contribution(Money.of(wage), production_pack()) == Money.of(
        contribution
    )


def test_social_security_uses_wage_floor_and_zero_for_no_wage() -> None:
    assert calculate_section_33_contribution(Money.of(1000), production_pack()) == Money.of("82.50")
    assert calculate_section_33_contribution(Money.zero(), production_pack()) == Money.zero()


@pytest.mark.negative
def test_negative_wage_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="negative"):
        calculate_section_33_contribution(Money.of(-1), production_pack())


@pytest.mark.mandatory
def test_personal_allowance_is_conditional() -> None:
    assert personal_allowance(True, production_pack()) == Money.of(60000)
    assert personal_allowance(False, production_pack()) == Money.zero()


@pytest.mark.mandatory
def test_two_eligible_parents() -> None:
    parents = (Parent("father", True), Parent("mother", True), Parent("spouse-father", False))
    assert allowance_for_parents(parents, production_pack()) == Money.of(60000)


def test_child_order_legality_and_birth_year_are_explicit() -> None:
    children = (
        Child(order=1, legally_eligible=True, birth_year=2017),
        Child(order=2, legally_eligible=True, birth_year=2018),
        Child(order=3, legally_eligible=False, birth_year=2020),
    )
    assert allowance_for_children(children, production_pack()) == Money.of(90000)


@pytest.mark.negative
def test_child_order_and_birth_year_are_validated() -> None:
    with pytest.raises(InvalidValueError):
        Child(order=0, legally_eligible=True, birth_year=2018)
    with pytest.raises(InvalidValueError):
        Child(order=1, legally_eligible=True, birth_year=2561)


@pytest.mark.mandatory
def test_mortgage_cap() -> None:
    assert deductible_mortgage_interest(Money.of(125000), True, production_pack()) == Money.of(
        100000
    )
    assert deductible_mortgage_interest(Money.of(125000), False, production_pack()) == Money.zero()


@pytest.mark.negative
def test_negative_mortgage_interest_is_rejected() -> None:
    with pytest.raises(InvalidValueError):
        deductible_mortgage_interest(Money.of(-1), True, production_pack())


@pytest.mark.mandatory
@pytest.mark.golden
def test_retirement_shared_limit_exhaustion() -> None:
    result = calculate_deduction_capacity(
        category="RMF",
        standalone_limit=Money.of(500000),
        amount_used=Money.zero(),
        shared_group="RETIREMENT",
        shared_amount_used=Money.of(500000),
        pack=production_pack(),
    )
    assert result.shared_remaining == Money.zero()
    assert result.usable_amount == Money.zero()


def test_capacity_is_minimum_of_standalone_and_shared_remaining() -> None:
    result = calculate_deduction_capacity(
        category="PENSION",
        standalone_limit=Money.of(200000),
        amount_used=Money.of(50000),
        shared_group="RETIREMENT",
        shared_amount_used=Money.of(400000),
        pack=production_pack(),
    )
    assert result.standalone_remaining == Money.of(150000)
    assert result.shared_remaining == Money.of(100000)
    assert result.usable_amount == Money.of(100000)


def test_standalone_capacity_without_shared_group() -> None:
    result = calculate_deduction_capacity(
        category="OTHER",
        standalone_limit=Money.of(100000),
        amount_used=Money.of(25000),
        shared_group=None,
        shared_amount_used=Money.zero(),
        pack=production_pack(),
    )
    assert result.shared_limit is None
    assert result.shared_remaining is None
    assert result.usable_amount == Money.of(75000)


@pytest.mark.negative
@pytest.mark.parametrize(
    ("limit", "used", "shared", "shared_used"),
    [(-1, 0, None, 0), (100, -1, None, 0), (100, 101, None, 0), (100, 0, "RETIREMENT", 500001)],
)
def test_invalid_capacity_and_overflow_are_rejected(
    limit: int, used: int, shared: str | None, shared_used: int
) -> None:
    with pytest.raises(InvalidValueError):
        calculate_deduction_capacity(
            category="x",
            standalone_limit=Money.of(limit),
            amount_used=Money.of(used),
            shared_group=shared,
            shared_amount_used=Money.of(shared_used),
            pack=production_pack(),
        )


@pytest.mark.negative
def test_unknown_shared_group_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="shared group"):
        calculate_deduction_capacity(
            category="x",
            standalone_limit=Money.of(100),
            amount_used=Money.zero(),
            shared_group="UNKNOWN",
            shared_amount_used=Money.zero(),
            pack=production_pack(),
        )


@pytest.mark.negative
def test_shared_usage_without_group_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="requires"):
        calculate_deduction_capacity(
            category="x",
            standalone_limit=Money.of(100),
            amount_used=Money.zero(),
            shared_group=None,
            shared_amount_used=Money.of(1),
            pack=production_pack(),
        )


@pytest.mark.negative
@pytest.mark.parametrize(
    ("rule_id", "parameters", "call"),
    [
        (
            "TH-PIT-ALLOWANCE-PERSONAL",
            {"amount": True},
            lambda pack: personal_allowance(True, pack),
        ),
        (
            "TH-PIT-EXPENSE-40-1",
            {"rate": True, "cap": "100000.00"},
            lambda pack: calculate_section_40_1_expense(Money.of(1), pack),
        ),
        (
            "TH-PIT-RATE-SCHEDULE",
            {"brackets": "bad"},
            lambda pack: calculate_progressive_pit(Money.of(1), pack),
        ),
        (
            "TH-PIT-RATE-SCHEDULE",
            {"brackets": ["bad"]},
            lambda pack: calculate_progressive_pit(Money.of(1), pack),
        ),
        (
            "TH-PIT-RATE-SCHEDULE",
            {"brackets": [{"upper": True, "rate": "0"}]},
            lambda pack: calculate_progressive_pit(Money.of(1), pack),
        ),
        (
            "TH-PIT-ALLOWANCE-CHILD",
            {
                "standard": "30000.00",
                "additional_legal_child": "30000.00",
                "additional_min_order": "2",
                "additional_min_birth_year": 2018,
            },
            lambda pack: allowance_for_children((), pack),
        ),
        (
            "TH-PIT-ALLOWANCE-CHILD",
            {
                "standard": "30000.00",
                "additional_legal_child": "30000.00",
                "additional_min_order": 2,
                "additional_min_birth_year": "2018",
            },
            lambda pack: allowance_for_children((), pack),
        ),
    ],
)
def test_malformed_calculation_parameters_are_rejected(
    rule_id: str, parameters: object, call: object
) -> None:
    with pytest.raises(InvalidValueError):
        call(_pack_with_parameters(rule_id, parameters))  # type: ignore[operator]


def test_authoritative_tax_saving_crosses_bracket() -> None:
    impact = calculate_tax_saving(Money.of(820000), Money.of(100000), production_pack())
    assert impact.taxable_after == Money.of(720000)
    assert impact.pit_before == Money.of(79000)
    assert impact.pit_after == Money.of(60500)
    assert impact.saving == Money.of(18500)


def test_tax_saving_cannot_reduce_taxable_income_below_zero() -> None:
    impact = calculate_tax_saving(Money.of(10000), Money.of(20000), production_pack())
    assert impact.taxable_after == Money.zero()
    assert impact.saving == Money.zero()


@pytest.mark.negative
def test_negative_additional_deduction_is_rejected() -> None:
    with pytest.raises(InvalidValueError):
        calculate_tax_saving(Money.of(1), Money.of(-1), production_pack())
