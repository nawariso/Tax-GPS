"""TGPS-P1-003 mandatory acceptance tests GR-01..16 and golden G05-G07 extensions."""

from __future__ import annotations

from dataclasses import fields
from datetime import date
from decimal import Decimal

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.engine import calculate_tax
from tax_gps.financial.audit import (
    GuardrailReplayError,
    create_guardrail_snapshot,
    replay_guardrails,
)
from tax_gps.financial.engine import evaluate_guardrails
from tax_gps.financial.models import GuardrailAssessment, GuardrailDecision, GuardrailResult
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    activate_financial_policy,
    bundled_financial_policy,
)
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialPlanningContext,
    FinancialProfile,
    ProtectionProfile,
)
from tax_gps.financial.reason_codes import FinancialReasonCode
from tax_gps.financial.state import FinancialValidationError, compute_financial_state
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.profile.models import (
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    UserProfile,
)
from tests.acceptance.test_discovery import SOLAR_FULLY_ASSERTED
from tests.support.catalog import production_catalog, solar_ready_catalog
from tests.support.policy import production_pack

PLANNING_DATE = date(2026, 6, 1)


def _policy() -> ActivatedFinancialPolicy:
    return activate_financial_policy(bundled_financial_policy(TaxYear(2026)))


def _tax_profile(
    salary: int = 990500,
    *,
    benefits: ExistingTaxBenefits | None = None,
    facts: OpportunityFacts | None = None,
) -> UserProfile:
    return UserProfile(
        profile_id="persona",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(salary)),
        benefits=benefits or ExistingTaxBenefits(social_security_paid=Money.of(10500)),
        opportunity_facts=facts if facts is not None else OpportunityFacts(shared_limit_usage=()),
    )


def _discovery(
    user: UserProfile,
    *,
    catalog: ActivatedOpportunityCatalog | None = None,
    planning_date: date = PLANNING_DATE,
) -> DiscoveryResult:
    state = calculate_tax(user, production_pack())
    return discover_opportunities(
        user,
        state,
        production_pack(),
        catalog or production_catalog(),
        DiscoveryContext(TaxYear(2026), planning_date),
    )


_DEFAULT_PROTECTION = ProtectionProfile()


def _financial_profile(
    *,
    liquid_assets: int,
    expenses: int | None,
    debts: tuple[Debt, ...] = (),
    committed_cash_needs: tuple[CommittedCashNeed, ...] = (),
    protection: ProtectionProfile = _DEFAULT_PROTECTION,
) -> FinancialProfile:
    return FinancialProfile(
        liquid_assets=Money.of(liquid_assets),
        monthly_essential_expenses=Money.of(expenses) if expenses is not None else None,
        debts=debts,
        committed_cash_needs=committed_cash_needs,
        protection=protection,
    )


def _guardrails(
    discovery: DiscoveryResult,
    financial_profile: FinancialProfile,
    *,
    budget: int,
    planning_date: date = PLANNING_DATE,
) -> GuardrailResult:
    policy = _policy()
    context = FinancialPlanningContext(
        planning_date=planning_date, available_budget=Money.of(budget)
    )
    state = compute_financial_state(financial_profile, policy, context)
    return evaluate_guardrails(discovery, state, policy, context)


def assessment(result: GuardrailResult, opportunity_id: str) -> GuardrailAssessment:
    return next(item for item in result.assessments if item.opportunity_id == opportunity_id)


HIGH_APR_DEBT = Debt(
    debt_id="cc-1",
    category=DebtCategory.CREDIT_CARD,
    outstanding_balance=Money.of(50000),
    annual_percentage_rate=Decimal("0.18"),
    minimum_monthly_payment=Money.of(2000),
    secured=False,
)


@pytest.mark.mandatory
def test_gr_01_existing_right_passthrough_even_with_critical_debt_and_low_emergency_fund() -> None:
    discovery = _discovery(
        _tax_profile(benefits=ExistingTaxBenefits(parents=(Parent("father", True),)))
    )
    financial_profile = _financial_profile(
        liquid_assets=5000, expenses=5000, debts=(HIGH_APR_DEBT,)
    )
    result = _guardrails(discovery, financial_profile, budget=0)
    parent = assessment(result, opportunity_ids.PARENT_ALLOWANCE)
    assert parent.decision is GuardrailDecision.ALLOW
    assert parent.reason_codes == (FinancialReasonCode.EXISTING_RIGHT_PASSTHROUGH,)


@pytest.mark.mandatory
def test_gr_02_critical_debt_blocks_thai_esg() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(
        liquid_assets=500000, expenses=50000, debts=(HIGH_APR_DEBT,)
    )
    result = _guardrails(discovery, financial_profile, budget=100000)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is GuardrailDecision.BLOCK
    assert thai_esg.max_feasible_allocation == Money.zero()
    assert FinancialReasonCode.CRITICAL_DEBT_PRESENT in thai_esg.reason_codes


@pytest.mark.mandatory
def test_gr_03_low_emergency_fund_blocks_thai_esg() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=100000, expenses=50000)
    result = _guardrails(discovery, financial_profile, budget=50000)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is GuardrailDecision.BLOCK
    assert FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR in thai_esg.reason_codes


@pytest.mark.mandatory
def test_gr_04_liquidity_cap() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=200000, expenses=50000)
    result = _guardrails(discovery, financial_profile, budget=100000)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is GuardrailDecision.CAP
    assert thai_esg.max_feasible_allocation == Money.of(50000)
    assert FinancialReasonCode.ALLOCATION_CAPPED_BY_LIQUIDITY in thai_esg.reason_codes


@pytest.mark.mandatory
def test_gr_05_healthy_state_allows_full_budget() -> None:
    discovery = _discovery(_tax_profile(2000000))
    financial_profile = _financial_profile(liquid_assets=500000, expenses=50000)
    result = _guardrails(discovery, financial_profile, budget=100000)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is GuardrailDecision.ALLOW
    assert thai_esg.max_feasible_allocation == Money.of(100000)


@pytest.mark.mandatory
def test_gr_06_commitment_reduces_feasibility_to_cap() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(
        liquid_assets=300000,
        expenses=50000,
        committed_cash_needs=(
            CommittedCashNeed(
                need_id="tuition",
                amount=Money.of(100000),
                due_date=date(2026, 9, 1),
                mandatory=True,
                description="tuition",
            ),
        ),
    )
    result = _guardrails(discovery, financial_profile, budget=100000)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is GuardrailDecision.CAP
    assert thai_esg.max_feasible_allocation == Money.of(50000)


@pytest.mark.mandatory
def test_gr_07_critical_debt_plus_intrinsic_purpose_requires_review() -> None:
    discovery = _discovery(
        _tax_profile(facts=OpportunityFacts(solar_rooftop=SOLAR_FULLY_ASSERTED)),
        catalog=solar_ready_catalog(),
    )
    financial_profile = _financial_profile(
        liquid_assets=500000, expenses=50000, debts=(HIGH_APR_DEBT,)
    )
    result = _guardrails(discovery, financial_profile, budget=100000)
    solar = assessment(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.decision is GuardrailDecision.REQUIRE_REVIEW
    assert FinancialReasonCode.CRITICAL_DEBT_PRESENT in solar.reason_codes


@pytest.mark.mandatory
def test_gr_08_emergency_shortfall_plus_intrinsic_purpose_requires_review() -> None:
    discovery = _discovery(
        _tax_profile(facts=OpportunityFacts(solar_rooftop=SOLAR_FULLY_ASSERTED)),
        catalog=solar_ready_catalog(),
    )
    financial_profile = _financial_profile(liquid_assets=100000, expenses=50000)
    result = _guardrails(discovery, financial_profile, budget=50000)
    solar = assessment(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.decision is GuardrailDecision.REQUIRE_REVIEW
    assert FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR in solar.reason_codes


@pytest.mark.mandatory
@pytest.mark.negative
def test_gr_09_upstream_unavailable_solar_is_not_applicable() -> None:
    discovery = _discovery(_tax_profile())  # production catalog: solar rule not ready
    financial_profile = _financial_profile(liquid_assets=500000, expenses=50000)
    result = _guardrails(discovery, financial_profile, budget=100000)
    solar = assessment(result, opportunity_ids.SOLAR_ROOFTOP)
    assert solar.decision is GuardrailDecision.NOT_APPLICABLE
    assert solar.reason_codes == (FinancialReasonCode.UPSTREAM_NOT_AVAILABLE,)


@pytest.mark.mandatory
@pytest.mark.negative
def test_gr_10_missing_expenses_never_allows_new_cash() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=500000, expenses=None)
    result = _guardrails(discovery, financial_profile, budget=0)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is not GuardrailDecision.ALLOW
    assert FinancialReasonCode.FINANCIAL_INPUT_REQUIRED in thai_esg.reason_codes


@pytest.mark.mandatory
@pytest.mark.negative
def test_gr_11_budget_greater_than_liquid_assets_fails_closed() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=10000, expenses=5000)
    with pytest.raises(FinancialValidationError):
        _guardrails(discovery, financial_profile, budget=20000)


@pytest.mark.mandatory
def test_gr_12_protection_gap_is_informational_and_does_not_block() -> None:
    discovery = _discovery(_tax_profile(2000000))
    financial_profile = _financial_profile(
        liquid_assets=500000,
        expenses=50000,
        protection=ProtectionProfile(
            required_life_coverage=Money.of(3000000), existing_life_coverage=Money.of(1000000)
        ),
    )
    result = _guardrails(discovery, financial_profile, budget=100000)
    thai_esg = assessment(result, opportunity_ids.THAI_ESG)
    assert thai_esg.decision is GuardrailDecision.ALLOW
    assert FinancialReasonCode.PROTECTION_GAP in thai_esg.reason_codes


@pytest.mark.mandatory
@pytest.mark.negative
def test_gr_13_protection_unknown_is_null_not_zero() -> None:
    financial_profile = _financial_profile(liquid_assets=500000, expenses=50000)
    policy = _policy()
    context = FinancialPlanningContext(
        planning_date=PLANNING_DATE, available_budget=Money.of(100000)
    )
    state = compute_financial_state(financial_profile, policy, context)
    assert state.protection_gap is None


@pytest.mark.mandatory
@pytest.mark.replay
def test_gr_14_determinism() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=500000, expenses=50000)
    result_a = _guardrails(discovery, financial_profile, budget=100000)
    result_b = _guardrails(discovery, financial_profile, budget=100000)
    assert result_a.guardrail_hash == result_b.guardrail_hash
    assert result_a.to_dict() == result_b.to_dict()


@pytest.mark.mandatory
@pytest.mark.replay
def test_gr_15_replay_rejects_mutated_material_input() -> None:
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=500000, expenses=50000)
    policy = _policy()
    context = FinancialPlanningContext(
        planning_date=PLANNING_DATE, available_budget=Money.of(100000)
    )
    state = compute_financial_state(financial_profile, policy, context)
    result = evaluate_guardrails(discovery, state, policy, context)
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)

    # Replay with identical inputs succeeds.
    replayed = replay_guardrails(snapshot, discovery, state, policy, context)
    assert replayed.guardrail_hash == result.guardrail_hash

    # Mutated financial profile invalidates the state hash the snapshot was bound to.
    mutated_profile = _financial_profile(liquid_assets=500001, expenses=50000)
    mutated_state = compute_financial_state(mutated_profile, policy, context)
    with pytest.raises(GuardrailReplayError):
        replay_guardrails(snapshot, discovery, mutated_state, policy, context)

    # Mutated available budget also invalidates replay.
    mutated_context = FinancialPlanningContext(
        planning_date=PLANNING_DATE, available_budget=Money.of(50000)
    )
    with pytest.raises(GuardrailReplayError):
        replay_guardrails(snapshot, discovery, state, policy, mutated_context)


@pytest.mark.mandatory
def test_gr_16_no_recommendation_leakage() -> None:
    forbidden = ("recommended", "rank", "score", "best", "optimal", "winner")
    discovery = _discovery(_tax_profile(800000))
    financial_profile = _financial_profile(liquid_assets=500000, expenses=50000)
    result = _guardrails(discovery, financial_profile, budget=100000)

    def check_keys(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(token in key.lower() for token in forbidden), key
                check_keys(item)
        elif isinstance(value, list):
            for item in value:
                check_keys(item)

    check_keys(result.to_dict())
    for model in (GuardrailResult, GuardrailAssessment):
        for field in fields(model):
            assert not any(token in field.name.lower() for token in forbidden), field.name
