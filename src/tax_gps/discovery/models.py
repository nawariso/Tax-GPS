"""Immutable discovery result models and stable machine-readable reasons."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from tax_gps.core.money import Money
from tax_gps.opportunity.models import (
    EvidenceRequirement,
    LockupMetadata,
    OpportunityCategory,
    OpportunityStatus,
    OpportunityType,
)
from tax_gps.policy.models import RuleSource


class DiscoveryStatus(StrEnum):
    READY = "READY"
    UNSUPPORTED = "UNSUPPORTED"


class DiscoveryReasonCode(StrEnum):
    EXISTING_RIGHT_AVAILABLE = "EXISTING_RIGHT_AVAILABLE"
    ELIGIBLE_OPPORTUNITY = "ELIGIBLE_OPPORTUNITY"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    NO_INTRINSIC_NEED = "NO_INTRINSIC_NEED"
    NO_REMAINING_CAPACITY = "NO_REMAINING_CAPACITY"
    OUTSIDE_EFFECTIVE_PERIOD = "OUTSIDE_EFFECTIVE_PERIOD"
    RULE_NOT_READY = "RULE_NOT_READY"
    UNSUPPORTED_TAX_STATE = "UNSUPPORTED_TAX_STATE"
    ZERO_CURRENT_TAX_BENEFIT = "ZERO_CURRENT_TAX_BENEFIT"
    SHARED_LIMIT_APPLIED = "SHARED_LIMIT_APPLIED"
    ELIGIBILITY_CONDITION_FAILED = "ELIGIBILITY_CONDITION_FAILED"


def _money(value: Money | None) -> str | None:
    return value.canonical() if value is not None else None


def _source_dict(source: RuleSource) -> dict[str, object]:
    return {
        "source_id": source.source_id,
        "title": source.title,
        "publisher": source.publisher,
        "authority": source.authority.value,
        "url": source.url,
        "published_at": source.published_at.isoformat() if source.published_at else None,
        "retrieved_at": source.retrieved_at.isoformat(),
    }


@dataclass(frozen=True, slots=True)
class DiscoveredRight:
    right_id: str
    name: str
    category: OpportunityCategory
    opportunity_type: OpportunityType
    status: OpportunityStatus
    requires_new_cash: bool
    claimed_amount: Money
    remaining_capacity: Money | None
    tax_impact: Money | None
    rule_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    reason_codes: tuple[DiscoveryReasonCode, ...]
    missing_fact_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "opportunity_id": self.right_id,
            "name": self.name,
            "category": self.category.value,
            "type": self.opportunity_type.value,
            "status": self.status.value,
            "requires_new_cash": self.requires_new_cash,
            "eligible_amount": self.claimed_amount.canonical(),
            "remaining_capacity": _money(self.remaining_capacity),
            "tax_impact": _money(self.tax_impact),
            "rule_ids": list(self.rule_ids),
            "source_ids": list(self.source_ids),
            "reason_codes": [reason.value for reason in self.reason_codes],
            "missing_fact_ids": list(self.missing_fact_ids),
        }


@dataclass(frozen=True, slots=True)
class DiscoveredOpportunity:
    opportunity_id: str
    name: str
    category: OpportunityCategory
    opportunity_type: OpportunityType
    status: OpportunityStatus
    requires_new_cash: bool
    intrinsic_need_required: bool
    remaining_capacity: Money | None
    maximum_tax_saving_at_capacity: Money | None
    shared_limit_group: str | None
    lockup_metadata: LockupMetadata | None
    evidence_requirements: tuple[EvidenceRequirement, ...]
    rule_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    reason_codes: tuple[DiscoveryReasonCode, ...]
    missing_fact_ids: tuple[str, ...] = ()
    failed_fact_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        lockup = self.lockup_metadata.to_dict() if self.lockup_metadata is not None else None
        return {
            "opportunity_id": self.opportunity_id,
            "name": self.name,
            "category": self.category.value,
            "type": self.opportunity_type.value,
            "status": self.status.value,
            "requires_new_cash": self.requires_new_cash,
            "intrinsic_need_required": self.intrinsic_need_required,
            "remaining_capacity": _money(self.remaining_capacity),
            "maximum_tax_saving_at_capacity": _money(self.maximum_tax_saving_at_capacity),
            "shared_limit_group": self.shared_limit_group,
            "lockup_metadata": lockup,
            "evidence_requirements": [item.to_dict() for item in self.evidence_requirements],
            "rule_ids": list(self.rule_ids),
            "source_ids": list(self.source_ids),
            "reason_codes": [reason.value for reason in self.reason_codes],
            "missing_fact_ids": list(self.missing_fact_ids),
            "failed_fact_ids": list(self.failed_fact_ids),
        }


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    status: DiscoveryStatus
    profile_hash: str
    tax_state_hash: str
    rule_pack_hash: str
    opportunity_catalog_hash: str
    tax_year: int
    planning_date: date
    existing_rights: tuple[DiscoveredRight, ...]
    opportunities: tuple[DiscoveredOpportunity, ...]
    reason_codes: tuple[DiscoveryReasonCode, ...]
    rules_applied: tuple[str, ...]
    sources: tuple[RuleSource, ...]
    catalog_version: str
    engine_version: str
    discovery_hash: str

    def material_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "profile_hash": self.profile_hash,
            "tax_state_hash": self.tax_state_hash,
            "rule_pack_hash": self.rule_pack_hash,
            "opportunity_catalog_hash": self.opportunity_catalog_hash,
            "tax_year": self.tax_year,
            "planning_date": self.planning_date.isoformat(),
            "existing_rights": [item.to_dict() for item in self.existing_rights],
            "opportunities": [item.to_dict() for item in self.opportunities],
            "reason_codes": [reason.value for reason in self.reason_codes],
            "rules_applied": list(self.rules_applied),
            "sources": [_source_dict(source) for source in self.sources],
            "catalog_version": self.catalog_version,
            "engine_version": self.engine_version,
        }

    def to_dict(self) -> dict[str, object]:
        result = self.material_dict()
        result["discovery_hash"] = self.discovery_hash
        return result
