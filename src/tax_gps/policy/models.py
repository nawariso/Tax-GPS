"""Immutable structural models for policy governance and provenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from tax_gps.core.canonical import JsonValue
from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage
from tax_gps.core.tax_year import TaxYear


class RuleStatus(StrEnum):
    DRAFT = "DRAFT"
    VERIFIED = "VERIFIED"
    EFFECTIVE = "EFFECTIVE"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"


class SourceAuthority(StrEnum):
    THAI_LAW_ROYAL_GAZETTE = "THAI_LAW_ROYAL_GAZETTE"
    REVENUE_DEPARTMENT = "REVENUE_DEPARTMENT"
    GOVERNMENT_AUTHORITY = "GOVERNMENT_AUTHORITY"
    OFFICIAL_PROVIDER = "OFFICIAL_PROVIDER"


@dataclass(frozen=True, slots=True)
class RuleSource:
    source_id: str
    title: str
    publisher: str
    authority: SourceAuthority
    url: str
    published_at: date | None
    retrieved_at: date


@dataclass(frozen=True, slots=True)
class TaxBracket:
    lower: Money
    upper: Money | None
    rate: Percentage


@dataclass(frozen=True, slots=True)
class LimitGroup:
    group_id: str
    cap: Money


@dataclass(frozen=True, slots=True)
class TaxRule:
    rule_id: str
    version: str
    tax_year: TaxYear
    effective_from: date
    effective_to: date | None
    status: RuleStatus
    source_id: str | None
    verified_at: date | None
    parameters: JsonValue
    supplementary_source_ids: tuple[str, ...]
    review_notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RulePack:
    schema_version: str
    rule_pack_id: str
    version: str
    description: str
    jurisdiction: str
    tax_year: TaxYear
    currency: str
    status: RuleStatus
    sources: tuple[RuleSource, ...]
    rules: tuple[TaxRule, ...]

    def find_rule(self, rule_id: str) -> TaxRule | None:
        return next((rule for rule in self.rules if rule.rule_id == rule_id), None)

    def rule(self, rule_id: str) -> TaxRule:
        rule = self.find_rule(rule_id)
        if rule is None:
            raise KeyError(rule_id)
        return rule

    def find_source(self, source_id: str) -> RuleSource | None:
        return next((source for source in self.sources if source.source_id == source_id), None)
