"""Unit tests for the versioned Financial Guardrail Policy (TGPS-P1-003 §23-26, R1-03).

Every readiness finding and activation-rejection path is exercised with the specific
finding code asserted, not merely executed.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.policy import (
    BUNDLED_FINANCIAL_POLICY_ID_2026,
    BUNDLED_FINANCIAL_POLICY_TAX_YEAR,
    POLICY_CLASSIFICATION,
    ActivatedFinancialPolicy,
    FinancialGuardrailPolicy,
    FinancialPolicyActivationError,
    FinancialPolicySource,
    FinancialPolicySourceAuthority,
    FinancialPolicyStatus,
    FinancialPolicyValidationError,
    activate_financial_policy,
    bundled_financial_policy,
    evaluate_financial_policy_readiness,
    evaluate_financial_policy_temporal_readiness,
)


def _valid_policy() -> FinancialGuardrailPolicy:
    return bundled_financial_policy(TaxYear(2026))


def _source(**overrides: object) -> FinancialPolicySource:
    defaults: dict[str, object] = {
        "source_id": "TEST-SOURCE",
        "publisher": "Test Publisher",
        "title": "Test Title",
        "url": "https://example.go.th/test",
        "authority": FinancialPolicySourceAuthority.MARKET_EDUCATION_BODY,
    }
    defaults.update(overrides)
    return FinancialPolicySource(**defaults)  # type: ignore[arg-type]


def test_bundled_policy_is_ready_and_classified_as_product_policy() -> None:
    policy = _valid_policy()
    assert evaluate_financial_policy_readiness(policy) == ()
    as_dict = policy.to_dict()
    assert as_dict["classification"] == POLICY_CLASSIFICATION
    assert policy.policy_id == BUNDLED_FINANCIAL_POLICY_ID_2026


def test_activate_bundled_policy_succeeds() -> None:
    activated = activate_financial_policy(_valid_policy())
    assert isinstance(activated, ActivatedFinancialPolicy)
    assert activated.policy_id == BUNDLED_FINANCIAL_POLICY_ID_2026
    assert activated.version == "1.0.0"
    assert activated.content_hash == _valid_policy().content_hash()


def test_missing_policy_id_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), policy_id="   ")
    assert "MISSING_POLICY_ID" in evaluate_financial_policy_readiness(policy)


def test_missing_version_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), version="")
    assert "MISSING_VERSION" in evaluate_financial_policy_readiness(policy)


def test_non_positive_emergency_floor_months_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), emergency_floor_months=0)
    assert "INVALID_EMERGENCY_FLOOR_MONTHS" in evaluate_financial_policy_readiness(policy)


def test_negative_emergency_floor_months_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), emergency_floor_months=-1)
    assert "INVALID_EMERGENCY_FLOOR_MONTHS" in evaluate_financial_policy_readiness(policy)


def test_target_below_floor_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), emergency_floor_months=6, emergency_target_months=3)
    assert "INVALID_EMERGENCY_TARGET_MONTHS" in evaluate_financial_policy_readiness(policy)


def test_target_equal_to_floor_is_valid() -> None:
    policy = replace(_valid_policy(), emergency_floor_months=3, emergency_target_months=3)
    assert "INVALID_EMERGENCY_TARGET_MONTHS" not in evaluate_financial_policy_readiness(policy)


def test_negative_critical_debt_apr_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), critical_debt_apr=Decimal("-0.01"))
    assert "INVALID_CRITICAL_DEBT_APR" in evaluate_financial_policy_readiness(policy)


def test_zero_critical_debt_apr_is_valid() -> None:
    policy = replace(_valid_policy(), critical_debt_apr=Decimal("0"))
    assert "INVALID_CRITICAL_DEBT_APR" not in evaluate_financial_policy_readiness(policy)


def test_non_positive_near_term_liquidity_months_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), near_term_liquidity_months=0)
    assert "INVALID_NEAR_TERM_LIQUIDITY_MONTHS" in evaluate_financial_policy_readiness(policy)


def test_missing_basis_sources_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), basis_sources=())
    assert "MISSING_BASIS_SOURCES" in evaluate_financial_policy_readiness(policy)


@pytest.mark.negative
def test_effective_from_after_effective_to_is_a_readiness_finding() -> None:
    policy = replace(
        _valid_policy(), effective_from=date(2026, 12, 31), effective_to=date(2026, 1, 1)
    )
    assert "INVALID_EFFECTIVE_PERIOD" in evaluate_financial_policy_readiness(policy)


@pytest.mark.negative
def test_non_https_basis_source_url_is_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), basis_sources=(_source(url="http://example.go.th/x"),))
    findings = evaluate_financial_policy_readiness(policy)
    assert any(f.startswith("INVALID_BASIS_SOURCE_METADATA") for f in findings)


@pytest.mark.negative
def test_blank_basis_source_fields_are_a_readiness_finding() -> None:
    policy = replace(_valid_policy(), basis_sources=(_source(publisher="  "),))
    findings = evaluate_financial_policy_readiness(policy)
    assert any(f.startswith("INVALID_BASIS_SOURCE_METADATA") for f in findings)


def test_valid_structured_basis_source_is_accepted() -> None:
    policy = replace(_valid_policy(), basis_sources=(_source(),))
    findings = evaluate_financial_policy_readiness(policy)
    assert not any(f.startswith("INVALID_BASIS_SOURCE_METADATA") for f in findings)


@pytest.mark.parametrize(
    "status",
    [
        FinancialPolicyStatus.DRAFT,
        FinancialPolicyStatus.UNAPPROVED,
        FinancialPolicyStatus.EXPIRED,
        FinancialPolicyStatus.INVALID,
    ],
)
def test_non_effective_status_is_a_readiness_finding(status: FinancialPolicyStatus) -> None:
    policy = replace(_valid_policy(), status=status)
    findings = evaluate_financial_policy_readiness(policy)
    assert f"POLICY_STATUS_{status.value}" in findings


def test_multiple_structural_findings_are_all_reported() -> None:
    policy = replace(
        _valid_policy(),
        policy_id="",
        version="",
        emergency_floor_months=0,
        near_term_liquidity_months=0,
        basis_sources=(),
    )
    findings = evaluate_financial_policy_readiness(policy)
    assert "MISSING_POLICY_ID" in findings
    assert "MISSING_VERSION" in findings
    assert "INVALID_EMERGENCY_FLOOR_MONTHS" in findings
    assert "INVALID_NEAR_TERM_LIQUIDITY_MONTHS" in findings
    assert "MISSING_BASIS_SOURCES" in findings


def test_activation_rejects_a_not_ready_policy_and_carries_findings() -> None:
    policy = replace(_valid_policy(), status=FinancialPolicyStatus.DRAFT)
    with pytest.raises(FinancialPolicyActivationError) as excinfo:
        activate_financial_policy(policy)
    assert excinfo.value.findings == ("POLICY_STATUS_DRAFT",)
    assert "POLICY_STATUS_DRAFT" in str(excinfo.value)


def test_effective_period_and_provenance_are_recorded_not_law() -> None:
    policy = _valid_policy()
    assert policy.effective_from == date(2026, 1, 1)
    assert policy.effective_to == date(2026, 12, 31)
    assert policy.basis_sources
    for source in policy.basis_sources:
        assert source.source_id
        assert source.publisher
        assert source.title
        assert source.url.startswith("https://")
    assert any("NOT a Bank of Thailand" in note for note in policy.review_notes)
    assert any(POLICY_CLASSIFICATION in note for note in policy.review_notes)


def test_content_hash_is_deterministic_and_reflects_material_fields() -> None:
    policy_a = _valid_policy()
    policy_b = _valid_policy()
    assert policy_a.content_hash() == policy_b.content_hash()
    mutated = replace(policy_a, version="1.0.1")
    assert mutated.content_hash() != policy_a.content_hash()


def test_effective_to_none_serializes_as_null() -> None:
    policy = replace(_valid_policy(), effective_to=None)
    assert policy.to_dict()["effective_to"] is None


# --- R1-03: policy effective-period vs. planning_date --------------------------------------


def test_planning_date_within_effective_period_has_no_temporal_findings() -> None:
    policy = _valid_policy()
    assert evaluate_financial_policy_temporal_readiness(policy, date(2026, 6, 1)) == ()


@pytest.mark.negative
def test_planning_date_after_effective_to_fails_closed() -> None:
    policy = replace(_valid_policy(), effective_to=date(2026, 12, 31))
    findings = evaluate_financial_policy_temporal_readiness(policy, date(2027, 1, 1))
    assert "PLANNING_DATE_AFTER_POLICY_EFFECTIVE_TO" in findings


@pytest.mark.negative
def test_planning_date_before_effective_from_fails_closed() -> None:
    policy = _valid_policy()
    findings = evaluate_financial_policy_temporal_readiness(policy, date(2025, 12, 31))
    assert "PLANNING_DATE_BEFORE_POLICY_EFFECTIVE_FROM" in findings


@pytest.mark.boundary
def test_planning_date_exactly_on_effective_to_is_within_period() -> None:
    policy = _valid_policy()
    assert evaluate_financial_policy_temporal_readiness(policy, date(2026, 12, 31)) == ()


@pytest.mark.boundary
def test_planning_date_exactly_on_effective_from_is_within_period() -> None:
    policy = _valid_policy()
    assert evaluate_financial_policy_temporal_readiness(policy, date(2026, 1, 1)) == ()


def test_temporal_readiness_with_no_effective_to_never_expires() -> None:
    policy = replace(_valid_policy(), effective_to=None)
    assert evaluate_financial_policy_temporal_readiness(policy, date(2099, 1, 1)) == ()


# --- R1-03: year-specific policy identity -----------------------------------------------


def test_bundled_policy_is_scoped_to_tax_year_2026() -> None:
    assert TaxYear(2026) == BUNDLED_FINANCIAL_POLICY_TAX_YEAR


@pytest.mark.negative
def test_bundled_policy_rejects_non_2026_tax_year() -> None:
    with pytest.raises(FinancialPolicyValidationError):
        bundled_financial_policy(TaxYear(2027))


@pytest.mark.negative
def test_bundled_policy_rejects_a_year_before_2026() -> None:
    with pytest.raises(FinancialPolicyValidationError):
        bundled_financial_policy(TaxYear(2025))
