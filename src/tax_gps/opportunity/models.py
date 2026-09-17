"""Immutable opportunity-catalog domain models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from tax_gps.core.canonical import JsonValue, canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.policy.models import RuleSource, RuleStatus


class OpportunityType(StrEnum):
    EXISTING_RIGHT = "EXISTING_RIGHT"
    NEW_CASH = "NEW_CASH"


class OpportunityCategory(StrEnum):
    CLAIM_EXISTING_RIGHT = "CLAIM_EXISTING_RIGHT"
    INVESTMENT_TAX = "INVESTMENT_TAX"
    LIFESTYLE_INTENT = "LIFESTYLE_INTENT"
    UTILITY_INVESTMENT = "UTILITY_INVESTMENT"


class OpportunityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    INELIGIBLE = "INELIGIBLE"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    RULE_NOT_READY = "RULE_NOT_READY"
    OUTSIDE_EFFECTIVE_PERIOD = "OUTSIDE_EFFECTIVE_PERIOD"


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    evidence_id: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return {"evidence_id": self.evidence_id, "description": self.description}


@dataclass(frozen=True, slots=True)
class LockupMetadata:
    minimum_holding_years: int
    measurement: str

    def to_dict(self) -> dict[str, object]:
        return {
            "minimum_holding_years": self.minimum_holding_years,
            "measurement": self.measurement,
        }


@dataclass(frozen=True, slots=True)
class OpportunityRule:
    rule_id: str
    version: str
    tax_year: TaxYear
    effective_from: date
    effective_to: date | None
    status: RuleStatus
    source_id: str | None
    verified_at: date | None
    parameters: Mapping[str, JsonValue]
    supplementary_source_ids: tuple[str, ...]
    review_notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpportunityDefinition:
    opportunity_id: str
    name: str
    category: OpportunityCategory
    opportunity_type: OpportunityType
    requires_new_cash: bool
    intrinsic_need_required: bool
    advisor_required: bool
    effective_from: date
    effective_to: date | None
    rule_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    standalone_limit: Money | None
    shared_limit_group: str | None
    lockup_metadata: LockupMetadata | None
    evidence_requirements: tuple[EvidenceRequirement, ...]
    catalog_version: str

    def to_dict(self) -> dict[str, object]:
        return {
            "opportunity_id": self.opportunity_id,
            "name": self.name,
            "category": self.category.value,
            "type": self.opportunity_type.value,
            "requires_new_cash": self.requires_new_cash,
            "intrinsic_need_required": self.intrinsic_need_required,
            "advisor_required": self.advisor_required,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "rule_ids": list(self.rule_ids),
            "source_ids": list(self.source_ids),
            "standalone_limit": self.standalone_limit.canonical()
            if self.standalone_limit
            else None,
            "shared_limit_group": self.shared_limit_group,
            "lockup_metadata": self.lockup_metadata.to_dict() if self.lockup_metadata else None,
            "evidence_requirements": [item.to_dict() for item in self.evidence_requirements],
            "catalog_version": self.catalog_version,
        }

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.to_dict()))


@dataclass(frozen=True, slots=True)
class OpportunityCatalog:
    schema_version: str
    catalog_id: str
    version: str
    description: str
    jurisdiction: str
    tax_year: TaxYear
    currency: str
    status: RuleStatus
    sources: tuple[RuleSource, ...]
    rules: tuple[OpportunityRule, ...]
    definitions: tuple[OpportunityDefinition, ...]

    def find_definition(self, opportunity_id: str) -> OpportunityDefinition | None:
        return next(
            (item for item in self.definitions if item.opportunity_id == opportunity_id), None
        )

    def definition(self, opportunity_id: str) -> OpportunityDefinition:
        result = self.find_definition(opportunity_id)
        if result is None:
            raise KeyError(opportunity_id)
        return result

    def find_rule(self, rule_id: str) -> OpportunityRule | None:
        return next((item for item in self.rules if item.rule_id == rule_id), None)

    def rule(self, rule_id: str) -> OpportunityRule:
        result = self.find_rule(rule_id)
        if result is None:
            raise KeyError(rule_id)
        return result

    def find_source(self, source_id: str) -> RuleSource | None:
        return next((item for item in self.sources if item.source_id == source_id), None)
