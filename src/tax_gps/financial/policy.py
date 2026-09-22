"""Versioned Financial Guardrail Policy (TGPS-P1-003 §23-26): PRODUCT_FINANCIAL_POLICY.

These parameters (emergency floor/target months, critical-debt APR threshold, near-term
liquidity horizon) are Tax GPS product financial-safety policy, not Thai tax/legal rules.
Provenance is documented via structured ``basis_sources`` (source_id/publisher/title/url/
authority, HTTPS-validated) and free-text ``review_notes`` on the policy object. The 15%
``critical_debt_apr`` threshold is an internal Tax GPS product-safety decision informed by,
but not equal to, the Bank of Thailand's ~16% p.a. credit-card cost ceiling: it is NEVER a
Bank of Thailand regulatory threshold (§25, R1-03).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from urllib.parse import urlsplit

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.errors import TaxCoreError
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.profile import canonical_apr

BUNDLED_FINANCIAL_POLICY_ID_2026 = "TH-FIN-GUARDRAIL-2026-001"
BUNDLED_FINANCIAL_POLICY_TAX_YEAR = TaxYear(2026)
POLICY_CLASSIFICATION = "PRODUCT_FINANCIAL_POLICY"


class FinancialPolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    UNAPPROVED = "UNAPPROVED"
    EFFECTIVE = "EFFECTIVE"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


class FinancialPolicySourceAuthority(StrEnum):
    """Provenance category for a financial-policy basis source (R1-03).

    Distinct from ``tax_gps.policy.models.SourceAuthority``: these sources back a Tax GPS
    *product* financial-safety policy, never a Thai tax/legal rule, so they are never
    represented as ``THAI_LAW_ROYAL_GAZETTE`` or similar statutory authority.
    """

    CENTRAL_BANK_REGULATOR = "CENTRAL_BANK_REGULATOR"
    MARKET_EDUCATION_BODY = "MARKET_EDUCATION_BODY"


@dataclass(frozen=True, slots=True)
class FinancialPolicySource:
    """A single provenance citation for a financial guardrail policy parameter (§25, R1-03)."""

    source_id: str
    publisher: str
    title: str
    url: str
    authority: FinancialPolicySourceAuthority

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "publisher": self.publisher,
            "title": self.title,
            "url": self.url,
            "authority": self.authority.value,
        }


def _has_valid_source_metadata(source: FinancialPolicySource) -> bool:
    """Structured provenance, not arbitrary text: non-empty identity fields plus an HTTPS URL
    with a resolvable hostname (mirrors ``tax_gps.policy.readiness``'s HTTPS/authority gate).
    """
    if not source.source_id.strip() or not source.publisher.strip() or not source.title.strip():
        return False
    parsed = urlsplit(source.url)
    return parsed.scheme == "https" and bool(parsed.hostname)


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

    basis_sources: tuple[FinancialPolicySource, ...]
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
            "basis_sources": [source.to_dict() for source in self.basis_sources],
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
    if policy.effective_to is not None and policy.effective_from > policy.effective_to:
        findings.append("INVALID_EFFECTIVE_PERIOD")
    if not policy.basis_sources:
        findings.append("MISSING_BASIS_SOURCES")
    else:
        for index, source in enumerate(policy.basis_sources):
            if not _has_valid_source_metadata(source):
                identifier = source.source_id.strip() or str(index)
                findings.append(f"INVALID_BASIS_SOURCE_METADATA:{identifier}")
    return tuple(findings)


def evaluate_financial_policy_readiness(policy: FinancialGuardrailPolicy) -> tuple[str, ...]:
    """Findings that make the policy fail-closed (§26); empty tuple means ready.

    Structural/provenance readiness only (independent of any particular planning date). Use
    :func:`evaluate_financial_policy_temporal_readiness` to additionally check that a specific
    ``planning_date`` falls within the policy's effective period (R1-03).
    """
    findings = list(_validate_structure(policy))
    if policy.status is not FinancialPolicyStatus.EFFECTIVE:
        findings.append(f"POLICY_STATUS_{policy.status.value}")
    return tuple(findings)


def evaluate_financial_policy_temporal_readiness(
    policy: FinancialGuardrailPolicy, planning_date: date
) -> tuple[str, ...]:
    """Fail closed if ``planning_date`` falls outside the policy's effective period (R1-03).

    A policy with ``status = EFFECTIVE`` alone is not sufficient: an EFFECTIVE policy whose
    ``effective_to`` has already passed relative to the planning date must not be silently
    applied.
    """
    findings: list[str] = []
    if planning_date < policy.effective_from:
        findings.append("PLANNING_DATE_BEFORE_POLICY_EFFECTIVE_FROM")
    if policy.effective_to is not None and planning_date > policy.effective_to:
        findings.append("PLANNING_DATE_AFTER_POLICY_EFFECTIVE_TO")
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
    """Initial TH-FIN-GUARDRAIL-2026-001 policy (§23).

    The bundled policy identity is fixed to tax year 2026 (see ``BUNDLED_FINANCIAL_POLICY_ID``);
    this phase does not yet define a year-specific identity strategy for other tax years, so
    any other tax year is rejected rather than silently producing a mismatched policy identity
    (R1-03).
    """
    if tax_year != BUNDLED_FINANCIAL_POLICY_TAX_YEAR:
        raise FinancialPolicyValidationError(
            f"no bundled financial guardrail policy exists for tax year {tax_year}; "
            f"{BUNDLED_FINANCIAL_POLICY_ID_2026} is scoped to tax year "
            f"{BUNDLED_FINANCIAL_POLICY_TAX_YEAR} only"
        )
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
            FinancialPolicySource(
                source_id="SET-EMERGENCY-FUND-GUIDANCE",
                publisher="The Stock Exchange of Thailand (SET Investnow)",
                title=(
                    "เงินออมฉุกเฉิน ปราการด่านแรกในการป้องกันปัญหาทางการเงิน "
                    "(Emergency savings: the first line of defense against financial "
                    "problems) - approximately 3-6 months of expenses"
                ),
                url=(
                    "https://www.setinvestnow.com/th/knowledge/article/"
                    "1-precuation-saving-to-avoid-financial-problem"
                ),
                authority=FinancialPolicySourceAuthority.MARKET_EDUCATION_BODY,
            ),
            FinancialPolicySource(
                source_id="BOT-CREDIT-CARD-INTEREST-CEILING",
                publisher="Bank of Thailand",
                title=(
                    "Notification of the Bank of Thailand: Regulations, Procedures and "
                    "Conditions for Undertaking Credit Card Business - interest/fee ceiling "
                    "of 16 percent per annum (effective rate)"
                ),
                url=(
                    "https://www.bot.or.th/content/dam/bot/fipcs/documents/FPG/2563/"
                    "EngPDF/25630183.pdf"
                ),
                authority=FinancialPolicySourceAuthority.CENTRAL_BANK_REGULATOR,
            ),
        ),
        review_notes=(
            f"{POLICY_CLASSIFICATION}: this policy encodes Tax GPS product financial-safety "
            "decisions, not Thai tax law or a statutory/regulatory requirement.",
            "critical_debt_apr = 15% is an internal Tax GPS conservative product-safety "
            "threshold informed by, but distinct from, the Bank of Thailand's ~16% p.a. "
            "credit-card cost ceiling; it is NOT a Bank of Thailand regulatory threshold.",
        ),
    )
