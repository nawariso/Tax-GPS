"""Immutable policy and outcome contracts for bounded candidate construction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage


class DeductionSemantics(StrEnum):
    FULL_ALLOCATION_DEDUCTION = "FULL_ALLOCATION_DEDUCTION"
    PERCENTAGE_OF_ALLOCATION = "PERCENTAGE_OF_ALLOCATION"


@dataclass(frozen=True, slots=True)
class OpportunityTreatment:
    opportunity_id: str
    semantics: DeductionSemantics
    rate: Percentage | None = None

    def __post_init__(self) -> None:
        if (
            not self.opportunity_id
            or not isinstance(self.semantics, DeductionSemantics)
            or (
                self.semantics is DeductionSemantics.FULL_ALLOCATION_DEDUCTION
                and self.rate is not None
            )
            or (self.semantics is DeductionSemantics.PERCENTAGE_OF_ALLOCATION and self.rate is None)
        ):
            raise ValueError("invalid explicit deduction treatment")

    def to_dict(self) -> dict[str, object]:
        return {
            "opportunity_id": self.opportunity_id,
            "semantics": self.semantics.value,
            "rate": self.rate.canonical() if self.rate is not None else None,
        }


@dataclass(frozen=True, slots=True)
class SharedLimit:
    group_id: str
    remaining: Money

    def __post_init__(self) -> None:
        if not self.group_id or self.remaining.is_negative():
            raise ValueError("invalid shared allocation limit")

    def to_dict(self) -> dict[str, str]:
        return {"group_id": self.group_id, "remaining": self.remaining.canonical()}


MAX_CANDIDATES = 256


@dataclass(frozen=True, slots=True)
class AllocationPolicy:
    policy_id: str
    catalog_hash: str
    treatments: tuple[OpportunityTreatment, ...]
    shared_limits: tuple[SharedLimit, ...]
    max_candidates: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "treatments", tuple(self.treatments))
        object.__setattr__(self, "shared_limits", tuple(self.shared_limits))
        if (
            not self.policy_id
            or not self.catalog_hash
            or (
                isinstance(self.max_candidates, bool)
                or not isinstance(self.max_candidates, int)
                or self.max_candidates < 1
                or self.max_candidates > MAX_CANDIDATES
            )
        ):
            raise ValueError("invalid allocation policy maximum or identity")
        if len({t.opportunity_id for t in self.treatments}) != len(self.treatments):
            raise ValueError("duplicate opportunity treatment")
        if len({g.group_id for g in self.shared_limits}) != len(self.shared_limits):
            raise ValueError("duplicate shared allocation limit")

    def material_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "catalog_hash": self.catalog_hash,
            "treatments": [
                t.to_dict() for t in sorted(self.treatments, key=lambda t: t.opportunity_id)
            ],
            "shared_limits": [
                g.to_dict() for g in sorted(self.shared_limits, key=lambda g: g.group_id)
            ],
            "max_candidates": self.max_candidates,
        }

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.material_dict()))


@dataclass(frozen=True, slots=True)
class Allocation:
    opportunity_id: str
    amount: Money

    def to_dict(self) -> dict[str, str]:
        return {"opportunity_id": self.opportunity_id, "amount": self.amount.canonical()}


@dataclass(frozen=True, slots=True)
class CandidateOutcome:
    candidate_id: str
    allocations: tuple[Allocation, ...]
    total_allocation: Money
    deductible_amount: Money
    tax_before: Money
    tax_after: Money
    tax_saved: Money
    cash_outflow: Money
    unused_budget: Money
    spendable_surplus_after: Money | None
    protection_gap: Money | None
    reason_codes: tuple[str, ...]
    input_hash: str
    policy_hash: str
    tax_rule_pack_hash: str
    guardrail_hash: str
    engine_version: str

    def allocation_dict(self) -> dict[str, object]:
        return {"allocations": [allocation.to_dict() for allocation in self.allocations]}

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            **self.allocation_dict(),
            "total_allocation": self.total_allocation.canonical(),
            "deductible_amount": self.deductible_amount.canonical(),
            "tax_before": self.tax_before.canonical(),
            "tax_after": self.tax_after.canonical(),
            "tax_saved": self.tax_saved.canonical(),
            "cash_outflow": self.cash_outflow.canonical(),
            "unused_budget": self.unused_budget.canonical(),
            "spendable_surplus_after": (
                self.spendable_surplus_after.canonical()
                if self.spendable_surplus_after is not None
                else None
            ),
            "protection_gap": self.protection_gap.canonical()
            if self.protection_gap is not None
            else None,
            "reason_codes": list(self.reason_codes),
            "input_hash": self.input_hash,
            "policy_hash": self.policy_hash,
            "tax_rule_pack_hash": self.tax_rule_pack_hash,
            "guardrail_hash": self.guardrail_hash,
            "engine_version": self.engine_version,
        }


@dataclass(frozen=True, slots=True)
class CandidateResult:
    candidates: tuple[CandidateOutcome, ...]
    input_hash: str
    policy_hash: str
    engine_version: str
    result_hash: str

    def material_dict(self) -> dict[str, object]:
        return {
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "input_hash": self.input_hash,
            "policy_hash": self.policy_hash,
            "engine_version": self.engine_version,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.material_dict(), "result_hash": self.result_hash}
