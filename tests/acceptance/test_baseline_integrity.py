"""C01: incomplete baselines must not publish usable tax or savings."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.engine import calculate_tax
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.profile.models import (
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    RetirementContribution,
    SharedLimitUsage,
    UnsupportedIncome,
    UserProfile,
)
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack


def _profile(
    *,
    usage: tuple[SharedLimitUsage, ...] | None = (),
    retirement: tuple[RetirementContribution, ...] = (),
    parents: tuple[Parent, ...] = (),
) -> UserProfile:
    return UserProfile(
        "c01-synthetic",
        "1",
        TaxYear(2026),
        IncomeProfile(Money.of(990500)),
        ExistingTaxBenefits(
            social_security_paid=Money.of(10500),
            parents=parents,
            retirement_contributions=retirement,
        ),
        OpportunityFacts(shared_limit_usage=usage),
    )


@pytest.mark.parametrize(
    ("user", "status", "codes", "missing"),
    [
        (_profile(usage=None), "REQUIRES_INPUT", ["SHARED_USAGE_REQUIRED"], ["opportunity_facts.shared_limit_usage"]),
        (_profile(usage=(SharedLimitUsage(THAI_ESG_2026_POOL, Money.of(1)),)), "UNSUPPORTED", ["PRIOR_SHARED_USAGE_BASELINE_UNSUPPORTED"], []),
        (_profile(retirement=(RetirementContribution("RMF", Money.of(100000)),)), "UNSUPPORTED", ["RETIREMENT_BASELINE_UNSUPPORTED"], []),
        (_profile(retirement=(RetirementContribution("PVD", Money.of(1)),)), "UNSUPPORTED", ["RETIREMENT_BASELINE_UNSUPPORTED"], []),
        (_profile(parents=(Parent("father", None),)), "REQUIRES_INPUT", ["PARENT_ELIGIBILITY_REQUIRED"], ["parent.father.eligible"]),
    ],
)
def test_incomplete_baseline_cannot_publish_tax_or_impact(
    user: UserProfile, status: str, codes: list[str], missing: list[str]
) -> None:
    state = calculate_tax(user, production_pack())
    assert state.status.value == status
    assert state.pit is state.taxable_income is state.marginal_rate is None
    assert state.to_dict()["reason_codes"] == codes
    assert state.to_dict()["missing_fact_ids"] == missing
    with pytest.raises(ValueError, match="unavailable"):
        state.tax_impact(Money.of(100000))
    # A supplied numeric base must not bypass non-READY status.
    forged = replace(state, taxable_income=Money.of(820000))
    with pytest.raises(ValueError, match="unavailable"):
        forged.tax_impact(Money.of(100000))


@pytest.mark.parametrize(
    "user",
    [
        _profile(),
        _profile(usage=(SharedLimitUsage(THAI_ESG_2026_POOL, Money.zero()),)),
        _profile(retirement=(RetirementContribution("RMF", Money.zero()),)),
        _profile(parents=(Parent("father", False),)),
    ],
)
def test_known_zero_preserves_independent_salary_golden(user: UserProfile) -> None:
    state = calculate_tax(user, production_pack())
    assert state.status.value == "READY"
    assert state.taxable_income == Money.of(820000)
    assert state.pit == Money.of(79000)
    assert state.tax_impact(Money.of(100000)).saving == Money.of(18500)
    assert state.to_dict()["reason_codes"] == []
    assert state.to_dict()["missing_fact_ids"] == []
    assert state.to_dict()["calculation_scope"] == "EMPLOYEE_40_1_SUPPORTED_RIGHTS_2026"


def test_confirmed_parent_has_hand_checked_tax() -> None:
    state = calculate_tax(_profile(parents=(Parent("father", True),)), production_pack())
    assert state.taxable_income == Money.of(790000)
    assert state.pit == Money.of(73000)


def test_combined_material_findings_have_stable_precedence_and_all_reasons() -> None:
    user = _profile(
        usage=None,
        retirement=(RetirementContribution("RMF", Money.of(1)),),
        parents=(Parent("father", None),),
    )
    user = replace(
        user,
        income=IncomeProfile(Money.of(990500), (UnsupportedIncome("40(8)", Money.of(1)),)),
    )
    first = calculate_tax(user, production_pack())
    assert first.status.value == "ADVANCED_TAX_PATH_REQUIRED"
    assert first.to_dict()["reason_codes"] == [
        "UNSUPPORTED_INCOME",
        "RETIREMENT_BASELINE_UNSUPPORTED",
        "PARENT_ELIGIBILITY_REQUIRED",
        "SHARED_USAGE_REQUIRED",
    ]
    assert first.output_hash == calculate_tax(user, production_pack()).output_hash
    assert first.pit is None


@pytest.mark.parametrize("amount", ["0", "1"])
def test_unrecognized_pool_cannot_bypass_baseline_boundary(amount: str) -> None:
    with pytest.raises(ValueError, match="unknown shared"):
        calculate_tax(
            _profile(usage=(SharedLimitUsage("invented-pool", Money.of(amount)),)),
            production_pack(),
        )


def test_discovery_keeps_baseline_evidence_without_opportunities() -> None:
    user = _profile(usage=None, parents=(Parent("father", None),))
    state = calculate_tax(user, production_pack())
    result = discover_opportunities(
        user,
        state,
        production_pack(),
        production_catalog(),
        DiscoveryContext(TaxYear(2026), date(2026, 10, 15)),
    )
    assert result.opportunities == ()
    assert result.to_dict()["baseline_status"] == "REQUIRES_INPUT"
    assert result.to_dict()["baseline_reason_codes"] == [
        "PARENT_ELIGIBILITY_REQUIRED", "SHARED_USAGE_REQUIRED"
    ]
    assert result.to_dict()["missing_fact_ids"] == [
        "parent.father.eligible", "opportunity_facts.shared_limit_usage"
    ]
