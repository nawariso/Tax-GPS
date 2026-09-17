"""Per-opportunity policy verification gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

from tax_gps.opportunity.models import (
    OpportunityCatalog,
    OpportunityDefinition,
    OpportunityRule,
    OpportunityType,
)
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import RuleSource, RuleStatus, SourceAuthority, TaxRule
from tax_gps.policy.readiness import ReadinessCode, ReadinessFinding


@dataclass(frozen=True, slots=True)
class OpportunityReadiness:
    findings: tuple[ReadinessFinding, ...]

    @property
    def ready(self) -> bool:
        return not self.findings


def _authoritative(source: RuleSource) -> bool:
    parsed = urlsplit(source.url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if source.authority is SourceAuthority.OFFICIAL_PROVIDER:
        return parsed.hostname == "sec.or.th" or parsed.hostname.endswith(".sec.or.th")
    return parsed.hostname == "go.th" or parsed.hostname.endswith(".go.th")


def _finding(code: ReadinessCode, subject: str, message: str) -> ReadinessFinding:
    return ReadinessFinding(code, subject, message)


def _resolve_source(
    source_id: str, catalog: OpportunityCatalog, pack: ActivatedRulePack
) -> RuleSource | None:
    catalog_source = catalog.find_source(source_id)
    pack_source = pack.pack.find_source(source_id)
    if catalog_source is not None and pack_source is not None and catalog_source != pack_source:
        return None
    return catalog_source or pack_source


def _resolve_rule(
    rule_id: str,
    definition: OpportunityDefinition,
    catalog: OpportunityCatalog,
    pack: ActivatedRulePack,
) -> OpportunityRule | TaxRule | None:
    if definition.opportunity_type is OpportunityType.EXISTING_RIGHT:
        return pack.pack.find_rule(rule_id)
    return catalog.find_rule(rule_id)


def _check_rule(
    rule: OpportunityRule | TaxRule,
    *,
    definition: OpportunityDefinition,
    catalog: OpportunityCatalog,
    pack: ActivatedRulePack,
    findings: list[ReadinessFinding],
    planning_date: date | None,
) -> None:
    if rule.status is not RuleStatus.EFFECTIVE:
        findings.append(
            _finding(ReadinessCode.RULE_NOT_EFFECTIVE, rule.rule_id, "rule is not EFFECTIVE")
        )
    if rule.verified_at is None:
        findings.append(
            _finding(ReadinessCode.RULE_NOT_VERIFIED, rule.rule_id, "rule is not verified")
        )
    if rule.tax_year != pack.pack.tax_year:
        findings.append(
            _finding(
                ReadinessCode.RULE_TAX_YEAR_MISMATCH,
                rule.rule_id,
                "rule tax year differs from pack",
            )
        )
    definition_covers_date = planning_date is None or (
        definition.effective_from <= planning_date
        and (definition.effective_to is None or planning_date <= definition.effective_to)
    )
    rule_covers_date = planning_date is None or (
        rule.effective_from <= planning_date
        and (rule.effective_to is None or planning_date <= rule.effective_to)
    )
    if isinstance(rule, OpportunityRule) and definition_covers_date != rule_covers_date:
        findings.append(
            _finding(
                ReadinessCode.RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR,
                rule.rule_id,
                "rule period does not cover planning date",
            )
        )
    if rule.source_id is None or not rule.source_id.strip():
        findings.append(
            _finding(ReadinessCode.RULE_SOURCE_MISSING, rule.rule_id, "rule source is missing")
        )
    else:
        source = _resolve_source(rule.source_id, catalog, pack)
        if source is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    rule.rule_id,
                    "rule source does not resolve",
                )
            )
        elif not _authoritative(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    rule.rule_id,
                    "rule source is not authoritative HTTPS",
                )
            )
    for source_id in rule.supplementary_source_ids:
        source = _resolve_source(source_id, catalog, pack)
        if source is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    rule.rule_id,
                    "supplementary source does not resolve",
                )
            )
        elif not _authoritative(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    rule.rule_id,
                    "supplementary source is not authoritative HTTPS",
                )
            )


def evaluate_opportunity_readiness(
    definition: OpportunityDefinition,
    catalog: OpportunityCatalog,
    pack: ActivatedRulePack,
    *,
    planning_date: date | None = None,
) -> OpportunityReadiness:
    findings: list[ReadinessFinding] = []
    if not definition.rule_ids:
        findings.append(
            _finding(
                ReadinessCode.REQUIRED_RULE_MISSING,
                definition.opportunity_id,
                "opportunity has no required rule",
            )
        )
    for rule_id in definition.rule_ids:
        rule = _resolve_rule(rule_id, definition, catalog, pack)
        if rule is None:
            findings.append(
                _finding(ReadinessCode.REQUIRED_RULE_MISSING, rule_id, "required rule is missing")
            )
        else:
            _check_rule(
                rule,
                definition=definition,
                catalog=catalog,
                pack=pack,
                findings=findings,
                planning_date=planning_date,
            )
    for source_id in definition.source_ids:
        source = _resolve_source(source_id, catalog, pack)
        if source is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    definition.opportunity_id,
                    "declared source does not resolve",
                )
            )
        elif not _authoritative(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    definition.opportunity_id,
                    "declared source is not authoritative HTTPS",
                )
            )
    return OpportunityReadiness(tuple(findings))
