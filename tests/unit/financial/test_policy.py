"""Unit tests for the versioned Financial Guardrail Policy (TGPS-P1-003 §23-26).

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
    POLICY_CLASSIFICATION,
    ActivatedFinancialPolicy,
    FinancialGuardrailPolicy,
    FinancialPolicyActivationError,
    FinancialPolicyStatus,
    activate_financial_policy,
    bundled_financial_policy,
    evaluate_financial_policy_readiness,
)


def _valid_policy() -> FinancialGuardrailPolicy:
    return bundled_financial_policy(TaxYear(2026))


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
    assert all(
        "not Thai statute" in s or "not a Bank of Thailand" in s for s in policy.basis_sources
    )
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
