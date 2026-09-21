"""Versioned Financial Guardrail Policy (TGPS-P1-003 §23-26): PRODUCT_FINANCIAL_POLICY.

These parameters (emergency floor/target months, critical-debt APR threshold, near-term
liquidity horizon) are Tax GPS product financial-safety policy, not Thai tax/legal rules.
Provenance is documented via ``basis_sources`` / ``review_notes`` on the policy object.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.errors import TaxCoreError
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.profile import canonical_apr

BUNDLED_FINANCIAL_POLICY_ID_2026 = "TH-FIN-GUARDRAIL-2026-001"
POLICY_CLASSIFICATION = "PRODUCT_FINANCIAL_POLICY"


class FinancialPolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    UNAPPROVED = "UNAPPROVED"
    EFFECTIVE = "EFFECTIVE"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class FinancialGuardrailPolicy:
    policy_id: str
    version: str
    status: FinancialPolicyStatus
    effective_from: date
    effective_to: date | None

    emergency_floor_months: int
    emergency_target_months: int

    critical_debt_apr: Decimal

    near_term_liquidity_months: int

    basis_sources: tuple[str, ...]
    review_notes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "basis_sources", tuple(self.basis_sources))
        object.__setattr__(self, "review_notes", tuple(self.review_notes))

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "status": self.status.value,
            "classification": POLICY_CLASSIFICATION,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "emergency_floor_months": self.emergency_floor_months,
            "emergency_target_months": self.emergency_target_months,
            "critical_debt_apr": canonical_apr(self.critical_debt_apr),
            "near_term_liquidity_months": self.near_term_liquidity_months,
            "basis_sources": list(self.basis_sources),
            "review_notes": list(self.review_notes),
        }

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.to_dict()))


class FinancialPolicyValidationError(TaxCoreError, ValueError):
    """A financial guardrail policy is structurally invalid."""


def _validate_structure(policy: FinancialGuardrailPolicy) -> tuple[str, ...]:
    findings: list[str] = []
    if not policy.policy_id.strip():
        findings.append("MISSING_POLICY_ID")
    if not policy.version.strip():
        findings.append("MISSING_VERSION")
    if policy.emergency_floor_months <= 0:
        findings.append("INVALID_EMERGENCY_FLOOR_MONTHS")
    if policy.emergency_target_months < policy.emergency_floor_months:
        findings.append("INVALID_EMERGENCY_TARGET_MONTHS")
    if policy.critical_debt_apr < 0:
        findings.append("INVALID_CRITICAL_DEBT_APR")
    if policy.near_term_liquidity_months <= 0:
        findings.append("INVALID_NEAR_TERM_LIQUIDITY_MONTHS")
    if not policy.basis_sources:
        findings.append("MISSING_BASIS_SOURCES")
    return tuple(findings)


def evaluate_financial_policy_readiness(policy: FinancialGuardrailPolicy) -> tuple[str, ...]:
    """Findings that make the policy fail-closed (§26); empty tuple means ready."""
    findings = list(_validate_structure(policy))
    if policy.status is not FinancialPolicyStatus.EFFECTIVE:
        findings.append(f"POLICY_STATUS_{policy.status.value}")
    return tuple(findings)


@dataclass(frozen=True, slots=True)
class ActivatedFinancialPolicy:
    policy: FinancialGuardrailPolicy
    content_hash: str

    @property
    def policy_id(self) -> str:
        return self.policy.policy_id

    @property
    def version(self) -> str:
        return self.policy.version


class FinancialPolicyActivationError(TaxCoreError):
    def __init__(self, findings: tuple[str, ...]) -> None:
        self.findings = findings
        super().__init__("; ".join(findings))


def activate_financial_policy(policy: FinancialGuardrailPolicy) -> ActivatedFinancialPolicy:
    findings = evaluate_financial_policy_readiness(policy)
    if findings:
        raise FinancialPolicyActivationError(findings)
    return ActivatedFinancialPolicy(policy, policy.content_hash())


def bundled_financial_policy(tax_year: TaxYear) -> FinancialGuardrailPolicy:
    """Initial TH-FIN-GUARDRAIL-2026-001 policy (§23), scoped to the given tax year."""
    return FinancialGuardrailPolicy(
        policy_id=BUNDLED_FINANCIAL_POLICY_ID_2026,
        version="1.0.0",
        status=FinancialPolicyStatus.EFFECTIVE,
        effective_from=date(tax_year.gregorian, 1, 1),
        effective_to=date(tax_year.gregorian, 12, 31),
        emergency_floor_months=3,
        emergency_target_months=6,
        critical_debt_apr=Decimal("0.15"),
        near_term_liquidity_months=12,
        basis_sources=(
            "Emergency savings guidance: approximately 3-6 months of expenses "
            "(general personal-finance planning practice, not Thai statute).",
            "Thai credit-card interest/fees can reach approximately 16% p.a.; Tax GPS sets "
            "critical_debt_apr = 15% as an internal conservative product-safety threshold, "
            "not a Bank of Thailand regulatory threshold.",
        ),
        review_notes=(
            f"{POLICY_CLASSIFICATION}: this policy encodes Tax GPS product financial-safety "
            "decisions, not Thai tax law or a statutory/regulatory requirement.",
        ),
    )
