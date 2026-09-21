"""Immutable Guardrail Result models (TGPS-P1-003 §28, §45-48).

No opaque scoring: only ``max_feasible_allocation`` (a safety ceiling, not advice) and
explicit machine-readable reason codes are exposed. See §44/§47 for forbidden semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from tax_gps.core.money import Money
from tax_gps.financial.reason_codes import FinancialReasonCode


class GuardrailDecision(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    CAP = "CAP"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    # PENALIZE is reserved for a future optimizer (§28) and is intentionally not implemented.


class GuardrailResultStatus(StrEnum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    POLICY_NOT_READY = "POLICY_NOT_READY"
    UNSUPPORTED = "UNSUPPORTED"


def _money(value: Money | None) -> str | None:
    return value.canonical() if value is not None else None


@dataclass(frozen=True, slots=True)
class GuardrailAssessment:
    opportunity_id: str
    decision: GuardrailDecision
    max_feasible_allocation: Money | None
    reason_codes: tuple[FinancialReasonCode, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "opportunity_id": self.opportunity_id,
            "decision": self.decision.value,
            "max_feasible_allocation": _money(self.max_feasible_allocation),
            "reason_codes": [reason.value for reason in self.reason_codes],
        }


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    status: GuardrailResultStatus

    profile_hash: str
    discovery_hash: str
    financial_state_hash: str
    financial_policy_hash: str

    planning_date: date
    available_budget: Money

    assessments: tuple[GuardrailAssessment, ...]

    policy_version: str
    engine_version: str
    guardrail_hash: str

    def material_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "profile_hash": self.profile_hash,
            "discovery_hash": self.discovery_hash,
            "financial_state_hash": self.financial_state_hash,
            "financial_policy_hash": self.financial_policy_hash,
            "planning_date": self.planning_date.isoformat(),
            "available_budget": self.available_budget.canonical(),
            "assessments": [item.to_dict() for item in self.assessments],
            "policy_version": self.policy_version,
            "engine_version": self.engine_version,
        }

    def to_dict(self) -> dict[str, object]:
        result = self.material_dict()
        result["guardrail_hash"] = self.guardrail_hash
        return result
