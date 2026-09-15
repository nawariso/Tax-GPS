"""Golden personas, unsupported paths, trace, audit, and deterministic replay."""

from dataclasses import FrozenInstanceError, replace

import pytest

from tax_gps.audit import AuditReplayError, create_audit_snapshot, replay
from tax_gps.calculation.models import TaxStatus, capacity_to_dict
from tax_gps.calculation.rules import calculate_deduction_capacity
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import ENGINE_VERSION, calculate_tax
from tax_gps.profile.models import (
    Child,
    ExistingTaxBenefits,
    IncomeProfile,
    Parent,
    RetirementContribution,
    UnsupportedIncome,
    UserProfile,
)
from tests.support.policy import production_pack


def profile(salary: int, sso: int = 10500) -> UserProfile:
    return UserProfile(
        profile_id="persona",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(salary)),
        benefits=ExistingTaxBenefits(social_security_paid=Money.of(sso)),
    )


@pytest.mark.golden
def test_g01_first_jobber() -> None:
    state = calculate_tax(profile(300000), production_pack())
    assert state.status is TaxStatus.READY
    assert state.taxable_income == Money.of(129500)
    assert state.pit == Money.zero()
    assert state.existing_rights == ()
    assert state.deduction_capacities == ()
    assert state.tax_impact(Money.of(100000)).saving == Money.zero()


@pytest.mark.golden
def test_g02_bracket_crossing() -> None:
    state = calculate_tax(profile(990500), production_pack())
    assert state.taxable_income == Money.of(820000)
    assert state.pit == Money.of(79000)
    assert state.marginal_rate is not None
    assert state.marginal_rate.canonical() == "0.2"
    assert state.tax_impact(Money.of(100000)).saving == Money.of(18500)


@pytest.mark.golden
def test_g03_high_income() -> None:
    state = calculate_tax(profile(2800000), production_pack())
    assert state.taxable_income == Money.of(2629500)
    assert state.pit == Money.of(553850)
    assert state.tax_impact(Money.of(100000)).saving == Money.of(30000)


@pytest.mark.mandatory
@pytest.mark.negative
def test_unsupported_01_material_section_40_8_income_is_explicit() -> None:
    user = replace(
        profile(300000),
        income=IncomeProfile(
            section_40_1=Money.of(300000),
            unsupported=(UnsupportedIncome("40(8)", Money.of(1)),),
        ),
    )
    state = calculate_tax(user, production_pack())
    assert state.status is TaxStatus.ADVANCED_TAX_PATH_REQUIRED
    assert state.unsupported_reasons == ("material unsupported income: 40(8)",)
    assert state.pit is None
    assert state.output_hash
    with pytest.raises(ValueError, match="unsupported"):
        state.tax_impact(Money.of(1))


def test_zero_unsupported_income_does_not_block_salary_path() -> None:
    user = replace(
        profile(300000),
        income=IncomeProfile(
            section_40_1=Money.of(300000),
            unsupported=(UnsupportedIncome("40(8)", Money.zero()),),
        ),
    )
    assert calculate_tax(user, production_pack()).status is TaxStatus.READY


@pytest.mark.negative
def test_profile_rejects_wrong_tax_year_and_negative_inputs() -> None:
    with pytest.raises(ValueError, match="tax year"):
        calculate_tax(replace(profile(1), tax_year=TaxYear(2025)), production_pack())
    with pytest.raises(ValueError, match="negative"):
        IncomeProfile(section_40_1=Money.of(-1))
    with pytest.raises(ValueError, match="negative"):
        ExistingTaxBenefits(social_security_paid=Money.of(-1))
    with pytest.raises(ValueError, match="negative"):
        UnsupportedIncome("40(8)", Money.of(-1))


def test_state_exposes_material_trace_rules_sources_and_serialization() -> None:
    state = calculate_tax(profile(990500), production_pack())
    assert state.income.assessable_income == Money.of(990500)
    assert state.expenses.section_40_1 == Money.of(100000)
    assert state.allowances.personal == Money.of(60000)
    assert state.allowances.social_security == Money.of(10500)
    assert state.calculation_trace.steps
    assert state.rules_applied
    assert state.sources
    data = state.to_dict()
    assert data["taxable_income"] == "820000.00"
    assert data["pit"] == "79000.00"
    assert data["output_hash"] == state.output_hash
    sources = data["sources"]
    assert isinstance(sources, list)
    assert isinstance(sources[0], dict)
    assert sources[0]["url"].startswith("https://")


@pytest.mark.replay
@pytest.mark.mandatory
def test_replay_01_same_material_input_has_same_hash() -> None:
    first = calculate_tax(profile(990500), production_pack())
    second = calculate_tax(profile(990500), production_pack())
    assert first.output_hash == second.output_hash
    snapshot = create_audit_snapshot(profile(990500), first, production_pack())
    assert replay(snapshot, profile(990500), production_pack()) == first


@pytest.mark.replay
def test_audit_snapshot_is_immutable_and_contains_required_material() -> None:
    user = profile(990500)
    state = calculate_tax(user, production_pack())
    snapshot = create_audit_snapshot(user, state, production_pack())
    assert snapshot.profile_version == "1"
    assert len(snapshot.profile_hash) == 64
    assert snapshot.tax_year == TaxYear(2026)
    assert snapshot.rule_pack_id == production_pack().rule_pack_id
    assert snapshot.rule_pack_version == production_pack().version
    assert snapshot.engine_version == ENGINE_VERSION
    assert snapshot.output_hash == state.output_hash
    with pytest.raises(FrozenInstanceError):
        snapshot.output_hash = "changed"  # type: ignore[misc]


@pytest.mark.replay
@pytest.mark.negative
def test_replay_detects_profile_policy_engine_and_output_mismatch() -> None:
    user = profile(990500)
    state = calculate_tax(user, production_pack())
    snapshot = create_audit_snapshot(user, state, production_pack())
    with pytest.raises(AuditReplayError, match="profile"):
        replay(snapshot, profile(990501), production_pack())
    with pytest.raises(AuditReplayError, match="engine"):
        replay(snapshot, user, production_pack(), engine_version="other")
    with pytest.raises(AuditReplayError, match="rule pack"):
        replay(replace(snapshot, rule_pack_hash="0" * 64), user, production_pack())
    with pytest.raises(AuditReplayError, match="output"):
        replay(replace(snapshot, output_hash="0" * 64), user, production_pack())


def test_profile_snapshot_hash_is_order_independent_of_construction() -> None:
    user = profile(100)
    assert user.profile_hash() == replace(user).profile_hash()


def test_capacity_serialization_covers_shared_limits() -> None:
    capacity = calculate_deduction_capacity(
        category="RMF",
        standalone_limit=Money.of(500000),
        amount_used=Money.zero(),
        shared_group="RETIREMENT",
        shared_amount_used=Money.of(400000),
        pack=production_pack(),
    )
    assert capacity_to_dict(capacity)["shared_remaining"] == "100000.00"


@pytest.mark.golden
@pytest.mark.mandatory
def test_existing_rights_and_shared_retirement_capacity_flow_through_engine() -> None:
    benefits = ExistingTaxBenefits(
        social_security_paid=Money.of(10500),
        parents=(Parent("father", True), Parent("mother", True)),
        children=(
            Child(order=1, legally_eligible=True, birth_year=2017),
            Child(order=2, legally_eligible=True, birth_year=2018),
        ),
        mortgage_interest_paid=Money.of(125000),
        mortgage_eligible=True,
        retirement_contributions=(
            RetirementContribution("PVD", Money.of(400000)),
            RetirementContribution("eligible_retirement_pension", Money.of(100000)),
        ),
    )
    user = replace(profile(2800000), benefits=benefits)
    state = calculate_tax(user, production_pack())
    assert state.allowances.parents == Money.of(60000)
    assert state.allowances.children == Money.of(90000)
    assert state.allowances.mortgage_interest == Money.of(100000)
    assert state.deduction_capacities[0].shared_remaining == Money.zero()
    assert state.deduction_capacities[0].usable_amount == Money.zero()
    retirement_steps = [
        step
        for step in state.calculation_trace.steps
        if step.rule_id == "TH-PIT-LIMIT-RETIREMENT-SHARED"
    ]
    assert len(retirement_steps) == 1
    assert retirement_steps[0].input_amount == Money.of(500000)
    assert retirement_steps[0].output_amount == Money.zero()
    assert {right.category for right in state.existing_rights} >= {
        "parent",
        "child",
        "mortgage_interest",
        "PVD",
        "eligible_retirement_pension",
    }
